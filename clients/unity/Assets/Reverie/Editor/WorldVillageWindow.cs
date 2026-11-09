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
        sealed class Market
        {
            public int stock;
            public int capacity;
            public string road;

            public bool Visible => capacity > 0;

            public bool Valid => capacity == 0
                ? stock == 0 && String.IsNullOrEmpty(road)
                : capacity > 0 && capacity <= 32 && stock >= 0 && stock <= capacity &&
                    (road == "blocked" || road == "restored" || road == "open");
        }

        [Serializable]
        sealed class Supply
        {
            public string status;
            public long cargo;
            public int cargo_required;
            public long gold;
            public Resident[] residents;
            public Market market;
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
        sealed class RoadTest
        {
            public int width, height, actor_cell, gate_cell, enemy_cell, actor_hp, enemy_hp, stamina;
            public int[] walls;
            public bool gate_open, engaged;
            public long tick, revision;
            public string status;
            public string[] messages;
        }

        [Serializable]
        sealed class WorldCombat
        {
            public bool active, ambush_pending, player_turn;
            public int player_hp, bandit_hp, bandit_x, bandit_y;
            public string[] order;
            public string last_actor, last_action;
        }

        [Serializable]
        sealed class DungeonView
        {
            public bool inside, can_enter, can_exit, can_engage, active, player_turn, pommel_used;
            public int x, y, orc_x, orc_y, player_hp, orc_hp, pommel_damage;
            public string[] order;
            public string last_action, weapon, pommel_name;
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
            public VillageLayout layout;
            public Landmark[] landmarks;
            public Supply supply;
            public string nearby;
            public bool has_interaction;
            public Interaction interaction;
            public bool can_start_road_test;
            public bool has_road_test;
            public RoadTest road_test;
            public bool has_world_combat;
            public WorldCombat world_combat;
            public bool has_dungeon;
            public DungeonView dungeon;

            public WorldCombat Battle => has_world_combat ? world_combat : null;
            public DungeonView Room => has_dungeon ? dungeon : null;
            public bool InDungeon => Room?.inside ?? false;
            public bool CanMove => InDungeon ? !Room.active : available;
            public Vector2 Location => InDungeon ? new Vector2(Room.x, Room.y) : new Vector2(x, y);
        }

        readonly List<KeyCode> keys = new List<KeyCode>();
        VillageConnection connection;
        Task<string> pending;
        Snapshot snapshot;
        Font font;
        [SerializeField] string workingPath;
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
        double nextCombatAction;
        double animationEnd;
        Vector2 animationFrom;
        Vector2 scroll;
        Village3DPreview preview;
        bool show3D = true;
        bool previewFailed;
        [SerializeField] string worldSeed;

        [MenuItem("Reverie/마을 걷기")]
        public static void Open() => OpenWorking(null);

        internal static WorldVillageWindow OpenWorking(string path)
            => OpenVillage(null, path, "마을 걷기");

        internal static WorldVillageWindow OpenSeeded(string seed)
        {
            if (!Regex.IsMatch(seed, VillageLayout.SeedPattern))
                throw new ArgumentException("WORLD_SEED");
            return OpenVillage(seed, null, "물버들 " + seed.Substring(0, 8));
        }

        static WorldVillageWindow OpenVillage(string seed, string path, string title)
        {
            foreach (var open in Resources.FindObjectsOfTypeAll<WorldVillageWindow>())
                if ((open.worldSeed ?? "") == (seed ?? "") &&
                    (open.workingPath ?? "") == (path ?? ""))
                {
                    open.Focus();
                    if (open.connection == null)
                        open.Connect();
                    return open;
                }
            var window = CreateInstance<WorldVillageWindow>();
            window.worldSeed = seed;
            window.workingPath = path;
            window.titleContent = new GUIContent(title);
            window.minSize = new Vector2(500, 440);
            window.Show();
            window.Connect();
            return window;
        }

        void Connect()
        {
            error = null;
            snapshot = null;
            requestId = 0;
            paused = false;
            idle = 0;
            nextStep = animationEnd = nextIdle = nextCombatAction = 0;
            lastSample = EditorApplication.timeSinceStartup;
            try
            {
                string root = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
                connection = new VillageConnection(root, String.IsNullOrEmpty(workingPath) ? null : workingPath,
                    String.IsNullOrEmpty(worldSeed) ? null : worldSeed);
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
                pendingIdle = action == "idle" || (action == "dungeon" && value == "wait");
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
                if (snapshot != null && next.InDungeon != snapshot.InDungeon)
                {
                    animationFrom = next.Location;
                    animationEnd = now;
                    keys.Clear();
                    queuedDirection = null;
                    idle = 0;
                }
                else if (snapshot != null && next.Location != snapshot.Location)
                {
                    animationFrom = snapshot.Location;
                    animationEnd = now + StepInterval;
                }
                if (next.has_interaction != (snapshot?.has_interaction ?? false))
                    scroll.y = next.has_interaction ? 10000 : 0;
                if (next.has_road_test != (snapshot?.has_road_test ?? false))
                {
                    keys.Clear();
                    queuedDirection = null;
                    scroll = Vector2.zero;
                }
                if ((next.Battle?.active ?? false) != (snapshot?.Battle?.active ?? false) ||
                    (next.Room?.active ?? false) != (snapshot?.Room?.active ?? false))
                {
                    keys.Clear();
                    queuedDirection = null;
                    idle = 0;
                }
                var prior = snapshot?.Battle;
                var battle = next.Battle;
                if (preview != null && snapshot != null && (show3D || next.InDungeon) &&
                    next.InDungeon == snapshot.InDungeon && next.revision > snapshot.revision)
                {
                    bool playerHit = next.InDungeon ? next.Room.orc_hp < snapshot.Room.orc_hp :
                        prior != null && battle != null && battle.bandit_hp < prior.bandit_hp;
                    bool enemyHit = next.InDungeon ? next.Room.player_hp < snapshot.Room.player_hp :
                        prior != null && battle != null && battle.player_hp < prior.player_hp;
                    if (playerHit || enemyHit)
                    {
                        preview.Hit(playerHit, now, next.InDungeon && next.Room.last_action == "pommel");
                        nextCombatAction = Math.Max(nextCombatAction, now + .55);
                    }
                }
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
            if (state.layout == null)
                throw new IOException("VILLAGE_LAYOUT");
            state.layout.Validate(state.rows);
            if (!String.IsNullOrEmpty(worldSeed) && state.layout.seed != worldSeed)
                throw new IOException("WORLD_SEED");
            if (state.has_dungeon && (state.Room == null || state.Room.order == null ||
                state.Room.order.Length > 2 || !Interior(state.Room.x, state.Room.y) ||
                !Interior(state.Room.orc_x, state.Room.orc_y) || state.Room.player_hp < 0 ||
                state.Room.orc_hp < 0 || state.Room.last_action == null ||
                String.IsNullOrEmpty(state.Room.weapon) || String.IsNullOrEmpty(state.Room.pommel_name) ||
                state.Room.pommel_damage < 1))
                throw new IOException("DUNGEON_RESPONSE");
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
                state.supply.gold < 0 || state.nearby == null ||
                (state.supply.market != null && !state.supply.market.Valid))
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
            if (state.has_road_test)
                ValidateRoadTest(state.road_test);
            var combat = state.Battle;
            if (state.has_world_combat && (combat == null ||
                combat.order == null || combat.order.Length > 4 ||
                combat.active != (combat.order.Length > 0) ||
                combat.player_turn && !combat.active || combat.player_hp < 0 ||
                combat.bandit_hp < 0 || !Walkable(state, combat.bandit_x, combat.bandit_y) ||
                combat.last_actor == null || combat.last_action == null))
                throw new IOException("WORLD_COMBAT_RESPONSE");
        }

        static bool Interior(int x, int y) => x > 0 && y > 0 &&
            x < VillageLayout.RoomSize - 1 && y < VillageLayout.RoomSize - 1;

        static void ValidateRoadTest(RoadTest battle)
        {
            if (battle == null || battle.width < 1 || battle.width > 32 ||
                battle.height < 1 || battle.height > 32 || battle.walls == null ||
                battle.messages == null || String.IsNullOrEmpty(battle.status) ||
                battle.tick < 0 || battle.revision < 0 || battle.actor_hp < 0 ||
                battle.enemy_hp < 0 || battle.stamina < 0)
                throw new IOException("VILLAGE_ROAD_TEST_RESPONSE");
            int cells = battle.width * battle.height;
            if (battle.actor_cell < 0 || battle.actor_cell >= cells ||
                battle.enemy_cell < 0 || battle.enemy_cell >= cells ||
                battle.gate_cell < 0 || battle.gate_cell >= cells ||
                Array.Exists(battle.walls, wall => wall < 0 || wall >= cells))
                throw new IOException("VILLAGE_ROAD_TEST_RESPONSE");
        }

        void Tick()
        {
            double now = EditorApplication.timeSinceStartup;
            double elapsed = now - lastSample;
            lastSample = now;
            bool wasPending = pending != null;
            Receive(now);
            if (now < animationEnd || ((show3D || (snapshot?.InDungeon ?? false)) &&
                (preview?.IsPlaying(now) ?? false)))
                Repaint();
            if (focusedWindow == this)
                AdvanceInput(now, elapsed, wasPending);
        }

        void AdvanceInput(double now, double elapsed, bool wasPending)
        {
            if (paused || snapshot == null || connection == null ||
                wasPending || pending != null || now < animationEnd)
                return;
            var combat = snapshot.Battle;
            var room = snapshot.Room;
            if ((combat?.active ?? false) || (room?.active ?? false))
            {
                bool playerTurn = snapshot.InDungeon ? room.player_turn : combat.player_turn;
                if (!playerTurn && String.IsNullOrEmpty(error) && now >= nextCombatAction)
                {
                    nextCombatAction = now + .35;
                    Send(snapshot.InDungeon ? "dungeon" : "world-combat", "advance");
                }
                return;
            }
            if (!snapshot.CanMove)
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
                if (snapshot.InDungeon) Send("dungeon", "wait");
                else Send("idle", "1");
            }
        }

        void Walk(double now)
        {
            nextStep = now + StepInterval;
            string direction = queuedDirection ?? Direction(keys[keys.Count - 1]);
            queuedDirection = null;
            Send(snapshot.InDungeon ? "dungeon" : "step", direction);
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
                if (snapshot != null && snapshot.has_road_test)
                    CombatAction(direction);
                else
                {
                    queuedDirection = direction;
                    double now = EditorApplication.timeSinceStartup;
                    if (snapshot != null && snapshot.CanMove && pending == null && now >= animationEnd)
                        Walk(now);
                }
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

        void CombatAction(string action)
        {
            if (!paused && pending == null && snapshot != null && snapshot.has_road_test &&
                snapshot.road_test.actor_hp > 0 && snapshot.road_test.enemy_hp > 0)
                Send("combat", action);
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
            if (snapshot.has_road_test)
            {
                DrawRoadTest(text);
                return;
            }
            EditorGUILayout.LabelField(
                $"{snapshot.name} · 게임 {snapshot.tick}초 · 기록 {snapshot.revision}", text);
            EditorGUILayout.LabelField(
                paused ? "일시정지 · ESC로 재개" : "WASD / 방향키로 걷기 · E로 말 걸기 · ESC로 일시정지", text);
            string notice = String.IsNullOrEmpty(error) ? snapshot.status : ErrorText(error);
            EditorGUILayout.LabelField(String.IsNullOrEmpty(notice) ? " " : notice, text);
            scroll = EditorGUILayout.BeginScrollView(scroll);
            if (snapshot.InDungeon)
            {
                DrawDungeon(text);
                EditorGUILayout.EndScrollView();
                return;
            }
            show3D = EditorGUILayout.ToggleLeft("3D 도트 화면", show3D);
            if (!show3D || !Draw3D(text))
                DrawMap(text);
            if (snapshot.Room != null && snapshot.Room.can_enter && CanInteract() &&
                GUILayout.Button("던전 들어가기"))
                Send("dungeon", "enter");
            DrawWorldCombat(text);
            DrawSupply(text);
            using (new EditorGUI.DisabledScope(!CanInteract()))
                if (snapshot.can_start_road_test &&
                    GUILayout.Button("마을 밖 길목 전투 테스트", new GUIStyle(GUI.skin.button) { font = font }))
                    Send("road-test", "");
            EditorGUILayout.EndScrollView();
        }

        void DrawDungeon(GUIStyle text)
        {
            var room = snapshot.Room;
            EditorGUILayout.LabelField(room.active ? "남쪽 석굴 · 턴제 전투" : "남쪽 석굴 · 탐색", text);
            if (!Draw3D(text))
            {
                for (int y = 0; y < VillageLayout.RoomSize; y++)
                {
                    EditorGUILayout.BeginHorizontal();
                    for (int x = 0; x < VillageLayout.RoomSize; x++)
                    {
                        string mark = (x == room.x && y == room.y) ? "나" :
                            (x == room.orc_x && y == room.orc_y && room.orc_hp > 0) ? "오크" :
                            Interior(x, y) ? "·" : "벽";
                        GUILayout.Label(mark, text, GUILayout.Width(45));
                    }
                    EditorGUILayout.EndHorizontal();
                }
            }
            EditorGUILayout.LabelField($"내 체력 {room.player_hp} · 오크 체력 {room.orc_hp}", text);
            EditorGUILayout.LabelField($"장착 무기 · {room.weapon}", text);
            if (room.active)
                EditorGUILayout.LabelField(String.Join(" → ", room.order), text);
            else if (room.orc_hp == 0 || room.player_hp == 0)
                EditorGUILayout.LabelField(room.orc_hp == 0 ? "전투 승리" : "전투 패배", text);
            if (room.last_action == "pommel" && room.active)
                EditorGUILayout.LabelField("오크가 비틀거립니다.", text);
            else if (room.last_action == "stagger")
                EditorGUILayout.LabelField("오크가 균형을 잃어 차례를 넘겼습니다.", text);
            using (new EditorGUI.DisabledScope(paused || pending != null ||
                (preview?.IsPlaying(EditorApplication.timeSinceStartup) ?? false)))
            {
                if (room.active && room.player_turn)
                {
                    if (GUILayout.Button("베기")) Send("dungeon", "attack");
                    using (new EditorGUI.DisabledScope(room.pommel_used))
                    {
                        string skill = room.pommel_used ? $"{room.pommel_name} · 사용함" :
                            $"{room.pommel_name} · 피해 {room.pommel_damage}, 오크 차례 넘기기";
                        if (GUILayout.Button(skill)) Send("dungeon", "pommel");
                    }
                    if (GUILayout.Button("자리 지키기")) Send("dungeon", "hold");
                }
                else if (room.active && !String.IsNullOrEmpty(error) && GUILayout.Button("행동 다시 시도"))
                    Send("dungeon", "advance");
                else if (room.can_engage && GUILayout.Button("오크 공격"))
                    Send("dungeon", "engage");
                if (room.can_exit && GUILayout.Button("마을로 나오기"))
                    Send("dungeon", "exit");
            }
        }

        bool Draw3D(GUIStyle text)
        {
            if (previewFailed || (preview == null && !Village3DPreview.HasRig))
            {
                EditorGUILayout.LabelField(previewFailed ? "3D 화면을 열지 못했습니다." :
                    Village3DPreview.RigInstructions, text);
                return false;
            }
            var area = GUILayoutUtility.GetAspectRect(16f / 9f, GUILayout.ExpandWidth(true));
            if (Event.current.type != EventType.Repaint)
                return true;
            try
            {
                if (preview == null)
                    preview = new Village3DPreview(snapshot.rows, snapshot.layout);
                foreach (var npc in snapshot.supply.residents)
                    preview.SetResident(npc.id, npc.x, npc.y);
                double now = EditorApplication.timeSinceStartup;
                var target = snapshot.Location;
                var direction = target - animationFrom;
                var point = Vector2.Lerp(animationFrom, target, 1 - (float)((animationEnd - now) / StepInterval));
                if (snapshot.InDungeon)
                {
                    var room = snapshot.Room;
                    var dungeonImage = preview.Render(point, direction, now < animationEnd, true,
                        room.orc_hp > 0 || preview.ShowDefeated(now),
                        new Vector2(room.orc_x, room.orc_y), now, dungeon: true);
                    GUI.DrawTexture(area, dungeonImage, ScaleMode.ScaleToFit, false);
                    return true;
                }
                var battle = snapshot.Battle;
                bool bandit = battle != null && (battle.active || preview.ShowDefeated(now));
                var image = preview.Render(point, direction, now < animationEnd,
                    snapshot.available || bandit, bandit,
                    battle == null ? Vector2.zero : new Vector2(battle.bandit_x, battle.bandit_y), now);
                GUI.DrawTexture(area, image, ScaleMode.ScaleToFit, false);
            }
            catch (Exception failure) when (ExpectedFailure(failure))
            {
                Debug.LogException(failure);
                preview?.Dispose();
                preview = null;
                previewFailed = true;
                Repaint();
            }
            return true;
        }

        void DrawWorldCombat(GUIStyle text)
        {
            var combat = snapshot.Battle;
            if (combat == null)
                return;
            var button = new GUIStyle(GUI.skin.button) { font = font };
            if (combat.ambush_pending)
            {
                using (new EditorGUI.DisabledScope(paused || pending != null))
                    if (GUILayout.Button("행동 결과 다시 확인", button)) Send("inspect", "");
                return;
            }
            if (combat.active)
            {
                EditorGUILayout.LabelField(
                    $"턴제 전투 · 내 체력 {combat.player_hp} · 도적 체력 {combat.bandit_hp}", text);
                EditorGUILayout.LabelField(String.Join(" → ", combat.order), text);
                string action = combat.last_action == "open" ? "첫 공격" :
                    combat.last_action == "attack" ? "공격" : "자리 지킴";
                EditorGUILayout.LabelField($"{combat.last_actor} · {action}", text);
                using (new EditorGUI.DisabledScope(paused || pending != null ||
                    (show3D && (preview?.IsPlaying(EditorApplication.timeSinceStartup) ?? false))))
                {
                    if (combat.player_turn)
                    {
                        if (GUILayout.Button("공격", button)) Send("world-combat", "attack");
                        if (GUILayout.Button("자리 지키기", button)) Send("world-combat", "hold");
                    }
                    else if (!String.IsNullOrEmpty(error) && GUILayout.Button("행동 다시 시도", button))
                        Send("world-combat", "advance");
                }
            }
            else if (combat.last_action.Length != 0)
                EditorGUILayout.LabelField(combat.bandit_hp == 0 ? "전투 승리" : "전투 패배", text);
        }

        void DrawRoadTest(GUIStyle text)
        {
            var battle = snapshot.road_test;
            var button = new GUIStyle(GUI.skin.button) { font = font };
            EditorGUILayout.LabelField("마을 밖 길목 전투 테스트", text);
            EditorGUILayout.LabelField($"내 체력 {battle.actor_hp} · 기력 {battle.stamina} · 적 체력 {battle.enemy_hp}", text);
            string phase = battle.engaged ? "턴제 전투" : "길목 탐색";
            EditorGUILayout.LabelField(paused ? "일시정지 · ESC로 재개" :
                $"{phase} · {battle.tick}초 · 방향키로 이동", text);
            for (int y = 0; y < battle.height; y++)
            {
                EditorGUILayout.BeginHorizontal();
                for (int x = 0; x < battle.width; x++)
                {
                    int cell = y * battle.width + x;
                    string label = cell == battle.actor_cell ? "나" :
                        cell == battle.enemy_cell && battle.enemy_hp > 0 ? "적" :
                        cell == battle.gate_cell ? (battle.gate_open ? "열린 문" : "닫힌 문") :
                        Array.IndexOf(battle.walls, cell) >= 0 ? "벽" : "·";
                    GUILayout.Label(label, button, GUILayout.Width(64));
                }
                EditorGUILayout.EndHorizontal();
            }
            if (!String.IsNullOrEmpty(error))
                EditorGUILayout.LabelField(ErrorText(error), text);
            foreach (string message in battle.messages)
                EditorGUILayout.LabelField(message, text);
            if (battle.enemy_hp == 0 || battle.actor_hp == 0)
                EditorGUILayout.LabelField(battle.enemy_hp == 0 ? "전투 승리" : "전투 패배", text);
            using (new EditorGUI.DisabledScope(paused || pending != null || battle.actor_hp == 0 || battle.enemy_hp == 0))
            {
                EditorGUILayout.BeginHorizontal();
                if (GUILayout.Button("문 열기", button)) CombatAction("open");
                if (GUILayout.Button("공격", button)) CombatAction("attack");
                if (GUILayout.Button("쉬기", button)) CombatAction("rest");
                EditorGUILayout.EndHorizontal();
            }
            using (new EditorGUI.DisabledScope(pending != null))
                if (GUILayout.Button("마을로 돌아가기", button))
                    Send("return", "");
        }

        void DrawSupply(GUIStyle text)
        {
            var supply = snapshot.supply;
            var button = new GUIStyle(GUI.skin.button) { font = font };
            EditorGUILayout.LabelField(supply.status, text);
            var market = supply.market;
            if (market != null && market.Visible)
            {
                string road = market.road == "blocked" ? "보급로 막힘" :
                    market.road == "restored" ? "보급로 복구됨" : "보급로 정상";
                EditorGUILayout.LabelField($"시장 진열대 · {market.stock}/{market.capacity} · {road}", text);
                DrawMarketShelf(GUILayoutUtility.GetRect(144, 24, GUILayout.ExpandWidth(false)), market);
            }
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
                case "DUNGEON_WALL": return "석굴 벽에 막혔습니다.";
                case "DUNGEON_OCCUPIED": return "오크가 서 있는 칸입니다.";
                case "DUNGEON_GATE": return "입구 바로 앞에서 이용할 수 있습니다.";
                case "DUNGEON_SKILL_SPENT": return "이번 전투에서 이미 사용한 기술입니다.";
                case "OUT_OF_RANGE": return "공격하려면 대상에게 더 가까이 가세요.";
                case "SAVE_UNAVAILABLE": return "행동을 저장하지 못했습니다. 다시 시도해 주세요.";
                case "VILLAGE_NPC_OUT_OF_REACH": return "주민의 바로 옆 칸에서 말을 걸어 주세요.";
                case "VILLAGE_OFFER_STALE": return "의뢰 조건이 달라졌습니다. 화면의 내용을 다시 확인해 주세요.";
                case "VILLAGE_ENTRANCE_REQUIRED": return "마을 입구에서 전투 테스트를 열 수 있습니다.";
                default: return code;
            }
        }

        void DrawMap(GUIStyle text)
        {
            int width = snapshot.rows[0].Length;
            int height = snapshot.rows.Length;
            float size = Mathf.Clamp((position.width - 30) / width, 18, 38);
            var area = GUILayoutUtility.GetRect(width * size, height * size, GUILayout.ExpandWidth(false));
            Rect marketTile = default;
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                {
                    char tile = snapshot.rows[y][x];
                    var cell = new Rect(area.x + x * size, area.y + y * size, size - 1, size - 1);
                    Color color;
                    switch (tile)
                    {
                        case 'H': color = new Color(.48f, .26f, .22f); break;
                        case 'M':
                            color = new Color(.71f, .43f, .19f);
                            marketTile = cell;
                            break;
                        case 'A': color = new Color(.27f, .41f, .55f); break;
                        case 'W': color = new Color(.43f, .33f, .22f); break;
                        case '#': color = new Color(.19f, .31f, .24f); break;
                        default: color = new Color(.63f, .54f, .38f); break;
                    }
                    EditorGUI.DrawRect(cell, color);
                }
            var market = snapshot.supply.market;
            if (market != null && market.Visible && marketTile.width > 0)
                DrawMarketShelf(new Rect(marketTile.x, marketTile.y - size * .45f,
                    size * 1.45f, size * .36f), market);
            var label = new GUIStyle(text) { normal = { textColor = Color.white } };
            foreach (var landmark in snapshot.landmarks)
                GUI.Label(new Rect(area.x + landmark.x * size + 2, area.y + landmark.y * size,
                    size * 2, size), landmark.name, label);
            bool showActors = snapshot.available || (snapshot.Battle?.active ?? false);
            if (showActors)
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
            GUI.Label(new Rect(area.x + snapshot.layout.gate_x * size + 2,
                area.y + snapshot.layout.gate_y * size, size * 2, size), "석굴", label);
            var combat = snapshot.Battle;
            if (combat != null && combat.bandit_hp > 0 && combat.active)
                GUI.Label(new Rect(area.x + combat.bandit_x * size,
                    area.y + combat.bandit_y * size, size * 2, size), "도적", label);
            if (!showActors)
                return;
            var target = new Vector2(snapshot.x, snapshot.y);
            float progress = 1 - (float)((animationEnd - EditorApplication.timeSinceStartup) / StepInterval);
            var point = Vector2.Lerp(animationFrom, target, Mathf.Clamp01(progress));
            float px = area.x + (point.x + .5f) * size;
            float py = area.y + (point.y + .5f) * size;
            EditorGUI.DrawRect(new Rect(px - 7, py - 2, 14, 11), new Color(.10f, .34f, .75f));
            EditorGUI.DrawRect(new Rect(px - 4, py - 9, 8, 8), new Color(1, .81f, .62f));
        }

        static void DrawMarketShelf(Rect area, Market market)
        {
            var rail = market.road == "blocked" ? new Color(.72f, .29f, .23f) :
                market.road == "restored" ? new Color(.27f, .67f, .42f) : new Color(.44f, .57f, .65f);
            EditorGUI.DrawRect(area, new Color(.18f, .15f, .12f));
            EditorGUI.DrawRect(new Rect(area.x, area.yMax - 2, area.width, 2), rail);
            float slotWidth = area.width / market.capacity;
            float gap = Mathf.Min(2, slotWidth * .2f);
            for (int slot = 0; slot < market.capacity; slot++)
            {
                var cell = new Rect(area.x + slot * slotWidth + gap, area.y + 2,
                    slotWidth - gap * 2, area.height - 5);
                bool filled = slot < market.stock;
                EditorGUI.DrawRect(cell, filled ? new Color(.85f, .64f, .30f) :
                    new Color(.29f, .26f, .22f));
                if (filled)
                    EditorGUI.DrawRect(new Rect(cell.center.x - 1, cell.y, 2, cell.height),
                        new Color(.55f, .36f, .16f));
            }
        }

        void Disconnect()
        {
            preview?.Dispose();
            preview = null;
            previewFailed = false;
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
