using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;

namespace ReverieSaga
{
    // One private process owns all authoritative state;the renderer only submits intents.
    public sealed class BrainConnection : IDisposable
    {
        const int MaxFrame = 1024 * 1024;
        readonly Process child;
        readonly ConcurrentQueue<WireResponse> updates = new ConcurrentQueue<WireResponse>();
        readonly ConcurrentQueue<string> errors = new ConcurrentQueue<string>();
        readonly ConcurrentQueue<string> diagnostics = new ConcurrentQueue<string>();
        readonly Task reader;
        readonly Task stderrReader;
        long nextId = 1;
        string attachment = "";
        volatile bool disposed;
        readonly object shutdownLock = new object();
        Task shutdown;
        bool awaiting = true;
        long awaitingId;
        readonly Stopwatch deadline = Stopwatch.StartNew();
        public int ProcessId { get { return child.Id; } }
        public bool Busy { get { return awaiting; } }

        public BrainConnection(string root, string workingFile, string scenario = "legacy",
            string questCatalog = "", string questSha256 = "", bool npcMemory = false)
        {
            string python = Path.Combine(root, ".venv", "Scripts", "python.exe");
            string catalog = Path.Combine(root, "content", "narratives.json");
            if (!File.Exists(python) || !File.Exists(catalog))
                throw new IOException("Python runtime or accepted catalog is missing");
            string questArgs="";
            if(npcMemory&&(String.IsNullOrEmpty(questCatalog)||String.IsNullOrEmpty(questSha256)))
                throw new IOException("NPC_MEMORY_CONTENT");
            if(!String.IsNullOrEmpty(questCatalog)||!String.IsNullOrEmpty(questSha256)) {
                if(String.IsNullOrEmpty(questCatalog)||String.IsNullOrEmpty(questSha256))
                    throw new IOException("QUEST_CONTENT_UNAVAILABLE");
                questArgs=" --quest-catalog "+Quote(questCatalog)+" --quest-sha256 "+Quote(questSha256);
            }
            var start = new ProcessStartInfo {
                FileName = python, WorkingDirectory = root,
                Arguments = "-m app.engine_bridge --working " + Quote(workingFile) +
                    " --catalog " + Quote(catalog) + " --catalog-sha256 " + CatalogPin.Hash +
                    " --scenario " + Quote(scenario) + questArgs + (npcMemory?" --npc-memory":""),
                UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardInput = true, RedirectStandardOutput = true,
                RedirectStandardError = true
            };
            start.EnvironmentVariables["PYTHONPATH"] = Path.Combine(root, "src");
            start.EnvironmentVariables["PYTHONUTF8"] = "1";
            child = Process.Start(start) ?? throw new IOException("Brain did not start");
            stderrReader = Task.Run(() => {
                string line;
                while ((line = child.StandardError.ReadLine()) != null) diagnostics.Enqueue(line);
            });
            reader = Task.Run(ReadLoop);
        }

        static string Quote(string value)
        {
            if (value.Contains("\"") || value.Contains("\n") || value.Contains("\r"))
                throw new ArgumentException("Invalid process argument");
            return "\"" + value + "\"";
        }

        static byte[] Exact(Stream source, int length)
        {
            var bytes = new byte[length];
            int offset = 0;
            while (offset < length) {
                int read = source.Read(bytes, offset, length - offset);
                if (read == 0) throw new EndOfStreamException("Truncated Brain frame");
                offset += read;
            }
            return bytes;
        }

        void ReadLoop()
        {
            try {
                Stream source = child.StandardOutput.BaseStream;
                while (!disposed) {
                    int first = source.ReadByte();
                    if (first < 0) break;
                    byte[] tail = Exact(source, 3);
                    uint count = ((uint)first << 24) | ((uint)tail[0] << 16) |
                                 ((uint)tail[1] << 8) | tail[2];
                    if (count < 1 || count > MaxFrame) throw new IOException("Frame length");
                    string json = new UTF8Encoding(false, true).GetString(Exact(source, (int)count));
                    WireResponse update = JsonUtility.FromJson<WireResponse>(json);
                    if (update == null || update.kind != "update" || update.version != "1" ||
                        update.schema_hash != WireSchema.Hash || update.update == null ||
                        update.narratives == null) throw new IOException("Wire schema mismatch");
                    updates.Enqueue(update);
                }
                if (!disposed) errors.Enqueue("Brain disconnected");
            } catch (Exception e) { if (!disposed) errors.Enqueue("Brain pipe: " + e.Message); }
        }

        public bool Poll(out WireResponse value, out string error)
        {
            error = null; value = null;
            while(diagnostics.TryDequeue(out string diagnostic)) UnityEngine.Debug.LogWarning(diagnostic);
            if (errors.TryDequeue(out error)) return false;
            if (awaiting && deadline.Elapsed.TotalSeconds > 10) {
                error = "Brain response timeout"; StopAsync(); return false;
            }
            if (!updates.TryDequeue(out value)) return false;
            if (!long.TryParse(value.request_id, NumberStyles.None, CultureInfo.InvariantCulture,
                              out long id) || !(id == awaitingId || (id == 0 && !String.IsNullOrEmpty(value.error)))) {
                error = "Unexpected response identity"; StopAsync(); value = null; return false;
            }
            attachment = value.update.attachment_id;
            awaiting = false;
            return true;
        }

        public void Send(string intent)
        {
            if (disposed || awaiting) throw new InvalidOperationException("Brain unavailable/busy");
            var request = new WireRequest {kind="request", version="1",
                request_id=nextId.ToString(CultureInfo.InvariantCulture), attachment_id=attachment,
                request=intent, seconds="1", slot_id="slot01"};
            byte[] body = Encoding.UTF8.GetBytes(JsonUtility.ToJson(request));
            if (body.Length > 16 * 1024) throw new IOException("Request capacity");
            int size = body.Length;
            byte[] frame = {(byte)(size >> 24),(byte)(size >> 16),(byte)(size >> 8),(byte)size};
            Stream target = child.StandardInput.BaseStream;
            target.Write(frame,0,4); target.Write(body,0,size); target.Flush();
            awaitingId = nextId++;
            awaiting = true; deadline.Restart();
        }

        public Task StopAsync()
        {
            lock(shutdownLock) {
                if(shutdown!=null)return shutdown;
                disposed=true;awaiting=false;
                shutdown=Task.Run(Cleanup);
                return shutdown;
            }
        }

        void Cleanup()
        {
            try {
                try { child.StandardInput.Close(); }
                catch(IOException e) { diagnostics.Enqueue("Brain input already closed: "+e.Message); }
                if(!child.WaitForExit(5000)) {
                    child.Kill();
                    if(!child.WaitForExit(5000))throw new IOException("Brain child did not exit");
                }
                if(!Task.WaitAll(new [] {reader, stderrReader},5000))
                    throw new IOException("Brain readers did not exit");
            } finally { child.Dispose(); }
        }

        public void Dispose() { StopAsync().GetAwaiter().GetResult(); }

#if UNITY_EDITOR || DEVELOPMENT_BUILD
        public void SendMalformedForVerification()
        {
            if(disposed||awaiting)throw new InvalidOperationException("Brain unavailable/busy");
            byte[] bad=Encoding.UTF8.GetBytes("{\"kind\":\"request\",\"kind\":\"request\"}");
            Stream target=child.StandardInput.BaseStream;
            target.WriteByte(0);target.WriteByte(0);target.WriteByte(0);target.WriteByte((byte)bad.Length);
            target.Write(bad,0,bad.Length);target.Flush();
            awaitingId=nextId++;awaiting=true;deadline.Restart();
        }
#endif
    }
}
