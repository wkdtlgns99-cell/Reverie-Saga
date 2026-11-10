using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

namespace ReverieSaga
{
    internal sealed class VillageConnection : IDisposable
    {
        internal const string Format = "reverie-world-village/v1";
        const int Limit = 16384;
        const int TimeoutMilliseconds = 15000;
        readonly Process child;
        readonly Task<string> diagnostics;
        int disposed;

        [Serializable]
        sealed class Request
        {
            public string format = Format;
            public long id;
            public string action;
            public string value;
        }

        internal VillageConnection(string root, string path, string seed = null, string trial = null)
        {
            if (path != null && (path.Contains("\"") || path.Contains("\n") || path.Contains("\r")))
                throw new ArgumentException("VILLAGE_PATH");
            if (seed != null && !System.Text.RegularExpressions.Regex.IsMatch(seed, VillageLayout.SeedPattern))
                throw new ArgumentException("WORLD_SEED");
            if (trial != null && ((trial != "slime" && trial != "guard") || seed == null || path != null))
                throw new ArgumentException("DUNGEON_TRIAL");
            string python = Path.Combine(root, ".venv", "Scripts", "python.exe");
            if (!File.Exists(python))
                throw new IOException("VILLAGE_PYTHON_MISSING");
            var start = new ProcessStartInfo
            {
                FileName = python,
                WorkingDirectory = root,
                Arguments = "-B -m app.world_village_bridge" +
                    (path == null ? "" : " --working \"" + path + "\"") +
                    (seed == null ? "" : " --seed " + seed) +
                    (trial == null ? "" : " --dungeon-trial " + trial),
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                StandardErrorEncoding = Encoding.UTF8,
            };
            start.EnvironmentVariables["PYTHONPATH"] = Path.Combine(root, "src");
            start.EnvironmentVariables["PYTHONUTF8"] = "1";
            child = Process.Start(start) ?? throw new IOException("VILLAGE_START_FAILED");
            diagnostics = DrainDiagnostics(child.StandardError);
        }

        static async Task<string> DrainDiagnostics(StreamReader source)
        {
            var head = new StringBuilder();
            var buffer = new char[512];
            int count;
            while ((count = await source.ReadAsync(buffer, 0, buffer.Length).ConfigureAwait(false)) != 0)
                head.Append(buffer, 0, Math.Min(count, 2048 - head.Length));
            return head.ToString().Trim();
        }

        internal async Task<string> Send(long id, string action, string value)
        {
            byte[] body = Encoding.UTF8.GetBytes(JsonUtility.ToJson(new Request {
                id = id, action = action, value = value,
            }));
            var exchange = Exchange(body);
            using (var timeout = new CancellationTokenSource())
            {
                var timer = Task.Delay(TimeoutMilliseconds, timeout.Token);
                if (await Task.WhenAny(exchange, timer).ConfigureAwait(false) != exchange)
                {
                    Observe(exchange);
                    throw new TimeoutException("VILLAGE_TIMEOUT");
                }
                timeout.Cancel();
            }
            try
            {
                return await exchange.ConfigureAwait(false);
            }
            catch (IOException)
            {
                if (await Task.WhenAny(diagnostics, Task.Delay(250)).ConfigureAwait(false) != diagnostics ||
                    diagnostics.Status != TaskStatus.RanToCompletion)
                    throw;
                string detail = await diagnostics.ConfigureAwait(false);
                if (detail.Length == 0)
                    throw;
                throw new IOException(detail);
            }
        }

        async Task<string> Exchange(byte[] body)
        {
            if (body.Length < 1 || body.Length > Limit)
                throw new IOException("VILLAGE_FRAME");
            var input = child.StandardInput.BaseStream;
            var output = child.StandardOutput.BaseStream;
            var header = new[] { (byte)0, (byte)0, (byte)(body.Length >> 8), (byte)body.Length };
            await input.WriteAsync(header, 0, header.Length).ConfigureAwait(false);
            await input.WriteAsync(body, 0, body.Length).ConfigureAwait(false);
            await input.FlushAsync().ConfigureAwait(false);
            await Read(output, header).ConfigureAwait(false);
            if (header[0] != 0 || header[1] != 0)
                throw new IOException("VILLAGE_FRAME");
            int length = (header[2] << 8) | header[3];
            if (length < 1 || length > Limit)
                throw new IOException("VILLAGE_FRAME");
            var response = new byte[length];
            await Read(output, response).ConfigureAwait(false);
            return Encoding.UTF8.GetString(response);
        }

        static async Task Read(Stream source, byte[] bytes)
        {
            for (int offset = 0; offset < bytes.Length;)
            {
                int count = await source.ReadAsync(bytes, offset, bytes.Length - offset).ConfigureAwait(false);
                if (count == 0)
                    throw new EndOfStreamException("VILLAGE_CLOSED");
                offset += count;
            }
        }

        internal static void Observe(Task task)
        {
            _ = task?.ContinueWith(failed => { _ = failed.Exception; }, TaskContinuationOptions.OnlyOnFaulted);
        }

        public void Dispose()
        {
            if (Interlocked.Exchange(ref disposed, 1) != 0)
                return;
            Observe(diagnostics);
            try { child.StandardInput.Close(); }
            catch (IOException error) { UnityEngine.Debug.LogWarning(error.Message); }
            Observe(Task.Run(() =>
            {
                using (child)
                {
                    if (!child.WaitForExit(2000) && !child.HasExited)
                        child.Kill();
                }
            }));
        }
    }
}
