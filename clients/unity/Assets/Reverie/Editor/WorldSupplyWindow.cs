using System;
using System.ComponentModel;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;

namespace ReverieSaga
{
    public sealed class WorldSupplyWindow : EditorWindow
    {
        const string Format = "reverie-world-supply/v1";
        const string Module = "app.world_supply_bridge";

        [Serializable]
        sealed class Offer
        {
            public string token;
            public string label;
            public string line;
            public string terms;
        }

        [Serializable]
        sealed class Snapshot
        {
            public string format;
            public long tick;
            public long revision;
            public string location;
            public string status;
            public string notice;
            public long cargo;
            public int cargo_required;
            public long gold;
            public string error;
            public bool has_offer;
            public Offer offer;
        }

        string workingPath;
        Snapshot snapshot;
        string error;
        Font koreanFont;
        Vector2 scroll;
        CancellationTokenSource cancellation;
        Task<string> pending;

        [MenuItem("Reverie/보급 의뢰 플레이")]
        public static void Open() => OpenWorking(null);

        internal static WorldSupplyWindow OpenWorking(string path)
        {
            var window = GetWindow<WorldSupplyWindow>("보급 의뢰");
            window.minSize = new Vector2(460, 340);
            if (window.pending != null)
                return window;
            window.workingPath = path;
            window.StartRequest(null);
            return window;
        }

        void StartRequest(string confirmation)
        {
            if (pending != null)
                return;
            if (confirmation == null)
                snapshot = null;
            error = null;
            cancellation = new CancellationTokenSource();
            string root = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
            pending = WorldReadOnlyWindow.ReadAsync(root, workingPath, cancellation.Token, Module, confirmation);
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
                error = next.error;
            }
            catch (Exception exception) when (exception is IOException || exception is ArgumentException ||
                exception is InvalidOperationException || exception is Win32Exception ||
                exception is TimeoutException || exception is OperationCanceledException)
            {
                error = exception.Message;
            }
            finally
            {
                pending = null;
                cancellation.Dispose();
                cancellation = null;
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
            EditorGUILayout.LabelField("보급 의뢰 플레이", title);
            using (new EditorGUI.DisabledScope(pending != null))
                if (GUILayout.Button("새로고침", button))
                    StartRequest(null);
            if (pending != null)
            {
                EditorGUILayout.LabelField("진행을 확인하는 중…", text);
                return;
            }
            if (!String.IsNullOrEmpty(error))
                EditorGUILayout.LabelField(ErrorText(error), text);
            if (snapshot == null)
                return;

            scroll = EditorGUILayout.BeginScrollView(scroll);
            EditorGUILayout.LabelField(
                $"{snapshot.location} · 게임 {snapshot.tick}초 · 기록 {snapshot.revision}", text);
            EditorGUILayout.LabelField(snapshot.status, text);
            EditorGUILayout.LabelField($"복구품 {snapshot.cargo}/{snapshot.cargo_required} · 소지금 {snapshot.gold}금", text);
            EditorGUILayout.LabelField(snapshot.notice, text);
            if (snapshot.has_offer)
            {
                var offer = snapshot.offer;
                EditorGUILayout.Space();
                EditorGUILayout.LabelField(offer.line, text);
                EditorGUILayout.LabelField(offer.terms, text);
                if (GUILayout.Button(offer.label, button) &&
                    EditorUtility.DisplayDialog(offer.label, offer.terms, "확인", "취소"))
                    StartRequest(offer.token);
            }
            EditorGUILayout.EndScrollView();
        }

        static string ErrorText(string code)
        {
            switch (code)
            {
                case "SAVE_LOCKED":
                    return "Python에서 이 진행본을 사용 중입니다. Python 게임을 닫고 새로고침하세요.";
                case "WORLD_SUPPLY_STALE":
                    return "진행본이 바뀌었습니다. 현재 제안을 확인하고 다시 선택하세요.";
                case "WORLD_SUPPLY_NOT_COMMITTED":
                    return "행동이 저장되지 않았습니다. 현재 상태를 확인하고 다시 시도하세요.";
                default:
                    return "진행을 확인하지 못했습니다. 새로고침하거나 같은 행동을 다시 시도하세요.\n" + code;
            }
        }

        static void Validate(Snapshot data)
        {
            if (data == null || data.format != Format || data.tick < 0 || data.revision < 0 ||
                String.IsNullOrEmpty(data.location) || String.IsNullOrEmpty(data.status) ||
                data.notice == null || data.error == null || data.cargo < 0 || data.cargo_required < 1 ||
                data.gold < 0)
                throw new IOException("WORLD_SUPPLY_FORMAT");
            var offer = data.offer;
            if (data.has_offer && (offer == null || offer.token == null ||
                !Regex.IsMatch(offer.token, @"\A[0-9a-f]{64}\z") ||
                String.IsNullOrEmpty(offer.label) || String.IsNullOrEmpty(offer.line) ||
                String.IsNullOrEmpty(offer.terms)))
                throw new IOException("WORLD_SUPPLY_FORMAT");
            if (!data.has_offer)
                data.offer = null;
        }

        void OnDisable()
        {
            if (cancellation != null)
            {
                cancellation.Cancel();
                cancellation.Dispose();
                cancellation = null;
                _ = pending?.ContinueWith(task => { _ = task.Exception; },
                    TaskContinuationOptions.OnlyOnFaulted);
                pending = null;
            }
            if (koreanFont != null)
                DestroyImmediate(koreanFont);
        }
    }
}
