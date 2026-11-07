using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;

namespace ReverieSaga
{
    public sealed class WorldReadOnlyWindow : EditorWindow
    {
        const string Format = "reverie-world-observer/v1";
        const int OutputLimit = 128 * 1024;
        const int TimeoutMilliseconds = 15000;

        [Serializable]
        sealed class Exchange
        {
            public long tick;
            public string player;
            public string reply;
        }

        [Serializable]
        sealed class Resident
        {
            public string id;
            public string name;
            public string role;
            public Exchange[] exchanges;
        }

        [Serializable]
        sealed class Snapshot
        {
            public string format;
            public long tick;
            public long revision;
            public string location;
            public string quest_location;
            public string quest_phase;
            public string quest_status;
            public int cargo;
            public int cargo_required;
            public long resolved_tick;
            public Resident[] residents;
        }

        Task<string> pending;
        CancellationTokenSource cancellation;
        Snapshot snapshot;
        string error;
        string selectedId;
        string[] residentLabels;
        string workingPath;
        int selected;
        Vector2 scroll;
        Font koreanFont;

        [MenuItem("Reverie/현재 월드 보기 (읽기 전용)")]
        public static void Open()
        {
            OpenWorking(null);
        }

        internal static WorldReadOnlyWindow OpenWorking(string path)
        {
            var window = GetWindow<WorldReadOnlyWindow>("현재 월드");
            window.minSize = new Vector2(440, 320);
            window.workingPath = path;
            window.Refresh();
            return window;
        }

        void Refresh()
        {
            CancelPending();
            snapshot = null;
            error = null;
            scroll = Vector2.zero;
            cancellation = new CancellationTokenSource();
            string root = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
            pending = ReadAsync(root, workingPath, cancellation.Token);
            Repaint();
        }

        void OnInspectorUpdate()
        {
            if (pending == null || !pending.IsCompleted)
                return;

            try
            {
                var next = JsonUtility.FromJson<Snapshot>(pending.GetAwaiter().GetResult());
                Validate(next);
                snapshot = next;
                residentLabels = Array.ConvertAll(next.residents, r => $"{r.name} · {r.role}");
                selected = Math.Max(0, Array.FindIndex(next.residents, r => r.id == selectedId));
            }
            catch (Exception e) when (e is IOException || e is ArgumentException ||
                                      e is InvalidOperationException || e is Win32Exception ||
                                      e is TimeoutException || e is OperationCanceledException)
            {
                error = e.Message;
            }
            finally
            {
                CancelPending();
                Repaint();
            }
        }

        void OnGUI()
        {
            if (koreanFont == null)
                koreanFont = Font.CreateDynamicFontFromOSFont("Malgun Gothic", 14);
            var title = new GUIStyle(EditorStyles.boldLabel) { font = koreanFont };
            var text = new GUIStyle(EditorStyles.wordWrappedLabel) { font = koreanFont, richText = false };
            var button = new GUIStyle(GUI.skin.button) { font = koreanFont };
            EditorGUILayout.LabelField("현재 월드 · 읽기 전용", title);
            using (new EditorGUI.DisabledScope(pending != null))
                if (GUILayout.Button("새로고침", button))
                    Refresh();

            if (pending != null || snapshot == null)
            {
                EditorGUILayout.LabelField(pending != null ? "현재 진행본을 읽는 중…" :
                    error == null ? "새로고침을 눌러 진행본을 읽으세요." :
                    $"진행본을 읽지 못했습니다. 새로고침으로 다시 시도하세요.\n{error}", text);
                return;
            }

            scroll = EditorGUILayout.BeginScrollView(scroll);
            EditorGUILayout.LabelField($"{snapshot.location} · 게임 {snapshot.tick}초 · 기록 {snapshot.revision}", text);
            EditorGUILayout.Space();
            EditorGUILayout.LabelField($"보급 의뢰 · {snapshot.quest_phase}", title);
            EditorGUILayout.LabelField(snapshot.quest_location, text);
            EditorGUILayout.LabelField(snapshot.quest_status, text);
            EditorGUILayout.LabelField($"소지한 복구품 {snapshot.cargo}/{snapshot.cargo_required}", text);
            if (snapshot.resolved_tick > 0)
                EditorGUILayout.LabelField($"완료 시각 · 게임 {snapshot.resolved_tick}초", text);

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("주민과 나눈 대화 · 최근 최대 8건", title);
            if (snapshot.residents.Length == 0)
                EditorGUILayout.LabelField("현재 위치에서 볼 수 있는 주민이 없습니다.", text);
            else
            {
                selected = EditorGUILayout.Popup(selected, residentLabels,
                    new GUIStyle(EditorStyles.popup) { font = koreanFont });
                Resident resident = snapshot.residents[selected];
                selectedId = resident.id;
                if (resident.exchanges.Length == 0)
                    EditorGUILayout.LabelField("완료된 대화가 없습니다.", text);
                foreach (Exchange exchange in resident.exchanges)
                {
                    EditorGUILayout.LabelField($"게임 {exchange.tick}초 · 나: {exchange.player}", text);
                    if (!String.IsNullOrEmpty(exchange.reply))
                        EditorGUILayout.LabelField($"{resident.name}: {exchange.reply}", text);
                }
            }
            EditorGUILayout.EndScrollView();
        }

        void OnDisable()
        {
            CancelPending();
            if (koreanFont != null)
                DestroyImmediate(koreanFont);
        }

        void CancelPending()
        {
            if (cancellation == null)
                return;
            cancellation.Cancel();
            cancellation.Dispose();
            cancellation = null;
            pending = null;
        }

        static void Validate(Snapshot data)
        {
            if (data == null || data.format != Format || data.tick < 0 || data.revision < 0 ||
                String.IsNullOrEmpty(data.location) || String.IsNullOrEmpty(data.quest_phase) ||
                String.IsNullOrEmpty(data.quest_location) || String.IsNullOrEmpty(data.quest_status) ||
                data.cargo_required < 1 || data.cargo < 0 || data.resolved_tick < 0 ||
                data.resolved_tick > data.tick || data.residents == null)
                throw new IOException("WORLD_VIEW_FORMAT");
            foreach (Resident resident in data.residents)
            {
                if (resident == null || String.IsNullOrEmpty(resident.id) || String.IsNullOrEmpty(resident.name) ||
                    String.IsNullOrEmpty(resident.role) || resident.exchanges == null || resident.exchanges.Length > 8)
                    throw new IOException("WORLD_VIEW_FORMAT");
                foreach (Exchange exchange in resident.exchanges)
                    if (exchange == null || exchange.tick < 1 || exchange.tick > data.tick ||
                        String.IsNullOrEmpty(exchange.player) || exchange.reply == null)
                        throw new IOException("WORLD_VIEW_FORMAT");
            }
        }

        static async Task<string> ReadBounded(StreamReader stream, int limit)
        {
            var buffer = new char[4096];
            var text = new StringBuilder();
            int count;
            while ((count = await stream.ReadAsync(buffer, 0, buffer.Length).ConfigureAwait(false)) != 0)
            {
                if (text.Length + count > limit)
                    throw new IOException("WORLD_VIEW_OUTPUT_LIMIT");
                text.Append(buffer, 0, count);
            }
            return text.ToString();
        }

        static async Task<string> ReadAsync(string root, string path, CancellationToken token)
        {
            string python = Path.Combine(root, ".venv", "Scripts", "python.exe");
            if (!File.Exists(python))
                throw new IOException("WORLD_VIEW_PYTHON_MISSING");
            if (path != null && (path.Contains("\"") || path.Contains("\n") || path.Contains("\r")))
                throw new ArgumentException("WORLD_VIEW_PATH");
            var start = new ProcessStartInfo
            {
                FileName = python,
                WorkingDirectory = root,
                Arguments = "-B -m app.world_observer" + (path == null ? "" : " --working \"" + path + "\""),
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8,
            };
            start.EnvironmentVariables["PYTHONPATH"] = Path.Combine(root, "src");
            start.EnvironmentVariables["PYTHONUTF8"] = "1";

            using (var child = Process.Start(start) ?? throw new IOException("WORLD_VIEW_START_FAILED"))
            {
                try
                {
                    var stdout = ReadBounded(child.StandardOutput, OutputLimit);
                    var stderr = ReadBounded(child.StandardError, 2048);
                    var streams = Task.WhenAll(stdout, stderr);
                    if (await Task.WhenAny(streams, Task.Delay(TimeoutMilliseconds, token)).ConfigureAwait(false) != streams)
                    {
                        token.ThrowIfCancellationRequested();
                        throw new TimeoutException("WORLD_VIEW_TIMEOUT");
                    }
                    await streams.ConfigureAwait(false);
                    if (!child.WaitForExit(1000))
                        throw new TimeoutException("WORLD_VIEW_TIMEOUT");
                    if (child.ExitCode != 0)
                        throw new IOException(String.IsNullOrWhiteSpace(stderr.Result) ? "WORLD_VIEW_FAILED" : stderr.Result.Trim());
                    return stdout.Result;
                }
                finally
                {
                    if (!child.HasExited)
                        child.Kill();
                }
            }
        }
    }
}
