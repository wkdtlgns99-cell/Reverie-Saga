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
        readonly List<float> historyRowStarts=new List<float>(200);
        float historyContentHeight,historyViewportHeight;
        Vector2 controlsScroll;
        bool dialogueFocused;
        bool saveManagerOpen;
        public bool DialogueFocused { get { return dialogueFocused; } }
        public bool SaveManagerOpen { get { return saveManagerOpen; } }
        public bool GameplayInputEnabled { get { return !dialogueFocused&&!saveManagerOpen&&!Busy&&failure==""; } }
#if UNITY_EDITOR || DEVELOPMENT_BUILD
        internal bool IsolatePhysicalInputForVerification;
        public Rect ControlsViewport { get; private set; }
        public Rect HistoryViewport { get; private set; }
        public float ControlsContentHeight { get; private set; }
        public float ControlsScrollForVerification {
            get { return controlsScroll.y; }
            set { controlsScroll.y=value; }
        }
#endif
        int selected;
        int slotIndex;
        static readonly string[] SlotLabels={"01","02","03","04","05","06","07","08"};
        int waitIndex;
        static readonly int[] WaitSeconds={1,4,8,16};
        static readonly string[] WaitLabels={"1초","4초","8초","16초"};
        Font koreanFont;
        string root, working;
        string scenario = "legacy";
        string questCatalog="",questSha256="";
        bool npcMemory;
        bool npcWork;
        bool npcCycle;
        bool npcAid;
        bool npcReadyPatrol;
        public bool NpcReadyPatrolEnabled { get { return npcReadyPatrol; } }
        bool npcCallPause;
        public bool NpcCallPauseEnabled { get { return npcCallPause; } }
        bool npcQuestPatrol;
        public bool NpcQuestPatrolEnabled { get { return npcQuestPatrol; } }
        bool npcTalkPause;
        public bool NpcTalkPauseEnabled { get { return npcTalkPause; } }
        bool npcPatrol;
        public bool NpcPatrolEnabled { get { return npcPatrol; } }
        bool npcCallAid;
        public bool NpcCallAidEnabled { get { return npcCallAid; } }
        bool npcSupplyAid;
        public bool NpcSupplyAidEnabled { get { return npcSupplyAid; } }
        public bool NpcAidEnabled { get { return npcAid; } }
        public bool NpcCycleEnabled { get { return npcCycle; } }
        public string NpcModeLabel { get { return npcReadyPatrol?"NPC 지원 준비 우선·호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드":npcCallPause?"NPC 호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드":npcQuestPatrol?"NPC 의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드":npcTalkPause?"NPC 대화 대기·순찰·호출 지원·물자·반복 작업·기억 모드":npcPatrol?"NPC 순찰·호출 지원·물자·반복 작업·기억 모드":npcCallAid?"NPC 호출 지원·물자·반복 작업·기억 모드":npcSupplyAid?"NPC 물자 2개 확보 후 지원·반복 작업·기억 모드":npcAid?"NPC 의뢰 지원·반복 작업·기억 모드":npcCycle?"NPC 반복 작업·기억 모드":npcWork?"NPC 비축·기억 모드":npcMemory?"NPC 대화 기억 모드":"기본 모드"; } }
        public bool NpcWorkEnabled { get { return npcWork; } }
        public string QuestCatalog { get { return questCatalog; } }
        public bool NpcMemoryEnabled { get { return npcMemory; } }
        public bool CanInspectMemory { get { return npcMemory&&latest!=null&&!Busy&&failure==""; } }
        public bool CanInspectSlot { get { return latest!=null&&!Busy&&failure==""; } }
        public bool CanSelectSlot { get { return CanInspectSlot; } }
        public string SelectedSlot { get { return "slot"+SlotLabels[slotIndex]; } }
        public bool CanSelectWaitDuration { get { return CanInspectSlot; } }
        public int SelectedWaitSeconds { get { return WaitSeconds[waitIndex]; } }
        public WireResponse Latest { get { return latest; } }
        public bool Busy { get { return connecting || brain == null || brain.Busy; } }
        public bool Connecting { get { return connecting; } }
        public string TransportError { get { return transportError; } }
        public string Failure { get { return failure; } }
#if UNITY_EDITOR || DEVELOPMENT_BUILD
        public bool HasBrainForVerification { get { return brain!=null; } }
        public bool GateOpenForVerification { get { return gate!=null&&!gate.activeSelf; } }
        public Vector3 NpcPositionForVerification { get { return npc.transform.position; } }
#endif

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
                string workSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_WORK");
                if(!String.IsNullOrEmpty(workSelection)&&workSelection!="0"&&workSelection!="1")
                    throw new IOException("NPC_WORK_SELECTION");
                npcWork=workSelection=="1";
                string cycleSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_CYCLE");
                if(!String.IsNullOrEmpty(cycleSelection)&&cycleSelection!="0"&&cycleSelection!="1")
                    throw new IOException("NPC_CYCLE_SELECTION");
                npcCycle=cycleSelection=="1";
                string aidSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_AID");
                if(!String.IsNullOrEmpty(aidSelection)&&aidSelection!="0"&&aidSelection!="1")
                    throw new IOException("NPC_AID_SELECTION");
                npcAid=aidSelection=="1";
                string supplyAidSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_SUPPLY_AID");
                if(!String.IsNullOrEmpty(supplyAidSelection)&&supplyAidSelection!="0"&&supplyAidSelection!="1")
                    throw new IOException("NPC_SUPPLY_AID_SELECTION");
                npcSupplyAid=supplyAidSelection=="1";
                string callAidSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_CALL_AID");
                if(!String.IsNullOrEmpty(callAidSelection)&&callAidSelection!="0"&&callAidSelection!="1")
                    throw new IOException("NPC_CALL_AID_SELECTION");
                npcCallAid=callAidSelection=="1";
                string patrolSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_PATROL");
                if(!String.IsNullOrEmpty(patrolSelection)&&patrolSelection!="0"&&patrolSelection!="1")
                    throw new IOException("NPC_PATROL_SELECTION");
                npcPatrol=patrolSelection=="1";
                string talkPauseSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_TALK_PAUSE");
                if(!String.IsNullOrEmpty(talkPauseSelection)&&talkPauseSelection!="0"&&talkPauseSelection!="1")
                    throw new IOException("NPC_TALK_PAUSE_SELECTION");
                npcTalkPause=talkPauseSelection=="1";
                string questPatrolSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_QUEST_PATROL");
                if(!String.IsNullOrEmpty(questPatrolSelection)&&questPatrolSelection!="0"&&questPatrolSelection!="1")
                    throw new IOException("NPC_QUEST_PATROL_SELECTION");
                npcQuestPatrol=questPatrolSelection=="1";
                string callPauseSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_CALL_PAUSE");
                if(!String.IsNullOrEmpty(callPauseSelection)&&callPauseSelection!="0"&&callPauseSelection!="1")
                    throw new IOException("NPC_CALL_PAUSE_SELECTION");
                npcCallPause=callPauseSelection=="1";
                string readyPatrolSelection=Environment.GetEnvironmentVariable("REVERIE_UNITY_NPC_READY_PATROL");
                if(!String.IsNullOrEmpty(readyPatrolSelection)&&readyPatrolSelection!="0"&&readyPatrolSelection!="1")
                    throw new IOException("NPC_READY_PATROL_SELECTION");
                npcReadyPatrol=readyPatrolSelection=="1";
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
                scenario=BrainConnection.SelectScenario(scenario);
                if(npcCycle&&(!npcMemory||npcWork))throw new IOException("NPC_CYCLE_CONTENT");
                if(npcAid&&!npcCycle)throw new IOException("NPC_AID_CONTENT");
                if(npcSupplyAid&&!npcAid)throw new IOException("NPC_SUPPLY_AID_CONTENT");
                if(npcCallAid&&!npcSupplyAid)throw new IOException("NPC_CALL_AID_CONTENT");
                if(npcPatrol&&!npcCallAid)throw new IOException("NPC_PATROL_CONTENT");
                if(npcTalkPause&&!npcPatrol)throw new IOException("NPC_TALK_PAUSE_CONTENT");
                if(npcQuestPatrol&&!npcTalkPause)throw new IOException("NPC_QUEST_PATROL_CONTENT");
                if(npcCallPause&&!npcQuestPatrol)throw new IOException("NPC_CALL_PAUSE_CONTENT");
                if(npcReadyPatrol&&!npcCallPause)throw new IOException("NPC_READY_PATROL_CONTENT");
                if(npcWork&&!npcMemory)throw new IOException("NPC_WORK_CONTENT");
                if(npcMemory&&(scenario!="harbor"||String.IsNullOrEmpty(questCatalog)||
                    questSha256.Length!=64||!System.Text.RegularExpressions.Regex.IsMatch(questSha256,"^[0-9a-f]{64}$")))
                    throw new IOException("NPC_MEMORY_CONTENT");
                working = Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING");
                if (String.IsNullOrEmpty(working)) working=(scenario=="legacy"||scenario==WireScenarios.Legacy) ?
                    Path.Combine(root,"tmp","unity-play","game.sqlite") :
                    Path.Combine(root,"tmp","unity-play",scenario,"game.sqlite");
                if(!String.IsNullOrEmpty(questCatalog)&&String.IsNullOrEmpty(
                    Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING")))
                    working=npcMemory?Path.Combine(root,"tmp","unity-play",npcReadyPatrol?"harbor-ready-patrol":npcCallPause?"harbor-call-pause":npcQuestPatrol?"harbor-quest-patrol":npcTalkPause?"harbor-talk-patrol":npcPatrol?"harbor-call-patrol":npcCallAid?"harbor-call-aid":npcSupplyAid?"harbor-cycle-supply-aid":npcAid?"harbor-cycle-aid":npcCycle?"harbor-cycle":npcWork?"harbor-work":"harbor-memory",questSha256,"game.sqlite"):
                        Path.Combine(root,"tmp","unity-play","harbor-quest","game.sqlite");
                Directory.CreateDirectory(Path.GetDirectoryName(working));
                Connect();
            } catch(Exception e) { Fail(e); }
        }

        void Update()
        {
#if UNITY_EDITOR || DEVELOPMENT_BUILD
            bool physicalInput=!IsolatePhysicalInputForVerification;
#else
            const bool physicalInput=true;
#endif
            bool focusedAtInput=dialogueFocused||saveManagerOpen;
            if(physicalInput&&focusedAtInput&&Input.GetKeyDown(KeyCode.Escape)) {
                if(saveManagerOpen)SetSaveManager(false);else SetDialogueFocus(false);
            }
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
                    AppendHistory(reply.update.messages,reply.update.reset_log);
                } else if(error!=null) throw new IOException(error);
                if(focusedAtInput||!physicalInput)return;
                if (GameplayInputEnabled) {
                    if(Input.GetKeyDown(KeyCode.W)||Input.GetKeyDown(KeyCode.UpArrow)) Send("up");
                    else if(Input.GetKeyDown(KeyCode.S)||Input.GetKeyDown(KeyCode.DownArrow)) Send("down");
                    else if(Input.GetKeyDown(KeyCode.A)||Input.GetKeyDown(KeyCode.LeftArrow)) Send("left");
                    else if(Input.GetKeyDown(KeyCode.D)||Input.GetKeyDown(KeyCode.RightArrow)) Send("right");
                }
            } catch(Exception e) { Fail(e); }
        }

        void AppendHistory(string[] incoming,bool reset)
        {
            if(reset) {
                messages.Clear();historyRowStarts.Clear();historyContentHeight=0;
                ShowLatestHistory();
            }
            if(incoming.Length==0)return;
            bool follow=messages.Count==0||scroll.y+historyViewportHeight>=historyContentHeight-2;
            int discarded=Math.Max(0,messages.Count+incoming.Length-200);
            if(!follow&&discarded>0) {
                float removed=discarded<historyRowStarts.Count?
                    historyRowStarts[discarded]-historyRowStarts[0]:scroll.y;
                scroll.y=Mathf.Max(0,scroll.y-removed);
            }
            messages.AddRange(incoming);
            if(discarded>0)messages.RemoveRange(0,discarded);
            historyRowStarts.Clear();
            if(follow)ShowLatestHistory();
        }

        public void ShowLatestHistory() {scroll.y=float.MaxValue;}

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
            try { brain.Send(intent,SelectedSlot,SelectedWaitSeconds); } catch(Exception e) { Fail(e); }
        }

        public bool SelectSlot(int index)
        {
            if(index<0||index>=SlotLabels.Length)throw new ArgumentOutOfRangeException(nameof(index));
            if(!CanSelectSlot)return false;
            slotIndex=index;return true;
        }

        public bool SelectWaitDuration(int index)
        {
            if(index<0||index>=WaitSeconds.Length)throw new ArgumentOutOfRangeException(nameof(index));
            if(!CanSelectWaitDuration)return false;
            waitIndex=index;return true;
        }

        public void InspectMemory() { if(CanInspectMemory)Send("memory"); }
        public void InspectRecentMemory() { if(CanInspectMemory)Send("memory_recent"); }
        public void InspectActivity() { if(CanInspectMemory)Send("activity"); }
        public void InspectSlot() { if(CanInspectSlot)Send("slot_inspect"); }
        public void InspectPreviousSlot() { if(CanInspectSlot)Send("slot_previous_inspect"); }
        public void LoadPreviousSlot() { if(CanInspectSlot)Send("load_previous"); }

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
                brain=new BrainConnection(root,working,scenario,questCatalog,questSha256,npcMemory,npcWork,npcCycle,npcAid,npcSupplyAid,npcCallAid,npcPatrol,npcTalkPause,npcQuestPatrol,npcCallPause,npcReadyPatrol);
                failure="";transportError="";
            } catch(Exception e) {Fail(e);}
            finally {connecting=false;}
        }

        public void Reconnect() { Connect(); }

        public void SetDialogueFocus(bool enabled)
        {
            if(dialogueFocused==enabled)return;
            dialogueFocused=enabled;
            if(enabled)saveManagerOpen=false;
            ShowLatestHistory();
        }
        public void SetSaveManager(bool enabled)
        {
            if(saveManagerOpen==enabled)return;
            saveManagerOpen=enabled;
            if(enabled)dialogueFocused=false;
            controlsScroll=Vector2.zero;
        }
#if UNITY_EDITOR || DEVELOPMENT_BUILD
        public int BrainProcessId { get { return brain.ProcessId; } }
        public void SendMalformedForVerification() {brain.SendMalformedForVerification();}
        public void ApplyForVerification(WireView view) {Apply(view);}
        public string HistoryForVerification { get { return String.Join("\n",messages); } }
        public float HistoryScrollForVerification { get { return scroll.y; } set {scroll.y=value;} }
        public int HistoryCountForVerification { get { return messages.Count; } }
        public float HistoryContentHeightForVerification { get { return historyContentHeight; } }
        int HistoryRowForVerification {
            get {
                int index=0;
                while(index+1<historyRowStarts.Count&&historyRowStarts[index+1]<=scroll.y)index++;
                return index;
            }
        }
        public string HistoryTopForVerification { get {return messages.Count==0?"":messages[HistoryRowForVerification];} }
        public float HistoryRowOffsetForVerification {
            get {return historyRowStarts.Count==0?0:scroll.y-historyRowStarts[HistoryRowForVerification];}
        }
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
#if UNITY_EDITOR || DEVELOPMENT_BUILD
            if(IsolatePhysicalInputForVerification&&(Event.current.isKey||Event.current.isMouse||
                Event.current.type==EventType.ScrollWheel))Event.current.Use();
#endif
            if(koreanFont==null)koreanFont=Font.CreateDynamicFontFromOSFont("Malgun Gothic",16);
            GUI.skin.font=koreanFont;
            float width=Mathf.Max(0,Mathf.Min(380,Screen.width-24));
            float height=Mathf.Max(0,Screen.height-24);
            var panel=new Rect(12,12,width,height);
            Color previousColor=GUI.color;
            try {
                GUI.color=new Color(.04f,.05f,.07f,1f);
                GUI.DrawTexture(panel,Texture2D.whiteTexture);
            } finally {GUI.color=previousColor;}
            GUI.Box(panel,GUIContent.none);
            float innerWidth=Mathf.Max(0,width-12);
            GUI.Label(new Rect(18,18,innerWidth,24),"Reverie Saga — 플레이테스트");
            // This button stays outside the scrollable controls and their busy gates.
            float toggleWidth=Mathf.Max(0,(innerWidth-6)*.5f);
            if(GUI.Button(new Rect(18,48,toggleWidth,24),dialogueFocused?"조작 화면으로":"대화 크게 보기"))
                SetDialogueFocus(!dialogueFocused);
            if(GUI.Button(new Rect(24+toggleWidth,48,toggleWidth,24),saveManagerOpen?"저장 관리 닫기":"저장 관리"))
                SetSaveManager(!saveManagerOpen);
            float available=Mathf.Max(0,height-102);
            bool focusError=dialogueFocused&&(failure!=""||transportError!="");
            float controlsHeight=dialogueFocused?(focusError?Mathf.Min(24,available):0):Mathf.Floor(available*.6f);
            var controls=new Rect(18,78,innerWidth,controlsHeight);
            var history=new Rect(18,controls.yMax+30,innerWidth,available-controlsHeight);
            historyViewportHeight=history.height;
#if UNITY_EDITOR || DEVELOPMENT_BUILD
            ControlsViewport=controls;HistoryViewport=history;
#endif
            if(!dialogueFocused) {
                GUILayout.BeginArea(controls);
                controlsScroll=GUILayout.BeginScrollView(controlsScroll,false,false);
                if(saveManagerOpen)DrawSaveManager();else DrawControls(innerWidth);
#if UNITY_EDITOR || DEVELOPMENT_BUILD
                var end=GUILayoutUtility.GetRect(0,0);
                if(Event.current.type==EventType.Repaint)ControlsContentHeight=end.yMax;
#endif
                GUILayout.EndScrollView();GUILayout.EndArea();
            } else if(focusError) {
                GUI.Label(controls,failure!=""?"연결 오류: "+failure:"요청 거부: "+transportError);
            }
            float latestWidth=Mathf.Min(92,innerWidth);
            GUI.Label(new Rect(18,controls.yMax+6,Mathf.Max(0,innerWidth-latestWidth-6),24),"행동·대화 기록");
            GUI.enabled=true;
            if(GUI.Button(new Rect(18+innerWidth-latestWidth,controls.yMax+6,latestWidth,24),"최신 기록"))
                ShowLatestHistory();
            GUILayout.BeginArea(history);
            scroll=GUILayout.BeginScrollView(scroll,false,false);
            bool measure=Event.current.type==EventType.Repaint;
            if(measure)historyRowStarts.Clear();
            foreach(string message in messages) {
                GUILayout.Label(message);
                if(measure)historyRowStarts.Add(GUILayoutUtility.GetLastRect().y);
            }
            var historyEnd=GUILayoutUtility.GetRect(0,0);
            if(measure)historyContentHeight=historyEnd.yMax;
            GUILayout.EndScrollView();GUILayout.EndArea();
        }

        void DrawSaveManager()
        {
            GUILayout.Label("저장 관리 · "+SelectedSlot);
            if(latest!=null)GUILayout.Label("현재 진행 "+latest.update.view.tick+"초");
            if(transportError!="")GUILayout.Label("요청 거부: "+transportError);
            if(failure!="") {
                GUILayout.Label("연결 오류: "+failure);
                if(GUILayout.Button("다시 연결"))Reconnect();
            }
            GUI.enabled=CanSelectSlot;
            int nextSlot=GUILayout.SelectionGrid(slotIndex,SlotLabels,4);
            if(nextSlot!=slotIndex)SelectSlot(nextSlot);
            GUI.enabled=CanInspectSlot;
            GUILayout.BeginHorizontal();
            if(GUILayout.Button("현재 저장 정보"))InspectSlot();
            if(GUILayout.Button("이전 저장 정보"))InspectPreviousSlot();
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            if(GUILayout.Button("현재 진행 저장"))Send("save");
            if(GUILayout.Button("현재 저장 불러오기"))Send("load");
            GUILayout.EndHorizontal();
            if(GUILayout.Button("이전 저장 불러오기"))LoadPreviousSlot();
            GUI.enabled=true;
            GUILayout.Label("불러오기는 원본을 바꾸지 않고 별도 진행에서 이어집니다.");
            GUILayout.Label("덮어쓰기 전 저장 하나를 이전 저장으로 보관합니다.");
        }

        void DrawControls(float width)
        {
            if(latest!=null)GUILayout.Label(latest.update.scenario_name+" · "+NpcModeLabel);
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
                GUI.enabled=CanInspectMemory;
                if(GUILayout.Button("NPC 활동 기록")) InspectActivity();
                GUI.enabled=!Busy&&failure=="";
            }
            GUI.enabled=CanSelectWaitDuration;
            GUILayout.Label("대기 시간 · "+SelectedWaitSeconds.ToString(CultureInfo.InvariantCulture)+"초");
            int nextWait=GUILayout.SelectionGrid(waitIndex,WaitLabels,4);
            if(nextWait!=waitIndex)SelectWaitDuration(nextWait);
            GUI.enabled=!Busy&&failure=="";
            string[] actions={"open","close","attack","rest","wait","bell"};
            int columns=width<330?2:3;
            for(int i=0;i<actions.Length;i++) {
                if(i%columns==0)GUILayout.BeginHorizontal();
                string intent=actions[i];
                if(GUILayout.Button(Label(intent))) Send(intent);
                if(i%columns==columns-1||i==actions.Length-1)GUILayout.EndHorizontal();
            }
            GUI.enabled=CanSelectSlot;
            GUILayout.Label("저장 슬롯 · "+SelectedSlot);
            int nextSlot=GUILayout.SelectionGrid(slotIndex,SlotLabels,4);
            if(nextSlot!=slotIndex)SelectSlot(nextSlot);
            GUI.enabled=CanInspectSlot;
            if(GUILayout.Button(SelectedSlot+" 저장 정보")) InspectSlot();
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
