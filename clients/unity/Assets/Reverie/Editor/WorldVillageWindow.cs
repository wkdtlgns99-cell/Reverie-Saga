using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;

namespace ReverieSaga
{
    public sealed class WorldVillageWindow : EditorWindow
    {
        const double StepInterval = 0.16;
        const double IdleSeconds = 10;

        [Serializable]
        sealed class Landmark
        {
            public string name;
            public int x;
            public int y;
        }

        [Serializable]
        sealed class Resident
        {
            public string id;
            public string role;
            public int x;
            public int y;
        }

        [Serializable]
        sealed class Supply
        {
            public string status;
            public long cargo;
            public int cargo_required;
            public long gold;
            public Resident[] residents;
        }

        [Serializable]
        sealed class Interaction
        {
            public string line;
            public string terms;
            public string label;
            public string token;
        }

        [Serializable]
        sealed class Snapshot
        {
            public string format;
            public long id;
            public long tick;
            public long revision;
            public string error;
            public string name;
            public string status;
            public bool available;
            public int x;
            public int y;
            public int entrance_x;
            public int entrance_y;
            public string[] rows;
            public Landmark[] landmarks;
            public Supply supply;
            public string nearby;
            public bool has_interaction;
            public Interaction interaction;
        }

        readonly List<KeyCode> keys = new List<KeyCode>();
        VillageConnection connection;
        Task<string> pending;
        Snapshot snapshot;
        Font font;
        string workingPath;
        string error;
        string queuedDirection;
        long requestId;
        bool paused;
        bool escapeHeld;
        bool talkHeld;
        bool pendingIdle;
        double lastSample;
        double idle;
        double nextIdle;
        double nextStep;
        double animationEnd;
        Vector2 animationFrom;
        Vector2 scroll;

        [MenuItem("Reverie/마을 걷기")]
        public static void Open() => OpenWorking(null);

        internal static WorldVillageWindow OpenWorking(string path)
        {
            var window = GetWindow<WorldVillageWindow>("마을 걷기");
            window.minSize = new Vector2(500, 440);
            if (window.connection == null)
            {
                window.workingPath = path;
                window.Connect();
            }
            return window;
        }

        void Connect()
        {
            error = null;
            snapshot = null;
            requestId = 0;
            paused = false;
            idle = 0;
            nextStep = animationEnd = nextIdle = 0;
            lastSample = EditorApplication.timeSinceStartup;
            try
            {
                string root = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
                connection = new VillageConnection(root, workingPath);
                Send("inspect", "");
            }
            catch (Exception exception) when (ExpectedFailure(exception))
            {
                Fail(exception);
            }
        }

        void Send(string action, string value)
        {
            if (connection != null && pending == null)
            {
                pendingIdle = action == "idle";
                pending = connection.Send(++requestId, action, value);
            }
        }

        static bool ExpectedFailure(Exception exception)
        {
            return exception is IOException || exception is Win32Exception ||
                exception is InvalidOperationException || exception is ArgumentException ||
                exception is TimeoutException;
        }

        void Receive(double now)
        {
            if (pending == null || !pending.IsCompleted)
                return;
            try
            {
                var next = JsonUtility.FromJson<Snapshot>(pending.GetAwaiter().GetResult());
                Validate(next);
                if (snapshot != null && (next.x != snapshot.x || next.y != snapshot.y))
                {
                    animationFrom = new Vector2(snapshot.x, snapshot.y);
                    animationEnd = now + StepInterval;
                }
                if (next.has_interaction != (snapshot?.has_interaction ?? false))
                    scroll.y = next.has_interaction ? 10000 : 0;
                snapshot = next;
                error = next.error;
                if (pendingIdle && error == "SAVE_UNAVAILABLE")
                {
                    idle += IdleSeconds;
                    nextIdle = now + StepInterval;
                }
            }
            catch (Exception exception) when (ExpectedFailure(exception))
            {
                Fail(exception);
            }
            finally
            {
                pending = null;
                pendingIdle = false;
                Repaint();
            }
        }

        void Fail(Exception exception)
        {
            error = exception.Message;
            snapshot = null;
            Disconnect();
            Repaint();
        }

        static bool Walkable(Snapshot state, int x, int y)
        {
            return y >= 0 && y < state.rows.Length && x >= 0 &&
                x < state.rows[y].Length && state.rows[y][x] == '.';
        }

        void Validate(Snapshot state)
        {
            if (state == null || state.format != VillageConnection.Format || state.id != requestId ||
                state.tick < 0 || state.revision < 0 || String.IsNullOrEmpty(state.name) ||
                state.error == null || state.status == null || state.rows == null ||
                state.rows.Length < 1 || state.rows.Length > 32 || state.landmarks == null)
                throw new IOException("VILLAGE_RESPONSE");
            int width = state.rows[0]?.Length ?? 0;
            if (width < 1 || width > 32)
                throw new IOException("VILLAGE_RESPONSE");
            foreach (string row in state.rows)
                if (row == null || row.Length != width)
                    throw new IOException("VILLAGE_RESPONSE");
            if (!Walkable(state, state.x, state.y) ||
                !Walkable(state, state.entrance_x, state.entrance_y))
                throw new IOException("VILLAGE_RESPONSE");
            foreach (var landmark in state.landmarks)
                if (landmark == null || String.IsNullOrEmpty(landmark.name) ||
                    landmark.x < 0 || landmark.x >= width ||
                    landmark.y < 0 || landmark.y >= state.rows.Length)
                    throw new IOException("VILLAGE_RESPONSE");
            if (state.supply == null || state.supply.status == null || state.supply.residents == null ||
                state.supply.cargo < 0 || state.supply.cargo_required < 1 ||
                state.supply.gold < 0 || state.nearby == null)
                throw new IOException("VILLAGE_SUPPLY_RESPONSE");
            foreach (var npc in state.supply.residents)
                if (npc == null || String.IsNullOrEmpty(npc.id) || String.IsNullOrEmpty(npc.role) ||
                    npc.x < 0 || npc.x >= width || npc.y < 0 || npc.y >= state.rows.Length)
                    throw new IOException("VILLAGE_SUPPLY_RESPONSE");
            if (state.has_interaction)
            {
                var dialog = state.interaction;
                if (dialog == null || String.IsNullOrEmpty(dialog.line) || dialog.terms == null ||
                    dialog.label == null || dialog.token == null ||
                    (dialog.token.Length != 0 && (!Regex.IsMatch(dialog.token, @"\A[0-9a-f]{64}\z") ||
                        dialog.terms.Length == 0 || dialog.label.Length == 0)))
                    throw new IOException("VILLAGE_SUPPLY_RESPONSE");
            }
        }

        void Tick()
        {
            double now = EditorApplication.timeSinceStartup;
            double elapsed = now - lastSample;
            lastSample = now;
            bool wasPending = pending != null;
            Receive(now);
            if (now < animationEnd)
                Repaint();
            if (focusedWindow == this)
                AdvanceInput(now, elapsed, wasPending);
        }

        void AdvanceInput(double now, double elapsed, bool wasPending)
        {
            if (paused || snapshot == null || !snapshot.available || connection == null ||
                wasPending || pending != null || now < animationEnd)
                return;
            if (queuedDirection != null || keys.Count > 0)
            {
                if (now >= nextStep)
                    Walk(now);
                return;
            }
            idle += elapsed;
            if (idle >= IdleSeconds && now >= nextIdle)
            {
                idle -= IdleSeconds;
                Send("idle", "1");
            }
        }

        void Walk(double now)
        {
            nextStep = now + StepInterval;
            string direction = queuedDirection ?? Direction(keys[keys.Count - 1]);
            queuedDirection = null;
            Send("step", direction);
        }

        static string Direction(KeyCode key)
        {
            switch (key)
            {
                case KeyCode.W: case KeyCode.UpArrow: return "up";
                case KeyCode.A: case KeyCode.LeftArrow: return "left";
                case KeyCode.S: case KeyCode.DownArrow: return "down";
                case KeyCode.D: case KeyCode.RightArrow: return "right";
                default: return "";
            }
        }

        void HandleInput(Event input)
        {
            if (input.type != EventType.KeyDown && input.type != EventType.KeyUp)
                return;
            if (input.keyCode == KeyCode.Escape)
            {
                if (input.type == EventType.KeyDown && !escapeHeld)
                {
                    paused = !paused;
                    escapeHeld = true;
                    keys.Clear();
                    queuedDirection = null;
                    Repaint();
                }
                if (input.type == EventType.KeyUp)
                    escapeHeld = false;
                input.Use();
                return;
            }
            if (input.keyCode == KeyCode.E)
            {
                if (input.type == EventType.KeyDown && !talkHeld &&
                    !input.alt && !input.control && !input.command)
                {
                    talkHeld = true;
                    Talk();
                }
                if (input.type == EventType.KeyUp)
                    talkHeld = false;
                input.Use();
                return;
            }
            string direction = Direction(input.keyCode);
            if (direction.Length == 0)
                return;
            if (input.type == EventType.KeyUp)
                keys.Remove(input.keyCode);
            else if (!paused && !input.alt && !input.control && !input.command &&
                !keys.Contains(input.keyCode))
            {
                keys.Add(input.keyCode);
                queuedDirection = direction;
                double now = EditorApplication.timeSinceStartup;
                if (snapshot != null && snapshot.available && pending == null && now >= animationEnd)
                    Walk(now);
            }
            input.Use();
        }

        bool CanInteract() => !paused && snapshot != null && snapshot.available &&
            pending == null && EditorApplication.timeSinceStartup >= animationEnd;

        void Talk()
        {
            if (CanInteract() && snapshot.nearby.Length != 0)
            {
                keys.Clear();
                queuedDirection = null;
                Send("talk", snapshot.nearby);
            }
        }

        void Confirm()
        {
            if (CanInteract() && snapshot.has_interaction && snapshot.interaction.token.Length != 0)
                Send("confirm", snapshot.interaction.token);
        }

        void OnGUI()
        {
            HandleInput(Event.current);
            if (font == null)
                font = Font.CreateDynamicFontFromOSFont("Malgun Gothic", 14);
            var text = new GUIStyle(EditorStyles.wordWrappedLabel) { font = font, richText = false };
            if (snapshot == null)
            {
                EditorGUILayout.LabelField(error == null ? "마을을 여는 중…" : ErrorText(error), text);
                if (connection == null && GUILayout.Button("다시 연결"))
                    Connect();
                return;
            }
            EditorGUILayout.LabelField(
                $"{snapshot.name} · 게임 {snapshot.tick}초 · 기록 {snapshot.revision}", text);
            EditorGUILayout.LabelField(
                paused ? "일시정지 · ESC로 재개" : "WASD / 방향키로 걷기 · E로 말 걸기 · ESC로 일시정지", text);
            string notice = String.IsNullOrEmpty(error) ? snapshot.status : ErrorText(error);
            EditorGUILayout.LabelField(String.IsNullOrEmpty(notice) ? " " : notice, text);
            scroll = EditorGUILayout.BeginScrollView(scroll);
            DrawMap(text);
            DrawSupply(text);
            EditorGUILayout.EndScrollView();
        }

        void DrawSupply(GUIStyle text)
        {
            var supply = snapshot.supply;
            var button = new GUIStyle(GUI.skin.button) { font = font };
            EditorGUILayout.LabelField(supply.status, text);
            EditorGUILayout.LabelField($"복구품 {supply.cargo}/{supply.cargo_required} · 소지금 {supply.gold}금", text);
            using (new EditorGUI.DisabledScope(!CanInteract()))
            {
                if (snapshot.has_interaction)
                {
                    var dialog = snapshot.interaction;
                    EditorGUILayout.LabelField(dialog.line, text);
                    if (dialog.token.Length != 0)
                    {
                        EditorGUILayout.LabelField(dialog.terms, text);
                        if (GUILayout.Button(dialog.label + " 확인", button))
                            Confirm();
                    }
                    if (GUILayout.Button("대화 닫기", button))
                        Send("close", "");
                }
                else if (snapshot.nearby.Length != 0 && GUILayout.Button("E · 말 걸기", button))
                    Talk();
            }
        }

        static string ErrorText(string code)
        {
            switch (code)
            {
                case "SAVE_LOCKED": return "다른 화면에서 진행본을 사용 중입니다. 해당 화면을 닫고 다시 연결하세요.";
                case "VILLAGE_BLOCKED": return "길이 막혀 있습니다.";
                case "SAVE_UNAVAILABLE": return "행동을 저장하지 못했습니다. 다시 시도해 주세요.";
                case "VILLAGE_NPC_OUT_OF_REACH": return "주민의 바로 옆 칸에서 말을 걸어 주세요.";
                case "VILLAGE_OFFER_STALE": return "의뢰 조건이 달라졌습니다. 화면의 내용을 다시 확인해 주세요.";
                default: return code;
            }
        }

        void DrawMap(GUIStyle text)
        {
            int width = snapshot.rows[0].Length;
            int height = snapshot.rows.Length;
            float size = Mathf.Clamp((position.width - 30) / width, 18, 38);
            var area = GUILayoutUtility.GetRect(width * size, height * size, GUILayout.ExpandWidth(false));
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                {
                    char tile = snapshot.rows[y][x];
                    var cell = new Rect(area.x + x * size, area.y + y * size, size - 1, size - 1);
                    Color color;
                    switch (tile)
                    {
                        case 'H': color = new Color(.48f, .26f, .22f); break;
                        case 'M': color = new Color(.71f, .43f, .19f); break;
                        case 'A': color = new Color(.27f, .41f, .55f); break;
                        case 'W': color = new Color(.43f, .33f, .22f); break;
                        case '#': color = new Color(.19f, .31f, .24f); break;
                        default: color = new Color(.63f, .54f, .38f); break;
                    }
                    EditorGUI.DrawRect(cell, color);
                }
            var label = new GUIStyle(text) { normal = { textColor = Color.white } };
            foreach (var landmark in snapshot.landmarks)
                GUI.Label(new Rect(area.x + landmark.x * size + 2, area.y + landmark.y * size,
                    size * 2, size), landmark.name, label);
            if (snapshot.available)
                foreach (var npc in snapshot.supply.residents)
                {
                    float x = area.x + npc.x * size;
                    float y = area.y + npc.y * size + size * .62f;
                    var marker = new Color(.99f, .79f, .32f);
                    EditorGUI.DrawRect(new Rect(x + 2, y + 4, 7, 7), marker);
                    GUI.Label(new Rect(x + 11, y, size * 2, 22), npc.role, label);
                }
            GUI.Label(new Rect(area.x + snapshot.entrance_x * size + 2,
                area.y + snapshot.entrance_y * size, size * 2, size), "입구", label);
            if (!snapshot.available)
                return;
            var target = new Vector2(snapshot.x, snapshot.y);
            float progress = 1 - (float)((animationEnd - EditorApplication.timeSinceStartup) / StepInterval);
            var point = Vector2.Lerp(animationFrom, target, Mathf.Clamp01(progress));
            float px = area.x + (point.x + .5f) * size;
            float py = area.y + (point.y + .5f) * size;
            EditorGUI.DrawRect(new Rect(px - 7, py - 2, 14, 11), new Color(.10f, .34f, .75f));
            EditorGUI.DrawRect(new Rect(px - 4, py - 9, 8, 8), new Color(1, .81f, .62f));
        }

        void Disconnect()
        {
            keys.Clear();
            queuedDirection = null;
            VillageConnection.Observe(pending);
            pending = null;
            connection?.Dispose();
            connection = null;
        }

        void OnEnable() => EditorApplication.update += Tick;

        void OnFocus() => lastSample = EditorApplication.timeSinceStartup;

        void OnLostFocus()
        {
            keys.Clear();
            queuedDirection = null;
            escapeHeld = false;
            talkHeld = false;
        }

        void OnDisable()
        {
            EditorApplication.update -= Tick;
            Disconnect();
            if (font != null)
                DestroyImmediate(font);
        }
    }
}
