using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;

namespace ReverieSaga
{
    public sealed class PlayRoom : MonoBehaviour
    {
        BrainConnection brain;
        WireResponse latest;
        GameObject actor, enemy, gate, npc;
        readonly List<Material> materials = new List<Material>();
        readonly List<string> messages = new List<string>();
        string failure = "";
        bool boardCreated, connecting, destroyed;
        int boardWidth,boardHeight;
        string boardWalls;
        string transportError="";
        Vector2 scroll;
        int selected;
        Font koreanFont;
        string root, working;
        string scenario = "legacy";
        string questCatalog="",questSha256="";
        bool npcMemory;
        public string QuestCatalog { get { return questCatalog; } }
        public bool NpcMemoryEnabled { get { return npcMemory; } }
        public bool CanInspectMemory { get { return npcMemory&&latest!=null&&!Busy&&failure==""; } }
        public bool CanInspectSlot { get { return latest!=null&&!Busy&&failure==""; } }
        public WireResponse Latest { get { return latest; } }
        public bool Busy { get { return connecting || brain == null || brain.Busy; } }
        public bool Connecting { get { return connecting; } }
        public string TransportError { get { return transportError; } }
        public string Failure { get { return failure; } }

        public static int Number(string value)
        {
            if (!int.TryParse(value, NumberStyles.None, CultureInfo.InvariantCulture, out int n))
                throw new InvalidDataException("Invalid public integer");
            return n;
        }

        void Start()
        {
            Application.runInBackground=true;
            try {
                root = Path.GetFullPath(Path.Combine(Application.dataPath,"..","..",".."));
                string scenarioSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_SCENARIO");
                string memorySelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_MEMORY");
                questCatalog=Environment.GetEnvironmentVariable("REVERIE_UNITY_QUEST_CATALOG")??"";
                questSha256=Environment.GetEnvironmentVariable("REVERIE_UNITY_QUEST_SHA256")??"";
                bool approvedPreset=String.IsNullOrEmpty(scenarioSelection)&&
                    String.IsNullOrEmpty(questCatalog)&&String.IsNullOrEmpty(questSha256)&&
                    String.IsNullOrEmpty(memorySelection);
                if(approvedPreset) {
                    scenario="harbor";npcMemory=true;
                    questCatalog=Path.Combine(root,"content","dialogue","harbor-memory-v1.json");
                    questSha256=File.ReadAllText(Path.Combine(root,"content","dialogue",
                        "harbor-memory-v1.sha256")).Trim();
                } else {
                    scenario=String.IsNullOrEmpty(scenarioSelection)?"legacy":scenarioSelection;
                    if(!String.IsNullOrEmpty(memorySelection)&&memorySelection!="0"&&memorySelection!="1")
                        throw new IOException("NPC_MEMORY_SELECTION");
                    npcMemory=memorySelection=="1";
                }
                if(scenario!="legacy"&&scenario!="harbor"&&scenario!="grove")
                    throw new IOException("SCENARIO_SELECTION");
                if(npcMemory&&(scenario!="harbor"||String.IsNullOrEmpty(questCatalog)||
                    questSha256.Length!=64||!System.Text.RegularExpressions.Regex.IsMatch(questSha256,"^[0-9a-f]{64}$")))
                    throw new IOException("NPC_MEMORY_CONTENT");
                working = Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING");
                if (String.IsNullOrEmpty(working)) working=scenario=="legacy" ?
                    Path.Combine(root,"tmp","unity-play","game.sqlite") :
                    Path.Combine(root,"tmp","unity-play",scenario,"game.sqlite");
                if(!String.IsNullOrEmpty(questCatalog)&&String.IsNullOrEmpty(
                    Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING")))
                    working=npcMemory?Path.Combine(root,"tmp","unity-play","harbor-memory",questSha256,"game.sqlite"):
                        Path.Combine(root,"tmp","unity-play","harbor-quest","game.sqlite");
                Directory.CreateDirectory(Path.GetDirectoryName(working));
                Connect();
            } catch(Exception e) { Fail(e); }
        }

        void Update()
        {
            if (brain == null || connecting || failure != "") return;
            try {
                if (brain.Poll(out WireResponse reply, out string error)) {
                    if (!String.IsNullOrEmpty(reply.error)) {
                        transportError=reply.error;
                        Debug.LogWarning("Brain request rejected: "+transportError);
                        return;
                    }
                    transportError="";
                    if (!reply.has_view || reply.update.view == null)
                        throw new IOException(reply.update.status+": "+String.Join("\n",reply.update.messages));
                    if(!String.IsNullOrEmpty(questCatalog)) {
                        int stage=Number(reply.update.quest_stage),reward=Number(reply.update.quest_reward);
                        if(stage>3||reward!=(stage==3?1:0)||reply.update.quest_id!="quest:harbor-sentinel"||
                           reply.update.dialogue_sha256!=questSha256)
                            throw new IOException("QUEST_PROJECTION_INVALID");
                    } else if(reply.update.quest_stage!="-1"||reply.update.quest_reward!="0")
                        throw new IOException("QUEST_PROJECTION_INVALID");
                    latest=reply;
                    working=reply.update.working_path;
                    Apply(reply.update.view);
                    if (reply.update.reset_log) messages.Clear();
                    messages.AddRange(reply.update.messages);
                    if(messages.Count>200) messages.RemoveRange(0,messages.Count-200);
                    if(reply.update.messages.Length>0) scroll.y=float.MaxValue;
                } else if(error!=null) throw new IOException(error);
                if (!Busy) {
                    if(Input.GetKeyDown(KeyCode.W)||Input.GetKeyDown(KeyCode.UpArrow)) Send("up");
                    else if(Input.GetKeyDown(KeyCode.S)||Input.GetKeyDown(KeyCode.DownArrow)) Send("down");
                    else if(Input.GetKeyDown(KeyCode.A)||Input.GetKeyDown(KeyCode.LeftArrow)) Send("left");
                    else if(Input.GetKeyDown(KeyCode.D)||Input.GetKeyDown(KeyCode.RightArrow)) Send("right");
                }
            } catch(Exception e) { Fail(e); }
        }

        Vector3 Position(int cell, int width, float y=0.5f)
        { return new Vector3(cell%width,y,-(cell/width)); }

        GameObject Shape(string label,PrimitiveType type,Color color)
        {
            var item=GameObject.CreatePrimitive(type); item.name=label;
            var prototype=Resources.Load<Material>("Placeholder");
            if(prototype==null) throw new IOException("Placeholder material missing");
            var material=new Material(prototype); material.color=color;
            materials.Add(material);
            item.GetComponent<Renderer>().material=material;
            return item;
        }

        void Apply(WireView view)
        {
            int width=Number(view.width),height=Number(view.height);
            if(width!=3||height!=3) throw new IOException("PROTOTYPE_BOARD_BOUNDS");
            string walls=String.Join(",",view.walls);
            if(boardCreated&&(width!=boardWidth||height!=boardHeight||walls!=boardWalls))
                throw new IOException("PROTOTYPE_BOARD_CHANGED");
            int size=checked(width*height);
            foreach(string cell in new [] {view.actor_cell,view.enemy_cell,view.gate_cell,view.npc_cell})
                if(Number(cell)>=size) throw new IOException("Entity cell bounds");
            if(!boardCreated) {
                var cameraObject=new GameObject("Camera");
                var camera=cameraObject.AddComponent<Camera>();
                camera.orthographic=true; camera.orthographicSize=4;
                camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.08f,.10f,.15f);
                camera.transform.position=new Vector3((width-1)/2f,6,-(height-1)/2f-3);
                camera.transform.LookAt(new Vector3((width-1)/2f,0,-(height-1)/2f));
                for(int i=0;i<size;i++) {
                    var tile=Shape("Tile "+i,PrimitiveType.Cube,new Color(.32f,.38f,.45f));
                    tile.transform.position=Position(i,width,-.08f);
                    tile.transform.localScale=new Vector3(.96f,.12f,.96f);
                }
                foreach(string c in view.walls) {
                    int cell=Number(c);if(cell>=size)throw new IOException("Wall bounds");
                    var wall=Shape("Wall",PrimitiveType.Cube,new Color(.18f,.23f,.3f));
                    wall.transform.position=Position(cell,width);
                }
                actor=Shape("Player",PrimitiveType.Capsule,new Color(.2f,.8f,.9f));
                enemy=Shape("Copper catfish placeholder",PrimitiveType.Sphere,new Color(.8f,.4f,.2f));
                gate=Shape("Door",PrimitiveType.Cube,new Color(.6f,.4f,.2f));
                npc=Shape("NPC",PrimitiveType.Capsule,new Color(.7f,.8f,.3f));
                actor.transform.localScale=enemy.transform.localScale=npc.transform.localScale=Vector3.one*.45f;
                gate.transform.localScale=new Vector3(.8f,.8f,.18f);
                boardWidth=width;boardHeight=height;boardWalls=walls;boardCreated=true;
            }
            actor.transform.position=Position(Number(view.actor_cell),width);
            enemy.transform.position=Position(Number(view.enemy_cell),width);
            npc.transform.position=Position(Number(view.npc_cell),width);
            gate.transform.position=Position(Number(view.gate_cell),width);
            gate.SetActive(!view.gate_open); enemy.SetActive(Number(view.enemy_hp)>0);
        }

        public void Send(string intent)
        {
            try { brain.Send(intent); } catch(Exception e) { Fail(e); }
        }

        public void InspectMemory() { if(CanInspectMemory)Send("memory"); }
        public void InspectRecentMemory() { if(CanInspectMemory)Send("memory_recent"); }
        public void InspectSlot() { if(CanInspectSlot)Send("slot_inspect"); }

        void Connect()
        {
            if(connecting||destroyed)return;
            connecting=true;StartCoroutine(ConnectRoutine());
        }

        IEnumerator ConnectRoutine()
        {
            if(brain!=null) {
                var stopped=brain.StopAsync();
                while(!stopped.IsCompleted)yield return null;
                if(stopped.IsFaulted) {connecting=false;Fail(stopped.Exception);yield break;}
                brain=null;
            }
            if(destroyed)yield break;
            try {
                brain=new BrainConnection(root,working,scenario,questCatalog,questSha256,npcMemory);
                failure="";transportError="";
            } catch(Exception e) {Fail(e);}
            finally {connecting=false;}
        }

        public void Reconnect() { Connect(); }
#if UNITY_EDITOR || DEVELOPMENT_BUILD
        public int BrainProcessId { get { return brain.ProcessId; } }
        public void SendMalformedForVerification() {brain.SendMalformedForVerification();}
        public void ApplyForVerification(WireView view) {Apply(view);}
        public string HistoryForVerification { get { return String.Join("\n",messages); } }
#endif
        void Fail(Exception error) { failure=error.Message;Debug.LogException(error); }

        static string Label(string intent)
        {
            switch(intent) {
                case "up": return "위"; case "down": return "아래";
                case "left": return "왼쪽"; case "right": return "오른쪽";
                case "open": return "문 열기"; case "close": return "문 닫기";
                case "attack": return "공격"; case "rest": return "휴식";
                case "wait": return "대기"; case "bell": return "NPC 호출";
                case "talk": return "NPC 대화·보고";
                case "save": return "저장"; case "load": return "불러오기";
                case "retry": return "재전송";
                case "recover": return "복구";
                default: throw new ArgumentException("Unknown UI intent");
            }
        }

        void OnGUI()
        {
            if(koreanFont==null)koreanFont=Font.CreateDynamicFontFromOSFont("Malgun Gothic",16);
            GUI.skin.font=koreanFont;
            GUILayout.BeginArea(new Rect(12,12,380,Screen.height-24),GUI.skin.box);
            GUILayout.Label("Reverie Saga — 플레이테스트");
            if(latest!=null)GUILayout.Label(latest.update.scenario_name);
            if(transportError!="")GUILayout.Label("요청 거부: "+transportError);
            if(failure!="") {
                GUILayout.Label("연결 오류: "+failure);
                if(GUILayout.Button("다시 연결")) Reconnect();
            }
            if(latest!=null) {
                var v=latest.update.view;
                GUILayout.Label("체력 "+v.actor_hp+" / 적 "+v.enemy_hp+" / 기력 "+v.stamina);
                GUILayout.Label("시간 "+v.tick+" / NPC 응답 "+v.npc_replies);
                if(latest.update.quest_stage!="-1") {
                    string[] stages={"미수락","진행 중","보고 가능","완료"};
                    GUILayout.Label("임무 "+stages[Number(latest.update.quest_stage)]+
                                    " / 포구의 호의 "+latest.update.quest_reward);
                }
            }
            GUI.enabled=!Busy&&failure=="";
            GUILayout.BeginHorizontal();
            foreach(string intent in new [] {"up","down","left","right"})
                if(GUILayout.Button(Label(intent))) Send(intent);
            GUILayout.EndHorizontal();
            if(!String.IsNullOrEmpty(questCatalog)&&GUILayout.Button(Label("talk"))) Send("talk");
            if(npcMemory) {
                GUILayout.BeginHorizontal();
                GUI.enabled=CanInspectMemory;
                if(GUILayout.Button("NPC 대화 기억")) InspectMemory();
                GUI.enabled=CanInspectMemory;
                if(GUILayout.Button("최근 대화 기억")) InspectRecentMemory();
                GUILayout.EndHorizontal();
                GUI.enabled=!Busy&&failure=="";
            }
            GUILayout.BeginHorizontal();
            foreach(string intent in new [] {"open","close","attack","rest","wait","bell"})
                if(GUILayout.Button(Label(intent))) Send(intent);
            GUILayout.EndHorizontal();
            GUI.enabled=CanInspectSlot;
            if(GUILayout.Button("slot01 저장 정보")) InspectSlot();
            GUI.enabled=!Busy&&failure=="";
            GUILayout.BeginHorizontal();
            foreach(string intent in new [] {"save","load","retry","recover"})
                if(GUILayout.Button(Label(intent))) Send(intent);
            GUILayout.EndHorizontal();GUI.enabled=true;
            if(latest!=null&&latest.narratives.Length>0) {
                selected=Math.Min(selected,latest.narratives.Length-1);
                if(GUILayout.Button("가져온 설정 보기: "+latest.narratives[selected].name_ko))
                    selected=(selected+1)%latest.narratives.Length;
                GUILayout.Label(latest.narratives[selected].description_ko);
            }
            scroll=GUILayout.BeginScrollView(scroll);
            foreach(string message in messages) GUILayout.Label(message);
            GUILayout.EndScrollView();GUILayout.EndArea();
        }

        void OnDestroy()
        {
            destroyed=true;
            try {
                if(brain!=null) {
                    var stopped=brain.StopAsync();
                    stopped.ContinueWith(task=>Debug.LogException(task.Exception),
                        System.Threading.Tasks.TaskContinuationOptions.OnlyOnFaulted);
                }
            }
            finally {
                foreach(var material in materials)Destroy(material);
                if(koreanFont!=null)Destroy(koreanFont);
            }
        }
    }
}
