#if UNITY_EDITOR || DEVELOPMENT_BUILD
using System;
using System.Collections;
using System.Globalization;
using System.IO;
#if UNITY_EDITOR
using UnityEditor;
#endif
using UnityEngine;
namespace ReverieSaga
{
    public sealed class LiveVerification : MonoBehaviour
    {
#if !UNITY_EDITOR
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void StartVerification()
        {
            if(Environment.GetEnvironmentVariable("REVERIE_UNITY_VERIFY")!="1")return;
            var runner=new GameObject("Native Verification").AddComponent<LiveVerification>();
            runner.StartCoroutine(runner.Run());
        }
#endif
        static void Exit(int code)
        {
#if UNITY_EDITOR
            SessionState.SetInt("Reverie.Verify.ExitCode",code);
            Debug.Log("ENGINE_VERIFY_RESULT code="+code);
            if(Environment.GetEnvironmentVariable("REVERIE_UNITY_VERIFY_EXIT")=="1")
                EditorApplication.Exit(code);
            else {
                SessionState.SetBool("Reverie.Verify.Retained",true);
                Debug.Log("ENGINE_VERIFY_EDITOR_RETAINED code="+code);
                EditorApplication.delayCall+=()=>{EditorApplication.isPlaying=false;};
            }
#else
            Application.Quit(code);
#endif
        }
        PlayRoom room;
        bool failed;
        void OnDestroy()
        {
            if(room!=null)room.IsolatePhysicalInputForVerification=false;
        }
        [Serializable] sealed class QuestTextLine { public string intent;public string text_ko; }
        [Serializable] sealed class QuestTextCandidate { public QuestTextLine[] lines; }
        [Serializable] sealed class QuestTextCatalog { public QuestTextCandidate candidate; }
        string QuestText(string intent)
        {
            string path=room.QuestCatalog;
            if(String.IsNullOrEmpty(path)||new FileInfo(path).Length>16384)
                throw new IOException("QUEST_TEST_CATALOG_INVALID");
            var catalog=JsonUtility.FromJson<QuestTextCatalog>(File.ReadAllText(path));
            if(catalog==null||catalog.candidate==null||catalog.candidate.lines==null||
               catalog.candidate.lines.Length!=4)throw new IOException("QUEST_TEST_CATALOG_INVALID");
            string[] order={"completion","gratitude","offer","reminder"};
            for(int i=0;i<order.Length;i++) {
                var line=catalog.candidate.lines[i];
                if(line==null||line.intent!=order[i]||String.IsNullOrEmpty(line.text_ko))
                    throw new IOException("QUEST_TEST_CATALOG_INVALID");
                if(line.intent==intent)return line.text_ko;
            }
            throw new IOException("QUEST_TEST_INTENT_INVALID");
        }
        IEnumerator Ready()
        {
            float start=Time.realtimeSinceStartup;
            while((room.Connecting||room.Busy)&&(room.Connecting||room.Failure=="")&&Time.realtimeSinceStartup-start<12)yield return null;
            if(room.Busy||room.Failure!="") {
                failed=true;Debug.LogError("Engine verification unavailable: "+room.Failure);
            }
        }
        IEnumerator Intent(string action)
        {
            if(failed)yield break;
            room.Send(action);yield return Ready();
        }
        void Check(bool condition,string label)
        {
            if(!condition) {failed=true;Debug.LogError("VERIFY_FAIL "+label);}
            else Debug.Log("VERIFY_PASS "+label);
        }

        static string FileHash(string path)
        {
            using(var hash=System.Security.Cryptography.SHA256.Create())
            using(var stream=new FileStream(path,FileMode.Open,FileAccess.Read,
                                           FileShare.ReadWrite|FileShare.Delete))
                return Convert.ToBase64String(hash.ComputeHash(stream));
        }

        [Serializable] sealed class LayoutEvidence {
            public int screenWidth,screenHeight;
            public Rect controls,history;
            public float contentHeight,bottomScroll;
        }

        IEnumerator InspectLayout(string output)
        {
            if(Application.isBatchMode||failed)yield break;
            string state=JsonUtility.ToJson(room.Latest),bytes=FileHash(room.Latest.update.working_path);
            room.ControlsScrollForVerification=0;
            yield return new WaitForEndOfFrame();
            var controls=room.ControlsViewport;var history=room.HistoryViewport;
            Check(controls.width>0&&controls.height>0&&history.height>=50&&
                  controls.xMin>=0&&controls.xMax<=Screen.width&&history.yMax<=Screen.height&&
                  controls.yMax+24<=history.yMin,"layout_visible_separate_regions");
            ScreenCapture.CaptureScreenshot(Path.Combine(output,"controls-top.png"));
            yield return new WaitForSecondsRealtime(.2f);
            room.ControlsScrollForVerification=float.MaxValue;
            yield return null;yield return new WaitForEndOfFrame();
            float bottom=room.ControlsScrollForVerification;
            Check(room.ControlsContentHeight<=controls.height||
                  bottom>0&&bottom+controls.height>=room.ControlsContentHeight-24,
                  "layout_controls_bottom_reachable");
            ScreenCapture.CaptureScreenshot(Path.Combine(output,"controls-bottom.png"));
            yield return new WaitForSecondsRealtime(.2f);
            room.ControlsScrollForVerification=bottom*.5f;
            yield return null;yield return new WaitForEndOfFrame();
            ScreenCapture.CaptureScreenshot(Path.Combine(output,"controls-middle.png"));
            yield return new WaitForSecondsRealtime(.2f);
            room.ControlsScrollForVerification=bottom;
            yield return null;yield return new WaitForEndOfFrame();
            Check(JsonUtility.ToJson(room.Latest)==state&&FileHash(room.Latest.update.working_path)==bytes,
                  "layout_scroll_preserves_committed_state");
            if(room.NpcMemoryEnabled) {
                yield return InspectMemorySelection("layout_scrolled_memory",1,true);
                yield return new WaitForEndOfFrame();
                Check(Mathf.Abs(room.ControlsScrollForVerification-bottom)<1,
                      "layout_history_does_not_scroll_controls");
            }
            File.WriteAllText(Path.Combine(output,"layout.json"),JsonUtility.ToJson(new LayoutEvidence {
                screenWidth=Screen.width,screenHeight=Screen.height,controls=controls,history=history,
                contentHeight=room.ControlsContentHeight,bottomScroll=bottom
            }));
            Check(File.Exists(Path.Combine(output,"controls-top.png"))&&
                  File.Exists(Path.Combine(output,"controls-bottom.png")),"layout_captures");
            room.ControlsScrollForVerification=0;
            yield return new WaitForEndOfFrame();
        }

        IEnumerator InspectSlot(string label,string tick,int memoryCount=1)
        {
            if(failed)yield break;
            var before=room.Latest.update;
            string view=JsonUtility.ToJson(before.view),working=FileHash(before.working_path);
            string slot=Path.Combine(Path.GetDirectoryName(before.working_path),"slots",room.SelectedSlot+".sqlite");
            string slotHash=File.Exists(slot)?FileHash(slot):null;
            Check(room.CanInspectSlot,label+"_enabled");
            room.InspectSlot();
            Check(room.Busy&&!room.CanInspectSlot&&!room.CanInspectMemory,label+"_busy_gate");
            room.InspectSlot();room.InspectMemory();room.InspectRecentMemory();
            yield return Ready();if(failed)yield break;
            var after=room.Latest.update;
            Check(after.status==(tick==null?"SAVE_NOT_FOUND":"SLOT_INSPECTED"),label+"_status");
            Check(JsonUtility.ToJson(after.view)==view&&after.quest_stage==before.quest_stage&&
                  after.quest_reward==before.quest_reward&&after.attachment_id==before.attachment_id&&
                  after.working_path==before.working_path&&!after.reset_log&&
                  FileHash(after.working_path)==working&&
                  (slotHash==null?!File.Exists(slot):FileHash(slot)==slotHash),label+"_read_only");
            if(tick!=null) {
                string text=String.Join("\n",after.messages);
                bool expected=text.Contains(room.SelectedSlot+" 저장 정보 · "+tick+"초");
                if(room.NpcMemoryEnabled)expected=expected&&text.Contains("저장된 NPC 대화 기억: "+memoryCount+"개")&&
                    text.Contains(memoryCount==2?"플레이어의 완료 보고를 받은 기억이 있습니다.":
                        "완료 보고를 받은 기억은 없습니다.");
                Check(expected&&room.HistoryForVerification.Contains(after.messages[0]),label+"_display");
            }
        }

        IEnumerator InspectComparedSlot(string label,string tick,int shared,int currentOnly,int savedOnly,bool capture=false)
        {
            yield return InspectSlot(label,tick,shared+savedOnly);
            if(failed)yield break;
            var after=room.Latest.update;
            string heading="NPC 기억 비교 · 현재 "+after.view.tick+"초 / 선택 저장 "+tick+"초";
            string counts="공통 "+shared+"개 · 현재에만 "+currentOnly+"개 · 저장에만 "+savedOnly+"개";
            string body=String.Join("\n",after.messages);
            Check(Array.IndexOf(after.messages,heading)>=0&&Array.IndexOf(after.messages,counts)>=0&&
                body.Contains("NPC가 기억을 잊었다는 뜻은 아닙니다")&&
                room.HistoryForVerification.Contains(counts),label+"_comparison");
            if(currentOnly>0)Check(body.Contains("현재에만 있는 기억")&&
                body.Contains("처치를 직접 본 기억은 아닙니다"),label+"_report_not_eyewitness");
            if(capture) {
                bool focused=room.DialogueFocused;
                room.SetDialogueFocus(true);
                yield return CaptureActivity(label);
                room.SetDialogueFocus(focused);
            }
        }

        IEnumerator SelectSlots(string output)
        {
            if(failed)yield break;
            var before=room.Latest.update;
            string view=JsonUtility.ToJson(before.view),state=JsonUtility.ToJson(room.Latest);
            string workingHash=FileHash(before.working_path);
            string slotRoot=Path.Combine(Path.GetDirectoryName(before.working_path),"slots");
            string originalSlot=Path.Combine(slotRoot,"slot01.sqlite"),originalHash=FileHash(originalSlot);
            int tick=PlayRoom.Number(before.view.tick);
            Check(room.SelectedSlot=="slot01"&&room.CanSelectSlot,"slots_default_01");
            foreach(int index in new [] {-1,8}) {
                bool rejected=false;
                try {room.SelectSlot(index);}catch(ArgumentOutOfRangeException){rejected=true;}
                Check(rejected&&room.SelectedSlot=="slot01","slots_invalid_index_"+index);
            }
            bool allSelected=true;
            for(int index=0;index<8;index++)
                allSelected=room.SelectSlot(index)&&room.SelectedSlot=="slot0"+(index+1)&&allSelected;
            Check(allSelected&&JsonUtility.ToJson(room.Latest)==state&&
                  FileHash(before.working_path)==workingHash,"slots_selection_local_only");
            room.InspectSlot();
            Check(room.Busy&&!room.CanSelectSlot&&!room.SelectSlot(1)&&room.SelectedSlot=="slot08",
                  "slots_busy_selection_preserves_target");
            yield return Ready();if(failed)yield break;
            Check(room.Latest.update.status=="SAVE_NOT_FOUND"&&
                  JsonUtility.ToJson(room.Latest.update.view)==view,"slots_missing_08_no_fallback");
            yield return Intent("save");
            Check(room.Latest.update.status=="SAVED"&&File.Exists(Path.Combine(slotRoot,"slot08.sqlite")),
                  "slots_save_08");
            Check(room.SelectSlot(1)&&room.SelectedSlot=="slot02","slots_select_02");
            yield return Intent("wait");
            Check(room.Latest.update.status=="COMMITTED"&&PlayRoom.Number(room.Latest.update.view.tick)==tick+1,
                  "slots_distinct_newer_state");
            yield return Intent("save");
            Check(room.Latest.update.status=="SAVED"&&File.Exists(Path.Combine(slotRoot,"slot02.sqlite")),
                  "slots_save_02");
            room.SelectSlot(7);
            yield return InspectSlot("slots_preview_08",tick.ToString(CultureInfo.InvariantCulture),2);
            yield return Intent("load");
            Check(room.Latest.update.status=="LOADED"&&room.Latest.update.reset_log&&
                  JsonUtility.ToJson(room.Latest.update.view)==view&&room.SelectedSlot=="slot08"&&
                  room.Latest.update.working_path!=before.working_path,"slots_load_08_exact");
            int pid=room.BrainProcessId;room.Reconnect();
            Check(!room.CanSelectSlot&&!room.SelectSlot(0)&&room.SelectedSlot=="slot08",
                  "slots_connecting_gate");
            yield return Ready();if(failed)yield break;
            Check(room.BrainProcessId!=pid&&room.SelectedSlot=="slot08"&&
                  JsonUtility.ToJson(room.Latest.update.view)==view,"slots_reconnect_retains_selection");
            room.SelectSlot(1);
            yield return InspectSlot("slots_preview_02",(tick+1).ToString(CultureInfo.InvariantCulture),2);
            Check(FileHash(originalSlot)==originalHash,"slots_original_01_unchanged");
            room.SelectSlot(7);
            File.WriteAllText(Path.Combine(output,"selected-slot.json"),
                "{\"selected_slot\":\""+room.SelectedSlot+"\",\"slot08_tick\":"+tick+
                ",\"slot02_tick\":"+(tick+1)+",\"slot01_sha256_base64\":\""+originalHash+"\"}");
        }

        IEnumerator SelectWait(string output)
        {
            if(failed)yield break;
            var before=room.Latest.update;
            string view=JsonUtility.ToJson(before.view),state=JsonUtility.ToJson(room.Latest);
            string workingHash=FileHash(before.working_path);
            string slotPath=Path.Combine(Path.GetDirectoryName(before.working_path),"slots",room.SelectedSlot+".sqlite");
            string slotHash=FileHash(slotPath);
            int tick=PlayRoom.Number(before.view.tick);
            Check(room.SelectedWaitSeconds==1&&room.CanSelectWaitDuration,"wait_default_1");
            foreach(int index in new [] {-1,4}) {
                bool rejected=false;
                try {room.SelectWaitDuration(index);}catch(ArgumentOutOfRangeException){rejected=true;}
                Check(rejected&&room.SelectedWaitSeconds==1,"wait_invalid_index_"+index);
            }
            bool allSelected=true;int[] expected={1,4,8,16};
            for(int index=0;index<expected.Length;index++)
                allSelected=room.SelectWaitDuration(index)&&room.SelectedWaitSeconds==expected[index]&&allSelected;
            Check(allSelected&&JsonUtility.ToJson(room.Latest)==state&&
                  FileHash(before.working_path)==workingHash,"wait_selection_local_only");
            room.Send("wait");
            Check(room.Busy&&!room.CanSelectWaitDuration&&!room.SelectWaitDuration(0)&&
                  room.SelectedWaitSeconds==16,"wait_busy_selection_preserves_duration");
            yield return Ready();if(failed)yield break;
            Check(room.Latest.update.status=="COMMITTED"&&PlayRoom.Number(room.Latest.update.view.tick)==tick+16,
                  "wait_actual_16_seconds");
            string waited=JsonUtility.ToJson(room.Latest.update.view);
            yield return InspectActivity("wait_self_activity",tick+16);
            room.SelectWaitDuration(1);yield return Intent("retry");
            Check(room.SelectedWaitSeconds==4&&JsonUtility.ToJson(room.Latest.update.view)==waited,
                  "wait_retry_uses_original_command_once");
            room.SelectWaitDuration(3);yield return Intent("load");
            Check(room.Latest.update.status=="LOADED"&&JsonUtility.ToJson(room.Latest.update.view)==view&&
                  room.SelectedWaitSeconds==16,"wait_load_restores_state_retains_choice");
            int pid=room.BrainProcessId;room.Reconnect();
            Check(!room.CanSelectWaitDuration&&!room.SelectWaitDuration(0),"wait_connecting_gate");
            yield return Ready();if(failed)yield break;
            Check(room.BrainProcessId!=pid&&room.SelectedWaitSeconds==16&&
                  JsonUtility.ToJson(room.Latest.update.view)==view,"wait_reconnect_retains_choice");
            Check(FileHash(slotPath)==slotHash,"wait_load_does_not_modify_slot");
            File.WriteAllText(Path.Combine(output,"selected-wait.json"),
                "{\"selected_seconds\":16,\"before_tick\":"+tick+",\"waited_tick\":"+(tick+16)+
                ",\"restored_tick\":"+room.Latest.update.view.tick+"}");
        }

        IEnumerator InspectMemory(string label,int count,int acceptedAt=2,int reportedAt=12)
        {
            yield return InspectMemorySelection(label,count,false,acceptedAt,reportedAt);
            yield return InspectMemorySelection(label+"_recent",count==0?0:1,true,acceptedAt,reportedAt);
        }

        IEnumerator InspectActivity(string label,int tick)
        {
            if(failed||!room.NpcMemoryEnabled)yield break;
            var before=room.Latest.update;
            string view=JsonUtility.ToJson(before.view),bytes=FileHash(before.working_path);
            float start=Time.realtimeSinceStartup;
            room.InspectActivity();
            Check(room.Busy&&!room.CanInspectMemory,label+"_busy_gate");
            room.InspectActivity();room.InspectMemory();
            yield return Ready();if(failed)yield break;
            var after=room.Latest.update;
            Check(after.status=="ACTIVITY_INSPECTED"&&JsonUtility.ToJson(after.view)==view&&
                  after.attachment_id==before.attachment_id&&after.working_path==before.working_path&&
                  after.quest_stage==before.quest_stage&&after.quest_reward==before.quest_reward&&
                  !after.reset_log&&FileHash(after.working_path)==bytes,label+"_read_only");
            int count=Math.Min(8,tick/2);
            bool expected=after.messages.Length==(count==0?1:count);
            if(count==0)expected=expected&&after.messages[0]=="현재 저장 구간에 남은 NPC 자기 활동이 없습니다.";
            for(int i=0;i<count&&expected;i++) {
                int at=tick/2*2-(count-1-i)*2;
                string line="NPC 활동 기록 · "+at+"초: 종을 울렸습니다. (누적 "+at/2+"회)";
                expected=after.messages[i]==line&&room.HistoryForVerification.Contains(line);
            }
            Check(expected&&room.CanInspectMemory,label+"_exact_records");
            Debug.Log("NPC_ACTIVITY_LATENCY_MS "+label+" "+
                      ((Time.realtimeSinceStartup-start)*1000).ToString(CultureInfo.InvariantCulture));
        }

        IEnumerator InspectMemorySelection(string label,int count,bool recent,int acceptedAt=2,int reportedAt=12)
        {
            if(failed||!room.NpcMemoryEnabled)yield break;
            var before=room.Latest.update;
            string view=JsonUtility.ToJson(before.view),bytes=FileHash(before.working_path);
            Check(room.CanInspectMemory,label+"_enabled");
            if(recent)room.InspectRecentMemory();else room.InspectMemory();
            Check(room.Busy&&!room.CanInspectMemory,label+"_busy_gate");
            room.InspectMemory();room.InspectRecentMemory(); // Neither control may enqueue while busy.
            yield return Ready();if(failed)yield break;
            var after=room.Latest.update;
            Check(after.status=="MEMORY_INSPECTED"&&JsonUtility.ToJson(after.view)==view&&
                  after.quest_stage==before.quest_stage&&after.quest_reward==before.quest_reward&&
                  after.attachment_id==before.attachment_id&&after.working_path==before.working_path&&
                  !after.reset_log&&FileHash(after.working_path)==bytes,label+"_read_only");
            string text=String.Join("\n",after.messages);
            bool expected=count==0?after.messages.Length==1&&text.Contains("아직 기록된"):
                after.messages.Length==count&&after.messages[0].Contains(acceptedAt.ToString(CultureInfo.InvariantCulture)+"초:")&&
                after.messages[0].Contains("직접 들었습니다")&&
                (count==1||after.messages[1].Contains(reportedAt.ToString(CultureInfo.InvariantCulture)+"초:")&&
                 after.messages[1].Contains("완료 보고를 받았습니다")&&
                 after.messages[1].Contains("직접 본 기억은 아닙니다"));
            if(recent&&count!=0) {
                bool reported=before.quest_stage=="3";
                expected=after.messages.Length==1&&text.StartsWith("최근 NPC 대화 기억")&&
                    (reported?text.Contains(reportedAt.ToString(CultureInfo.InvariantCulture)+"초:")&&text.Contains("완료 보고를 받았습니다")&&
                              text.Contains("직접 본 기억은 아닙니다"):
                              text.Contains(acceptedAt.ToString(CultureInfo.InvariantCulture)+"초:")&&text.Contains("직접 들었습니다"));
            }
            Check(expected&&room.HistoryForVerification.Contains(after.messages[0])&&
                  room.CanInspectMemory,label+"_display");
        }

        IEnumerator ScenarioFlow(string scenario)
        {
            yield return Ready();if(failed){Exit(1);yield break;}
            bool grove=scenario=="grove";
            Check(room.Latest.update.scenario_id=="scenario:"+scenario,"scenario_pin_display");
            Check(room.Latest.update.view.actor_cell==(grove?"6":"0"),"scenario_initial");
            Check(room.Latest.update.view.npc_cell==(grove?"0":"6"),"scenario_npc_position");
            string initial=JsonUtility.ToJson(room.Latest.update.view);
            yield return Intent("load");
            Check(room.Latest.update.status=="SAVE_NOT_FOUND"&&
                  JsonUtility.ToJson(room.Latest.update.view)==initial,"scenario_failed_load_preserves");
            foreach(string action in new [] {grove?"up":"down","open","right",grove?"up":"down"})
                yield return Intent(action);
            yield return Intent("attack");
            var first=room.Latest.update.view;
            Check(first.actor_cell==(grove?"1":"7")&&first.actor_hp=="2"&&first.enemy_hp=="3"&&
                  first.stamina=="1"&&first.tick=="5","scenario_first_attack");
            string saved=JsonUtility.ToJson(first);
            yield return Intent("save");yield return InspectSlot("scenario_slot","5");
            yield return Intent("attack");yield return Intent("load");
            Check(room.Latest.update.reset_log&&JsonUtility.ToJson(room.Latest.update.view)==saved,
                  "scenario_load_exact_state");
            yield return Intent("attack");
            string second=JsonUtility.ToJson(room.Latest.update.view);
            yield return Intent("retry");
            Check(JsonUtility.ToJson(room.Latest.update.view)==second,"scenario_retry_once");
            yield return Intent("rest");yield return Intent("attack");
            Check(room.Latest.update.view.actor_hp=="1"&&room.Latest.update.view.enemy_hp=="0"&&
                  room.Latest.update.view.tick=="8","scenario_defeat_no_counter");
            yield return Intent("bell");
            Check(room.Latest.update.view.npc_replies=="1"&&room.Latest.update.view.npc_bells=="4",
                  "scenario_npc_chain");
            string before=JsonUtility.ToJson(room.Latest.update.view);
            int pid=room.BrainProcessId;
            room.Reconnect();yield return Ready();
            Check(room.BrainProcessId!=pid&&JsonUtility.ToJson(room.Latest.update.view)==before,
                  "scenario_loaded_branch_reconnect");
            string output=Path.Combine(Path.GetDirectoryName(
                Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING")),"evidence");
            Directory.CreateDirectory(output);
            yield return SelectSlots(output);
            yield return SelectWait(output);
            yield return InspectLayout(output);
            if(!Application.isBatchMode) {
                yield return new WaitForEndOfFrame();
                ScreenCapture.CaptureScreenshot(Path.Combine(output,"scenario.png"));
                yield return new WaitForSecondsRealtime(1);
                Check(File.Exists(Path.Combine(output,"scenario.png")),"scenario_capture");
            }
            var times=new float[120];
            for(int i=0;i<times.Length;i++){yield return null;times[i]=Time.unscaledDeltaTime;}
            Array.Sort(times);
            File.WriteAllText(Path.Combine(output,"performance.json"),
                "{\"frames\":120,\"median_ms\":"+(times[60]*1000).ToString(System.Globalization.CultureInfo.InvariantCulture)+
                ",\"p95_ms\":"+(times[114]*1000).ToString(System.Globalization.CultureInfo.InvariantCulture)+"}");
            File.WriteAllText(Path.Combine(output,"final-view.json"),JsonUtility.ToJson(room.Latest));
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        void CheckActivity(string label,string tick,string bells,string expected)
        {
            if(failed)return;
            var update=room.Latest.update;
            int count=0;
            foreach(string message in update.messages)
                if(message.StartsWith("NPC 활동 현황 · ",StringComparison.Ordinal))count++;
            Check(update.status=="COMMITTED"&&update.view.tick==tick&&
                  update.view.npc_bells==bells&&update.view.npc_replies=="0"&&count==1&&
                  Array.IndexOf(update.messages,expected)>=0&&
                  room.HistoryForVerification.EndsWith(expected,StringComparison.Ordinal),label);
        }

        void CheckNoActivity(string label)
        {
            if(failed)return;
            bool absent=true;
            foreach(string message in room.Latest.update.messages)
                if(message.StartsWith("NPC 활동 현황 · ",StringComparison.Ordinal))absent=false;
            Check(absent,label);
        }

        IEnumerator CaptureActivity(string label)
        {
            if(failed)yield break;
            string output=Path.Combine(Path.GetDirectoryName(Environment.GetEnvironmentVariable(
                "REVERIE_UNITY_WORKING")),"evidence");Directory.CreateDirectory(output);
            string response=JsonUtility.ToJson(room.Latest),history=room.HistoryForVerification;
            string bytes=FileHash(room.Latest.update.working_path);
            File.WriteAllText(Path.Combine(output,label+"-response.json"),response);
            File.WriteAllText(Path.Combine(output,label+"-history.txt"),history);
            if(!Application.isBatchMode) {
                yield return new WaitForEndOfFrame();
                ScreenCapture.CaptureScreenshot(Path.Combine(output,label+".png"));
                yield return new WaitForSecondsRealtime(1);
                Check(File.Exists(Path.Combine(output,label+".png")),label+"_capture");
            }
            Check(JsonUtility.ToJson(room.Latest)==response&&room.HistoryForVerification==history&&
                  FileHash(room.Latest.update.working_path)==bytes,label+"_capture_read_only");
        }

        IEnumerator QuestFlow()
        {
            yield return Ready();if(failed){Exit(1);yield break;}
            Check(room.Latest.update.quest_stage=="0"&&room.Latest.update.quest_reward=="0","quest_initial");
            if(room.NpcMemoryEnabled) {
                yield return InspectMemory("memory_empty",0);
                yield return InspectActivity("self_empty",0);
            }
            else {
                string initial=JsonUtility.ToJson(room.Latest.update.view);
                yield return Intent("memory");
                Check(room.Latest.update.status=="NPC_MEMORY_UNAVAILABLE"&&
                      JsonUtility.ToJson(room.Latest.update.view)==initial,"memory_disabled_explicit");
                yield return Intent("memory_recent");
                Check(room.Latest.update.status=="NPC_MEMORY_UNAVAILABLE"&&
                      JsonUtility.ToJson(room.Latest.update.view)==initial,"memory_recent_disabled_explicit");
            }
            yield return Intent("talk");
            Check(room.Latest.update.status=="OUT_OF_RANGE"&&room.Latest.update.view.tick=="0",
                  "quest_out_of_range_preserves");
            CheckNoActivity("activity_rejected_absent");
            yield return Intent("down");yield return Intent("talk");
            Check(room.Latest.update.quest_stage=="1"&&room.Latest.update.view.tick=="2","quest_accepted");
            Check(String.Join("\n",room.Latest.update.messages).Contains(QuestText("offer")),"quest_offer_text");
            CheckActivity("activity_accepted","2","1","NPC 활동 현황 · 2초 · 종 1회 · 호출 응답 0회.");
            yield return InspectMemory("memory_accepted",1);
            yield return InspectActivity("self_accepted",2);
            yield return Intent("talk");
            Check(room.Latest.update.quest_stage=="1"&&room.Latest.update.view.tick=="3"&&
                  String.Join("\n",room.Latest.update.messages).Contains(QuestText("reminder")),"quest_reminder_text");
            CheckActivity("activity_reminder","3","1","NPC 활동 현황 · 3초 · 종 1회 · 호출 응답 0회.");
            foreach(string action in new [] {"open","right","down","attack","attack","rest","attack"})
                yield return Intent(action);
            Check(room.Latest.update.quest_stage=="2"&&room.Latest.update.quest_reward=="0"&&
                  room.Latest.update.view.tick=="10"&&room.Latest.update.view.enemy_hp=="0", "quest_goal_met");
            yield return InspectMemory("memory_unreported",1);
            yield return InspectActivity("self_unreported",10);
            yield return Intent("save");yield return Intent("left");yield return Intent("talk");
            Check(room.Latest.update.quest_stage=="3"&&room.Latest.update.quest_reward=="1"&&
                  room.Latest.update.view.tick=="12","quest_report_grants_once");
            Check(String.Join("\n",room.Latest.update.messages).Contains(QuestText("completion")),"quest_completion_text");
            CheckActivity("activity_reported","12","6","NPC 활동 현황 · 12초 · 종 6회 · 호출 응답 0회.");
            yield return CaptureActivity("activity-reported");
            yield return InspectMemory("memory_reported",2);
            yield return InspectActivity("self_reported",12);
            yield return CaptureActivity("self-activity-reported");
            string committed=JsonUtility.ToJson(room.Latest.update.view);
            string committedBytes=FileHash(room.Latest.update.working_path);
            yield return Intent("retry");
            Check(JsonUtility.ToJson(room.Latest.update.view)==committed&&room.Latest.update.quest_reward=="1",
                  "quest_retry_no_second_grant");
            Check(!String.Join("\n",room.Latest.update.messages).Contains(QuestText("completion")),"quest_retry_no_repeat_line");
            CheckNoActivity("activity_retry_absent");
            Check(FileHash(room.Latest.update.working_path)==committedBytes,"activity_retry_save_unchanged");
            yield return Intent("talk");
            Check(room.Latest.update.view.tick=="13"&&room.Latest.update.quest_reward=="1"&&
                  String.Join("\n",room.Latest.update.messages).Contains(QuestText("gratitude")),"quest_gratitude");
            CheckActivity("activity_gratitude","13","6","NPC 활동 현황 · 13초 · 종 6회 · 호출 응답 0회.");
            yield return Intent("load");
            Check(room.Latest.update.quest_stage=="2"&&room.Latest.update.quest_reward=="0"&&
                  room.Latest.update.reset_log&&room.Latest.update.view.tick=="10","quest_load_progress");
            Check(room.Latest.update.view.npc_bells=="5"&&
                  !room.HistoryForVerification.Contains("NPC 활동 현황 · 12초")&&
                  !room.HistoryForVerification.Contains("NPC 활동 현황 · 13초"),"activity_load_rewinds_history");
            yield return InspectMemory("memory_loaded",1);
            yield return InspectActivity("self_loaded",10);
            if(room.NpcMemoryEnabled)Check(!room.HistoryForVerification.Contains("12초:"),"memory_load_clears_report");
            int pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.BrainProcessId!=pid&&room.Latest.update.quest_stage=="2"&&
                  room.Latest.update.view.tick=="10","quest_loaded_branch_reconnect");
            Check(room.Latest.update.view.npc_bells=="5"&&room.Latest.update.quest_reward=="0",
                  "activity_reconnect_uses_loaded_branch");
            CheckNoActivity("activity_reconnect_no_new_talk");
            yield return InspectMemory("memory_reconnected",1);
            yield return InspectActivity("self_reconnected",10);
            yield return Intent("left");yield return Intent("talk");
            Check(room.Latest.update.quest_stage=="3"&&room.Latest.update.quest_reward=="1","quest_branch_report_once");
            CheckActivity("activity_branch_reported","12","6","NPC 활동 현황 · 12초 · 종 6회 · 호출 응답 0회.");
            yield return CaptureActivity("activity-branch-reported");
            yield return InspectMemory("memory_branch_report",2);
            yield return InspectActivity("self_branch_report",12);
            yield return InspectSlot("quest_saved_slot","10");
            if(room.NpcMemoryEnabled)yield return InspectComparedSlot("slot-memory-comparison","10",1,1,0,true);
            Check(room.Latest.update.quest_reward=="1"&&
                  String.Join("\n",room.Latest.update.messages).Contains("저장된 임무: 보고 가능 · 포구의 호의 0"),
                  "slot_preview_does_not_replace_current_progress");
            string output=Path.Combine(Path.GetDirectoryName(Environment.GetEnvironmentVariable(
                "REVERIE_UNITY_WORKING")),"evidence");Directory.CreateDirectory(output);
            yield return SelectSlots(output);
            yield return SelectWait(output);
            yield return InspectLayout(output);
            if(!Application.isBatchMode) {
                yield return new WaitForEndOfFrame();
                ScreenCapture.CaptureScreenshot(Path.Combine(output,"quest.png"));
                yield return new WaitForSecondsRealtime(1);
                Check(File.Exists(Path.Combine(output,"quest.png")),"quest_capture");
            }
            File.WriteAllText(Path.Combine(output,"final-view.json"),JsonUtility.ToJson(room.Latest));
            var questTimes=new float[120];
            for(int i=0;i<questTimes.Length;i++){yield return null;questTimes[i]=Time.unscaledDeltaTime;}
            Array.Sort(questTimes);
            File.WriteAllText(Path.Combine(output,"performance.json"),
                "{\"frames\":120,\"median_ms\":"+(questTimes[60]*1000).ToString(System.Globalization.CultureInfo.InvariantCulture)+
                ",\"p95_ms\":"+(questTimes[114]*1000).ToString(System.Globalization.CultureInfo.InvariantCulture)+"}");
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator Courtyard()
        {
            var v=room.Latest.update.view;
            Check(room.Latest.narratives.Length==6,"courtyard_catalog_loaded");
            Check(v.actor_cell=="6"&&v.enemy_cell=="0"&&v.gate_cell=="2"&&v.npc_cell=="8"&&
                  v.walls.Length==1&&v.walls[0]=="7","courtyard_initial_positions");
            string output=Path.GetFullPath(Path.Combine(Application.dataPath,"..","..","..",
                "tmp","qtf02-unity","native",
                Path.GetFileName(Path.GetDirectoryName(Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING")))));
            Directory.CreateDirectory(output);
            if(!Application.isBatchMode) {
                ScreenCapture.CaptureScreenshot(Path.Combine(output,"initial.png"));
                yield return new WaitForSecondsRealtime(1);
                Check(File.Exists(Path.Combine(output,"initial.png")),"courtyard_initial_capture");
            }
            yield return Intent("right");
            Check(room.Latest.update.view.actor_cell=="6","courtyard_wall_blocks");
            yield return Intent("up");
            Check(room.Latest.update.view.actor_cell=="3","courtyard_movement");
            yield return Intent("attack");
            v=room.Latest.update.view;
            Check(v.actor_hp=="2"&&v.enemy_hp=="3"&&v.stamina=="1","courtyard_attack_counter");
            string saved=JsonUtility.ToJson(v);
            yield return Intent("save");yield return Intent("attack");yield return Intent("load");
            Check(room.Latest.update.status=="LOADED"&&JsonUtility.ToJson(room.Latest.update.view)==saved,
                  "courtyard_load_branch");
            yield return Intent("attack");string once=JsonUtility.ToJson(room.Latest.update.view);
            yield return Intent("retry");
            Check(JsonUtility.ToJson(room.Latest.update.view)==once,"courtyard_retry_once");
            yield return Intent("rest");yield return Intent("attack");
            Check(room.Latest.update.view.enemy_hp=="0"&&room.Latest.update.view.actor_hp=="1",
                  "courtyard_kill_no_counter");
            yield return Intent("up");
            Check(room.Latest.update.view.actor_cell=="0","courtyard_defeated_cell_passable");
            yield return Intent("bell");
            Check(room.Latest.update.view.npc_replies=="1","courtyard_npc_reply");
            yield return Intent("down");yield return Intent("right");yield return Intent("up");
            yield return Intent("right");
            Check(room.Latest.update.view.actor_cell=="1","courtyard_door_blocks");
            yield return Intent("open");yield return Intent("right");
            Check(room.Latest.update.view.actor_cell=="2"&&room.Latest.update.view.gate_open,
                  "courtyard_door_opens");
            string committed=JsonUtility.ToJson(room.Latest.update.view);
            System.Diagnostics.Process.GetProcessById(room.BrainProcessId).Kill();
            float until=Time.realtimeSinceStartup+12;
            while(room.Failure==""&&Time.realtimeSinceStartup<until)yield return null;
            Check(room.Failure!="","courtyard_disconnect_visible");
            room.Reconnect();yield return Ready();
            Check(room.Latest!=null&&JsonUtility.ToJson(room.Latest.update.view)==committed,
                  "courtyard_reconnect_same_scenario");
            int tick=PlayRoom.Number(room.Latest.update.view.tick);
            yield return Intent("wait");
            Check(room.Latest.update.status=="COMMITTED"&&
                  room.Latest.update.view.tick==(tick+1).ToString(),"courtyard_input_after_reconnect");
            if(!Application.isBatchMode) {
                ScreenCapture.CaptureScreenshot(Path.Combine(output,"final.png"));
                yield return new WaitForSecondsRealtime(1);
                Check(File.Exists(Path.Combine(output,"final.png")),"courtyard_final_capture");
            }
            File.WriteAllText(Path.Combine(output,"final-view.json"),JsonUtility.ToJson(room.Latest));
            Debug.Log("COURTYARD_NATIVE_OUTPUT "+output);
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");
            Exit(failed?1:0);
        }

        void CheckWork(string expected,string label)
        {
            Check(room.Latest.update.status=="COMMITTED"&&
                Array.IndexOf(room.Latest.update.messages,expected)>=0&&
                room.HistoryForVerification.EndsWith(expected,StringComparison.Ordinal),label);
        }

        void CheckRecollection(string[] expected,string previous,string label)
        {
            var actual=new System.Collections.Generic.List<string>();
            bool heading=false,empty=false;
            foreach(string message in room.Latest.update.messages) {
                if(message.StartsWith("NPC 작업 회상 · ",StringComparison.Ordinal)&&message.Contains("초: 물자"))
                    actual.Add(message);
                if(message==previous)heading=true;
                if(message=="현재 저장 구간에 새로 확인된 비축 작업이 없습니다.")empty=true;
            }
            Check(heading&&actual.Count==expected.Length,label+"_source_window");
            for(int i=0;i<Math.Min(expected.Length,actual.Count);i++)
                Check(actual[i]=="NPC 작업 회상 · "+expected[i]+"초: 물자 1개를 준비했습니다.",label+"_tick_"+expected[i]);
            if(expected.Length==0)Check(empty,label+"_empty_truthful");
        }

        void CheckCallRecollection(string[] ticks,string previous,string count,string label)
        {
            var actual=new System.Collections.Generic.List<string>();
            bool heading=false,summary=false,empty=false;
            foreach(string message in room.Latest.update.messages) {
                if(message.StartsWith("NPC 호출 회상 · ",StringComparison.Ordinal)&&message.Contains("초의 플레이어 호출에"))
                    actual.Add(message);
                if(message==previous)heading=true;
                if(message==count)summary=true;
                if(message=="현재 저장 구간에 새로 확인된 호출 응답이 없습니다.")empty=true;
            }
            Check(heading&&actual.Count==ticks.Length,label+"_heading_count");
            for(int i=0;i<Math.Min(actual.Count,ticks.Length);i++)
                Check(actual[i]=="NPC 호출 회상 · "+ticks[i]+"초의 플레이어 호출에 "+ticks[i]+"초에 응답했습니다.",label+"_tick_"+ticks[i]);
            Check(ticks.Length==0?empty:summary,label+"_range_summary");
        }

        void CheckPlayerMemory(string tick,bool reported,string label)
        {
            string expected="NPC 플레이어 기억 · "+tick+"초: "+(reported?
                "플레이어에게 완료 보고를 받았습니다. 처치를 직접 본 기억은 아닙니다.":
                "의뢰를 맡겠다는 말을 직접 들었습니다. 아직 완료 보고는 받지 못했습니다.");
            int count=0;bool exact=false;
            foreach(string message in room.Latest.update.messages) {
                if(message.StartsWith("NPC 플레이어 기억 · ",StringComparison.Ordinal))count++;
                if(message==expected)exact=true;
            }
            Check(count==1&&exact,label);
        }

        IEnumerator InspectDialogueFocus()
        {
            Check(!room.DialogueFocused,"focus_default_controls");
            string state=JsonUtility.ToJson(room.Latest),history=room.HistoryForVerification;
            string bytes=FileHash(room.Latest.update.working_path),slot=room.SelectedSlot;
            int seconds=room.SelectedWaitSeconds;
            room.ControlsScrollForVerification=70;
            yield return null;yield return new WaitForEndOfFrame();
            float controlsScroll=room.ControlsScrollForVerification;
            float normalHeight=room.HistoryViewport.height;
            room.SetDialogueFocus(true);room.SetDialogueFocus(true);
            yield return null;yield return new WaitForEndOfFrame();
            Check(room.DialogueFocused&&room.ControlsViewport.height==0&&
                room.HistoryViewport.height>normalHeight*2&&
                room.HistoryViewport.yMax<=Screen.height,"focus_expands_history");
            if(Screen.height>=376)Check(room.HistoryViewport.height>=200,"focus_compact_readable_height");
            Check(JsonUtility.ToJson(room.Latest)==state&&room.HistoryForVerification==history&&
                FileHash(room.Latest.update.working_path)==bytes,"focus_toggle_readonly_idempotent");
            yield return CaptureActivity("focus-player-reported");
            room.SetDialogueFocus(false);room.SetDialogueFocus(false);
            yield return null;yield return new WaitForEndOfFrame();
            Check(!room.DialogueFocused&&room.ControlsViewport.height>0&&
                Mathf.Abs(room.HistoryViewport.height-normalHeight)<1,"focus_restore_controls");
            Check(Mathf.Abs(room.ControlsScrollForVerification-controlsScroll)<1&&
                room.SelectedSlot==slot&&room.SelectedWaitSeconds==seconds,"focus_preserves_control_selection_scroll");
            Check(JsonUtility.ToJson(room.Latest)==state&&room.HistoryForVerification==history&&
                FileHash(room.Latest.update.working_path)==bytes,"focus_restore_readonly");
        }

        IEnumerator InspectWorkActivity(string label,string[] ticks,int stock,bool capture=false)
        {
            var before=room.Latest.update;
            string view=JsonUtility.ToJson(before.view),bytes=FileHash(before.working_path);
            float started=Time.realtimeSinceStartup;
            room.InspectActivity();
            Check(room.Busy&&!room.CanInspectMemory,label+"_busy_gate");
            room.InspectActivity();
            yield return Ready();if(failed)yield break;
            var after=room.Latest.update;
            Check(after.status=="ACTIVITY_INSPECTED"&&JsonUtility.ToJson(after.view)==view&&
                after.attachment_id==before.attachment_id&&after.working_path==before.working_path&&
                after.quest_stage==before.quest_stage&&after.quest_reward==before.quest_reward&&
                !after.reset_log&&FileHash(after.working_path)==bytes,label+"_read_only");
            var work=new System.Collections.Generic.List<string>();
            foreach(string message in after.messages)
                if(message.StartsWith("NPC 비축 작업 · ",StringComparison.Ordinal)&&message.Contains("초:"))work.Add(message);
            bool exact=work.Count==ticks.Length&&Array.IndexOf(after.messages,
                "NPC 비축 작업 · 0초 이후 저장 기록에서 확인했습니다.")>=0;
            for(int i=0;i<ticks.Length&&exact;i++) {
                string line="NPC 비축 작업 · "+ticks[i]+"초: +1개 (당시 "+(i+1)+"/3개)";
                exact=work[i]==line&&room.HistoryForVerification.Contains(line);
            }
            string final="NPC 공동 비축: 물자 "+stock+"/3개 · "+
                (stock==3?"가득 차 작업을 멈췄습니다.":"4초마다 물자 1개를 준비합니다.");
            Check(exact&&after.messages[after.messages.Length-1]==final&&
                (ticks.Length!=0||Array.IndexOf(after.messages,
                "현재 저장 구간에 남은 비축 작업 기록이 없습니다. 재고로 과거 작업을 추정하지 않습니다.")>=0),label+"_exact_work");
            Debug.Log("NPC_WORK_INSPECTION_LATENCY_MS "+label+" "+
                ((Time.realtimeSinceStartup-started)*1000).ToString(CultureInfo.InvariantCulture));
            if(capture) {
                room.SetDialogueFocus(true);
                yield return CaptureActivity(label);
                room.SetDialogueFocus(false);
            }
        }

        IEnumerator SaveManagerFlow()
        {
            if(failed)yield break;
            bool workMode=room.NpcWorkEnabled,cycleMode=room.NpcCycleEnabled;
            room.SetSaveManager(true);
            Check(room.SaveManagerOpen&&!room.DialogueFocused&&!room.GameplayInputEnabled,
                "manager_input_mode");
            Check(room.SelectSlot(6)&&room.SelectedSlot=="slot07","manager_selected_07");
            string root=Path.GetDirectoryName(room.Latest.update.working_path);
            string current=Path.Combine(root,"slots","slot07.sqlite");
            string previous=Path.Combine(root,"slots","slot07.previous.sqlite");
            room.InspectPreviousSlot();yield return Ready();
            Check(room.Latest.update.status=="PREVIOUS_SAVE_NOT_FOUND"&&room.SaveManagerOpen,
                "manager_missing_previous_explicit");
            int tick=PlayRoom.Number(room.Latest.update.view.tick);
            yield return Intent("save");
            room.SelectWaitDuration(0);yield return Intent("wait");yield return Intent("save");
            yield return Intent("wait");
            var before=room.Latest.update;
            string view=JsonUtility.ToJson(before.view),workingHash=FileHash(before.working_path);
            byte[] originalCurrent=File.ReadAllBytes(current);
            string previousHash=FileHash(previous);
            room.InspectPreviousSlot();
            Check(room.Busy&&!room.CanInspectSlot&&!room.CanSelectSlot&&!room.SelectSlot(0),
                "manager_pending_guards");
            room.LoadPreviousSlot();yield return Ready();
            Check(room.Latest.update.status=="SLOT_INSPECTED"&&
                room.Latest.update.messages[0].StartsWith("slot07 이전 저장 정보 · "+tick+"초",StringComparison.Ordinal)&&
                room.Latest.update.attachment_id==before.attachment_id&&
                JsonUtility.ToJson(room.Latest.update.view)==view&&FileHash(before.working_path)==workingHash,
                "manager_previous_preview_readonly_no_duplicate");
            yield return CaptureActivity("save-manager-preview");
            room.ControlsScrollForVerification=float.MaxValue;
            yield return CaptureActivity("save-manager-actions");
            room.ControlsScrollForVerification=0;
            File.WriteAllText(current,"F39 owned latest-slot corruption witness");
            string corruptHash=FileHash(current);
            yield return Intent("load");
            Check(room.Latest.update.status=="SAVE_CORRUPT"&&
                room.Latest.update.attachment_id==before.attachment_id&&
                JsonUtility.ToJson(room.Latest.update.view)==view,"manager_latest_corrupt_no_fallback");
            room.LoadPreviousSlot();yield return Ready();
            var loaded=room.Latest.update;
            Check(loaded.status=="LOADED"&&loaded.reset_log&&loaded.view.tick==tick.ToString(CultureInfo.InvariantCulture)&&
                loaded.attachment_id!=before.attachment_id&&loaded.working_path!=before.working_path&&
                Path.GetFileName(loaded.working_path).StartsWith(".loaded-",StringComparison.Ordinal)&&
                room.SaveManagerOpen&&room.SelectedSlot=="slot07","manager_previous_private_branch");
            Check(FileHash(current)==corruptHash&&FileHash(previous)==previousHash&&
                FileHash(before.working_path)==workingHash,"manager_restore_sources_preserved");
            yield return Intent("retry");
            Check(room.Latest.update.status=="NO_RETRY"&&room.Latest.update.view.tick==loaded.view.tick,
                "manager_restore_retry_cleared");
            yield return Intent("wait");
            Check(room.SelectSlot(7),"manager_select_08");yield return Intent("save");
            string resumedView=JsonUtility.ToJson(room.Latest.update.view);
            int pid=room.BrainProcessId;
            room.Reconnect();yield return Ready();
            Check(room.BrainProcessId!=pid&&room.SaveManagerOpen&&room.SelectedSlot=="slot08"&&
                JsonUtility.ToJson(room.Latest.update.view)==resumedView&&room.NpcMemoryEnabled&&room.NpcWorkEnabled==workMode&&room.NpcCycleEnabled==cycleMode,
                "manager_new_process_resume_pins_selection");
            yield return Intent("load");
            Check(room.SaveManagerOpen&&room.SelectedSlot=="slot08"&&
                JsonUtility.ToJson(room.Latest.update.view)==resumedView,"manager_current_load_after_recovery");
            room.ControlsScrollForVerification=0;
            yield return CaptureActivity("save-manager-restored");
            room.SetDialogueFocus(true);
            Check(!room.SaveManagerOpen&&room.DialogueFocused,"manager_dialogue_mutual_exclusion");
            room.SetSaveManager(true);
            Check(room.SaveManagerOpen&&!room.DialogueFocused,"manager_reopen_from_dialogue");
            room.SetSaveManager(false);
            Check(!room.SaveManagerOpen&&room.GameplayInputEnabled,"manager_close_restores_input");
            Check(FileHash(current)==corruptHash&&FileHash(previous)==previousHash,
                "manager_continue_did_not_repair_sources");
            // Restore only this verification run's deliberately damaged fixture after preservation checks.
            File.WriteAllBytes(current,originalCurrent);
        }

        IEnumerator CycleActivity(string summary,string[] expected,string[] assisted=null,int assistTotal=0)
        {
            string view=JsonUtility.ToJson(room.Latest.update.view);
            string bytes=FileHash(room.Latest.update.working_path);
            room.InspectActivity();
            Check(room.Busy&&!room.CanInspectMemory,"cycle_activity_pending_guard");
            room.InspectActivity();yield return Ready();
            var update=room.Latest.update;
            Check(update.status=="ACTIVITY_INSPECTED"&&update.messages[0]==summary,
                "cycle_activity_counters");
            int activityCount=Math.Min(8,int.Parse(update.view.tick,CultureInfo.InvariantCulture)/2);
            int prefixCount=expected.Length+5+Math.Max(1,activityCount);
            int assistanceCount=room.NpcAidEnabled?2+(assisted==null?0:assisted.Length):0;
            Check(update.messages.Length==prefixCount+assistanceCount,"cycle_memory_and_activity_bounded_count");
            Check(update.messages[prefixCount-2]=="NPC 호출 회상 · 현재 저장 구간에서 확인한 응답입니다."&&
                update.messages[prefixCount-1]=="현재 저장 구간에 새로 확인된 호출 응답이 없습니다.",
                "cycle_empty_causal_calls_explicit");
            for(int index=0;index<expected.Length;index++)
                Check(update.messages[index+2]==expected[index],"cycle_memory_anchor_"+index);
            Check(update.messages[expected.Length+2].StartsWith("NPC 종·호출 활동 · ",StringComparison.Ordinal)&&
                update.messages[expected.Length+2].Contains("최근 최대 8개"),"cycle_activity_source_boundary");
            if(activityCount==0)Check(update.messages[expected.Length+3].Contains(
                "누적 횟수로 과거 활동을 추정하지 않습니다"),"cycle_activity_empty_no_inference");
            else {
                int latest=int.Parse(update.view.tick,CultureInfo.InvariantCulture)/2*2;
                for(int index=0;index<activityCount;index++) {
                    int tick=latest-(activityCount-1-index)*2;
                    Check(update.messages[expected.Length+3+index]=="NPC 활동 기록 · "+tick+
                        "초: 종을 울렸습니다. (누적 "+(tick/2)+"회)","cycle_bell_activity_"+tick);
                }
            }
            Check(JsonUtility.ToJson(update.view)==view&&FileHash(update.working_path)==bytes,
                "cycle_activity_readonly");
            if(room.NpcAidEnabled)CheckAidActivity(assisted??new string[0],assistTotal);
        }

        void CheckAidActivity(string[] ticks,int total)
        {
            var messages=room.Latest.update.messages;
            int start=messages.Length-2-ticks.Length;
            Check(start>=0&&messages[start]=="NPC 의뢰 지원 · 0초 이후 저장 구간의 최근 최대 3건입니다.",
                "aid_activity_source_boundary");
            Check(messages[start+1]==(ticks.Length==0?
                "현재 저장 구간에 남은 의뢰 지원 기록이 없습니다. 문 상태로 과거 도움을 추정하지 않습니다.":
                "확인한 문 열기 "+total+"건 중 최근 "+ticks.Length+"건입니다."),"aid_activity_confirmed_count");
            for(int index=0;index<ticks.Length;index++)
                Check(messages[start+2+index]=="NPC 의뢰 지원 기록 · "+ticks[index]+"초: 통행문을 열었습니다.",
                    "aid_activity_retained_open_"+ticks[index]);
        }

        void CheckAidReturn(string heading,string[] details,int retainedRows)
        {
            var messages=room.Latest.update.messages;
            int start=Array.IndexOf(messages,heading);
            Check(start>=0&&start+details.Length<messages.Length,"aid_return_source_window");
            if(start<0||start+details.Length>=messages.Length)return;
            for(int index=0;index<details.Length;index++)
                Check(messages[start+1+index]==details[index],"aid_return_line_"+index);
            Check(Array.FindAll(messages,m=>m.StartsWith("NPC 의뢰 지원 회상 · ",StringComparison.Ordinal)).Length==retainedRows+1,
                "aid_return_only_confirmed_rows");
        }

        Color[] PanelSamples()
        {
            var pixels=new Texture2D(Screen.width,Screen.height,TextureFormat.RGB24,false);
            try {
                pixels.ReadPixels(new Rect(0,0,Screen.width,Screen.height),0,0);pixels.Apply();
                return new [] {pixels.GetPixel(30,Screen.height-80),pixels.GetPixel(Screen.width-20,Screen.height-80)};
            } finally {Destroy(pixels);}
        }

        IEnumerator PanelOcclusion()
        {
            var cameras=Camera.allCameras;
            Check(cameras.Length==1,"panel_probe_one_world_camera");if(failed)yield break;
            var camera=cameras[0];Color original=camera.backgroundColor;
            var flags=camera.clearFlags;bool focus=room.DialogueFocused;
            string state=JsonUtility.ToJson(room.Latest),history=room.HistoryForVerification;
            string bytes=FileHash(room.Latest.update.working_path);
            Color[] red=null,green=null;
            try {
                room.SetDialogueFocus(true);camera.clearFlags=CameraClearFlags.SolidColor;
                camera.backgroundColor=Color.red;yield return new WaitForEndOfFrame();red=PanelSamples();
                yield return CaptureActivity("panel-red-background");
                camera.backgroundColor=Color.green;yield return new WaitForEndOfFrame();green=PanelSamples();
                yield return CaptureActivity("panel-green-background");
            } finally {
                camera.backgroundColor=original;camera.clearFlags=flags;room.SetDialogueFocus(focus);
            }
            Debug.Log("PANEL_PIXEL_SAMPLES red="+red[0]+" green="+green[0]+" outside="+red[1]+"/"+green[1]);
            Check(red[1].r>green[1].r+.2f&&green[1].g>red[1].g+.2f,"panel_probe_world_background_changes");
            Check(Mathf.Abs(red[0].r-green[0].r)+Mathf.Abs(red[0].g-green[0].g)+
                Mathf.Abs(red[0].b-green[0].b)<.02f&&
                Mathf.Max(red[0].r,red[0].g,red[0].b,green[0].r,green[0].g,green[0].b)<.2f,
                "panel_backing_blocks_world_pixels");
            Check(JsonUtility.ToJson(room.Latest)==state&&room.HistoryForVerification==history&&
                FileHash(room.Latest.update.working_path)==bytes&&room.DialogueFocused==focus&&
                camera.backgroundColor==original&&camera.clearFlags==flags,"panel_probe_restores_readonly_state");
        }

        IEnumerator HistoryReadingPosition()
        {
            for(int index=0;index<20&&room.HistoryCountForVerification<200;index++) {
                room.InspectActivity();yield return Ready();if(failed)yield break;
                yield return null;yield return new WaitForEndOfFrame();
            }
            Check(room.HistoryCountForVerification==200,"history_probe_reaches_bounded_cap");
            string view=JsonUtility.ToJson(room.Latest.update.view),bytes=FileHash(room.Latest.update.working_path);
            room.SetDialogueFocus(true);yield return null;yield return new WaitForEndOfFrame();
            room.HistoryScrollForVerification=room.HistoryContentHeightForVerification*.45f;
            yield return null;yield return new WaitForEndOfFrame();
            string top=room.HistoryTopForVerification;float offset=room.HistoryRowOffsetForVerification;
            yield return CaptureActivity("history-reading-before");
            room.InspectActivity();yield return Ready();yield return null;yield return new WaitForEndOfFrame();
            yield return CaptureActivity("history-reading-after");
            Debug.Log("HISTORY_READING_TOP before="+top+" after="+room.HistoryTopForVerification+
                " offsets="+offset+"/"+room.HistoryRowOffsetForVerification);
            Check(room.HistoryTopForVerification==top&&Mathf.Abs(room.HistoryRowOffsetForVerification-offset)<2&&
                room.HistoryScrollForVerification+room.HistoryViewport.height<room.HistoryContentHeightForVerification*.85f,
                "history_append_preserves_retained_reading_position");
            Check(JsonUtility.ToJson(room.Latest.update.view)==view&&FileHash(room.Latest.update.working_path)==bytes&&
                room.HistoryCountForVerification==200,"history_append_readonly_and_bounded");
            if(failed){room.SetDialogueFocus(false);yield break;}
            room.HistoryScrollForVerification=0;
            yield return null;yield return new WaitForEndOfFrame();
            room.InspectActivity();yield return Ready();yield return null;yield return new WaitForEndOfFrame();
            Check(room.HistoryScrollForVerification<=2&&room.HistoryCountForVerification==200,
                "history_evicted_top_clamps_to_first_retained");
            string latestHistory=room.HistoryForVerification;
            room.ShowLatestHistory();
            yield return null;yield return new WaitForEndOfFrame();
            Check(room.HistoryForVerification==latestHistory&&JsonUtility.ToJson(room.Latest.update.view)==view&&
                FileHash(room.Latest.update.working_path)==bytes,"history_latest_action_readonly");
            room.InspectActivity();yield return Ready();yield return null;yield return new WaitForEndOfFrame();
            Check(room.HistoryScrollForVerification+room.HistoryViewport.height>=room.HistoryContentHeightForVerification-2,
                "history_tail_reader_follows_new_output");
            room.SetDialogueFocus(false);
        }

        void CheckPatrolCell(string cell,string label)
        {
            int value=int.Parse(cell,CultureInfo.InvariantCulture);
            Check(room.Latest.update.view.npc_cell==cell&&
                room.NpcPositionForVerification==new Vector3(value%3,.5f,-(value/3)),label);
        }

        IEnumerator ReadyPatrolFlow()
        {
            const string policy="NPC 지원 준비 · 의뢰 진행 중 통행문이 닫혀 있고 공동 물자가 2개 미만이면 원래 작업 지점 복귀·대기를 우선합니다.";
            const string nextNeighbor="NPC 다음 순찰 행동 · 다음 행동 시점에 옆 작업 지점으로 이동을 시도합니다. (현재 상태 기준)";
            const string idle="NPC 다음 순찰 행동 · 현재 작업 지점에서 기다립니다. (현재 상태 기준)";
            const string blockedHome="NPC 다음 순찰 행동 · 원래 작업 지점을 플레이어가 점유 중입니다. 현재 상태에서는 이동을 기다립니다.";
            room.SelectWaitDuration(0);
            Check(room.NpcReadyPatrolEnabled&&room.NpcCallPauseEnabled&&
                room.NpcModeLabel=="NPC 지원 준비 우선·호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드","ready_patrol_selection");
            yield return Intent("down");yield return Intent("talk");
            Check(Array.IndexOf(room.Latest.update.messages,idle)>=0&&
                Array.FindAll(room.Latest.update.messages,m=>m==policy).Length==1,"ready_patrol_low_stock_talk_plan");
            yield return Intent("up");yield return Intent("wait");CheckPatrolCell("6","ready_patrol_low_stock_holds4");
            Check(room.Latest.update.view.tick=="4","ready_patrol_first_production_time");yield return Intent("save");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("6","ready_patrol_low_stock_holds6");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("6","ready_patrol_prior_barrier_holds8");
            string bytes=FileHash(room.Latest.update.working_path);room.InspectActivity();yield return Ready();
            Check(room.Latest.update.view.tick=="8"&&FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,nextNeighbor)>=0&&
                Array.FindAll(room.Latest.update.messages,m=>m==policy).Length==1,"ready_patrol_new_stock_next_goal");
            room.InspectSlot();yield return Ready();Check(FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,"NPC 다음 순찰 행동 비교 · 현재 8초 / 선택 저장 4초")>=0&&
                Array.IndexOf(room.Latest.update.messages,"현재 "+nextNeighbor)>=0&&
                Array.IndexOf(room.Latest.update.messages,"선택 저장 "+idle)>=0,"ready_patrol_saved_stock_own_goal");
            yield return Intent("wait");yield return Intent("bell");CheckPatrolCell("6","ready_patrol_actual_answer_holds10");
            Check(room.Latest.update.view.tick=="10"&&room.Latest.update.view.npc_replies=="1"&&
                room.Latest.update.view.gate_open&&room.GateOpenForVerification,"ready_patrol_actual_aid_same_turn");
            bytes=FileHash(room.Latest.update.working_path);yield return Intent("retry");
            Check(FileHash(room.Latest.update.working_path)==bytes&&room.Latest.update.view.npc_replies=="1",
                "ready_patrol_retry_no_extra_reply");yield return Intent("save");
            room.InspectPreviousSlot();yield return Ready();Check(
                Array.IndexOf(room.Latest.update.messages,"NPC 다음 순찰 행동 비교 · 현재 10초 / 선택 저장 4초")>=0&&
                Array.IndexOf(room.Latest.update.messages,"현재 "+nextNeighbor)>=0&&
                Array.IndexOf(room.Latest.update.messages,"선택 저장 "+idle)>=0,"ready_patrol_saved_gate_own_goal");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","ready_patrol_next_wake_resumes12");
            string original=room.Latest.update.working_path,originalBytes=FileHash(original);
            yield return Intent("load");CheckPatrolCell("6","ready_patrol_load_no_latent_pause");
            int pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.NpcReadyPatrolEnabled&&room.BrainProcessId!=pid&&room.Latest.update.view.tick=="10",
                "ready_patrol_reconnect_mode");
            bytes=FileHash(room.Latest.update.working_path);room.InspectActivity();yield return Ready();
            Check(FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,nextNeighbor)>=0,"ready_patrol_open_gate_low_stock_patrol");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","ready_patrol_reconnected_resumes12");
            yield return Intent("down");yield return Intent("down");CheckPatrolCell("7","ready_patrol_occupied_home14");
            room.InspectActivity();yield return Ready();Check(room.Latest.update.view.tick=="14"&&
                Array.IndexOf(room.Latest.update.messages,blockedHome)>=0,"ready_patrol_occupied_reason");
            yield return Intent("up");yield return Intent("wait");CheckPatrolCell("6","ready_patrol_free_home16");
            yield return Intent("right");yield return Intent("down");yield return Intent("attack");
            yield return Intent("attack");yield return Intent("rest");yield return Intent("attack");
            Check(room.Latest.update.view.tick=="22"&&room.Latest.update.view.enemy_hp=="0"&&
                room.Latest.update.quest_stage=="2"&&room.Latest.update.quest_reward=="0","ready_patrol_unreported_defeat");
            yield return Intent("up");yield return Intent("left");CheckPatrolCell("7","ready_patrol_own_accepted_goal");
            yield return Intent("down");yield return Intent("talk");CheckPatrolCell("7","ready_patrol_report_hold26");
            Check(room.Latest.update.quest_reward=="1"&&Array.IndexOf(room.Latest.update.messages,blockedHome)>=0,
                "ready_patrol_report_reward_once");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","ready_patrol_reported_waits28");
            yield return Intent("up");yield return Intent("wait");CheckPatrolCell("6","ready_patrol_reported_returns30");
            yield return Intent("talk");Check(room.Latest.update.view.tick=="31"&&room.Latest.update.quest_reward=="1"&&
                Array.IndexOf(room.Latest.update.messages,idle)>=0,"ready_patrol_final_idle_no_extra_reward");
            room.InspectActivity();yield return Ready();Check(Array.FindAll(room.Latest.update.messages,m=>m==policy).Length==1,
                "ready_patrol_policy_once");room.InspectSlot();yield return Ready();
            Check(Array.IndexOf(room.Latest.update.messages,"NPC 다음 순찰 행동 비교 · 현재 31초 / 선택 저장 10초")>=0&&
                Array.IndexOf(room.Latest.update.messages,"현재 "+idle)>=0&&
                Array.IndexOf(room.Latest.update.messages,"선택 저장 "+nextNeighbor)>=0,"ready_patrol_reported_vs_saved_goal");
            Check(FileHash(original)==originalBytes,"ready_patrol_original_source_preserved");
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-ready-patrol");room.SetDialogueFocus(false);
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator CallPausePatrolFlow()
        {
            room.SelectWaitDuration(0);
            const string nextNeighbor="NPC 다음 순찰 행동 · 다음 행동 시점에 옆 작업 지점으로 이동을 시도합니다. (현재 상태 기준)";
            const string nextHome="NPC 다음 순찰 행동 · 다음 행동 시점에 원래 작업 지점으로 이동을 시도합니다. (현재 상태 기준)";
            const string blockedHome="NPC 다음 순찰 행동 · 원래 작업 지점을 플레이어가 점유 중입니다. 현재 상태에서는 이동을 기다립니다.";
            const string idle="NPC 다음 순찰 행동 · 현재 작업 지점에서 기다립니다. (현재 상태 기준)";
            Check(room.NpcCallPauseEnabled&&room.NpcQuestPatrolEnabled&&room.NpcTalkPauseEnabled&&
                room.NpcModeLabel=="NPC 호출 응답 대기·의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드","call_pause_selection");
            yield return Intent("down");yield return Intent("talk");
            Check(Array.IndexOf(room.Latest.update.messages,nextNeighbor)>=0,"call_pause_talk_next_goal");
            yield return Intent("up");
            yield return Intent("bell");CheckPatrolCell("6","call_pause_even_answer_holds");
            Check(room.Latest.update.view.tick=="4"&&room.Latest.update.view.npc_replies=="1"&&
                Array.IndexOf(room.Latest.update.messages,"NPC가 공동 작업 구역을 순찰했습니다.")<0,"call_pause_actual_answer_no_move");
            yield return Intent("save");
            string savedPath=room.Latest.update.working_path,bytes=FileHash(savedPath);
            room.InspectActivity();yield return Ready();
            Check(Array.IndexOf(room.Latest.update.messages,
                "NPC 응답 대기 · 호출에 답한 턴에는 이동을 멈추고, 다음 행동 시점에 순찰 계획을 다시 따릅니다.")>=0&&
                FileHash(savedPath)==bytes,"call_pause_policy_readonly");
            Check(Array.IndexOf(room.Latest.update.messages,nextNeighbor)>=0,"call_pause_answer_no_future_pause");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","call_pause_next_actual_wake");
            Check(room.Latest.update.view.tick=="6","call_pause_resume_time");
            bytes=FileHash(room.Latest.update.working_path);room.InspectSlot();yield return Ready();
            Check(room.Latest.update.view.tick=="6"&&FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,"NPC 다음 순찰 행동 비교 · 현재 6초 / 선택 저장 4초")>=0&&
                Array.IndexOf(room.Latest.update.messages,"현재 "+nextHome)>=0&&
                Array.IndexOf(room.Latest.update.messages,"선택 저장 "+nextNeighbor)>=0,"call_pause_slot_different_next_targets");
            string original=room.Latest.update.working_path,originalBytes=FileHash(original);
            yield return Intent("load");CheckPatrolCell("6","call_pause_load_current_cell");
            Check(room.Latest.update.view.tick=="4","call_pause_load_time");
            int pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.NpcCallPauseEnabled&&room.BrainProcessId!=pid&&room.Latest.update.view.tick=="4",
                "call_pause_reconnect_selection");
            bytes=FileHash(room.Latest.update.working_path);room.InspectActivity();yield return Ready();
            Check(FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,nextNeighbor)>=0,"call_pause_reconnected_next_goal");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","call_pause_no_saved_hold");
            yield return Intent("wait");yield return Intent("bell");CheckPatrolCell("7","call_pause_second_even_answer");
            Check(room.Latest.update.view.tick=="8"&&room.Latest.update.view.npc_replies=="2","call_pause_repeated_answer_count");
            bytes=FileHash(room.Latest.update.working_path);room.InspectActivity();yield return Ready();
            Check(FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,nextHome)>=0,"call_pause_answer_at_neighbor_next_goal");
            bytes=FileHash(room.Latest.update.working_path);yield return Intent("retry");
            Check(FileHash(room.Latest.update.working_path)==bytes&&room.Latest.update.view.npc_replies=="2",
                "call_pause_exact_retry_no_duplicate");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("6","call_pause_resume_existing_goal");
            Check(room.Latest.update.view.tick=="10"&&FileHash(original)==originalBytes,"call_pause_branch_source_preserved");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","call_pause_occupancy_setup");
            yield return Intent("down");yield return Intent("down");CheckPatrolCell("7","call_pause_blocked_home");
            Check(room.Latest.update.view.tick=="14"&&room.Latest.update.view.actor_cell=="6","call_pause_blocked_home_time");
            yield return Intent("save");bytes=FileHash(room.Latest.update.working_path);
            room.InspectActivity();yield return Ready();
            Check(FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,blockedHome)>=0,"call_pause_actual_blocked_reason");
            yield return Intent("up");bytes=FileHash(room.Latest.update.working_path);
            room.InspectSlot();yield return Ready();
            Check(room.Latest.update.view.tick=="15"&&FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,"NPC 다음 순찰 행동 비교 · 현재 15초 / 선택 저장 14초")>=0&&
                Array.IndexOf(room.Latest.update.messages,"현재 "+nextHome)>=0&&
                Array.IndexOf(room.Latest.update.messages,"선택 저장 "+blockedHome)>=0,"call_pause_slot_own_occupancy");
            room.InspectPreviousSlot();yield return Ready();
            Check(FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,"NPC 다음 순찰 행동 비교 · 현재 15초 / 선택 저장 4초")>=0&&
                Array.IndexOf(room.Latest.update.messages,"현재 "+nextHome)>=0&&
                Array.IndexOf(room.Latest.update.messages,"선택 저장 "+nextNeighbor)>=0,"call_pause_previous_slot_own_goal");
            yield return Intent("wait");CheckPatrolCell("6","call_pause_free_target_resumes");
            bytes=FileHash(room.Latest.update.working_path);room.InspectSlot();yield return Ready();
            Check(room.Latest.update.view.tick=="16"&&FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,"현재 "+nextNeighbor)>=0&&
                Array.IndexOf(room.Latest.update.messages,"선택 저장 "+blockedHome)>=0,"call_pause_arrived_current_saved_blocked");
            string blockedSource=room.Latest.update.working_path,blockedSourceBytes=FileHash(blockedSource);
            yield return Intent("load");CheckPatrolCell("7","call_pause_load_blocked_branch");
            Check(room.Latest.update.view.tick=="14"&&room.Latest.update.working_path!=blockedSource,
                "call_pause_load_blocked_time");
            pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.NpcCallPauseEnabled&&room.BrainProcessId!=pid&&room.Latest.update.view.tick=="14",
                "call_pause_blocked_reconnect_selection");
            bytes=FileHash(room.Latest.update.working_path);room.InspectActivity();yield return Ready();
            Check(FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,blockedHome)>=0,"call_pause_reconnected_blocked_reason");
            yield return Intent("up");yield return Intent("wait");CheckPatrolCell("6","call_pause_reconnected_target_freed");
            yield return Intent("right");yield return Intent("down");yield return Intent("attack");
            yield return Intent("attack");yield return Intent("rest");yield return Intent("attack");
            Check(room.Latest.update.view.tick=="22"&&room.Latest.update.view.enemy_hp=="0"&&
                room.Latest.update.quest_stage=="2"&&room.Latest.update.quest_reward=="0","call_pause_unreported_defeat");
            yield return Intent("up");yield return Intent("left");CheckPatrolCell("7","call_pause_not_omniscient_patrol");
            yield return Intent("down");yield return Intent("talk");CheckPatrolCell("7","call_pause_report_held");
            Check(room.Latest.update.view.tick=="26"&&room.Latest.update.quest_stage=="3"&&
                room.Latest.update.quest_reward=="1"&&Array.IndexOf(room.Latest.update.messages,blockedHome)>=0,
                "call_pause_report_reward_once");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","call_pause_reported_occupied_home");
            room.InspectActivity();yield return Ready();Check(room.Latest.update.view.tick=="28"&&
                Array.IndexOf(room.Latest.update.messages,blockedHome)>=0,"call_pause_reported_wait_reason");
            yield return Intent("up");room.InspectActivity();yield return Ready();
            Check(Array.IndexOf(room.Latest.update.messages,nextHome)>=0,"call_pause_reported_target_freed");
            yield return Intent("wait");CheckPatrolCell("6","call_pause_reported_return_home");
            yield return Intent("talk");Check(room.Latest.update.view.tick=="31"&&
                room.Latest.update.quest_reward=="1"&&room.Latest.update.view.npc_replies=="2"&&
                Array.IndexOf(room.Latest.update.messages,idle)>=0,"call_pause_gratitude_no_duplicate_reward");
            room.InspectActivity();yield return Ready();
            Check(Array.IndexOf(room.Latest.update.messages,idle)>=0,"call_pause_final_idle_goal");
            room.InspectSlot();yield return Ready();Check(
                Array.IndexOf(room.Latest.update.messages,"NPC 다음 순찰 행동 비교 · 현재 31초 / 선택 저장 14초")>=0&&
                Array.IndexOf(room.Latest.update.messages,"현재 "+idle)>=0&&
                Array.IndexOf(room.Latest.update.messages,"선택 저장 "+blockedHome)>=0,"call_pause_reported_current_saved_accepted");
            Check(FileHash(original)==originalBytes&&FileHash(blockedSource)==blockedSourceBytes,
                "call_pause_all_branch_sources_preserved");
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-call-pause");room.SetDialogueFocus(false);
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator QuestPatrolFlow()
        {
            Check(room.NpcQuestPatrolEnabled&&room.NpcTalkPauseEnabled&&room.NpcPatrolEnabled&&
                room.NpcModeLabel=="NPC 의뢰 순찰·대화 대기·호출 지원·물자·반복 작업·기억 모드","quest_patrol_selection");
            for(int i=0;i<4;i++){yield return Intent("wait");CheckPatrolCell("6","quest_patrol_unheard_home_"+i);}
            yield return Intent("down");yield return Intent("talk");CheckPatrolCell("6","quest_patrol_accept_hold");
            Check(Array.IndexOf(room.Latest.update.messages,
                "NPC 의뢰 순찰 계획 · 수락을 직접 들어 공동 작업 구역 순찰을 목표로 합니다.")>=0,"quest_patrol_heard_goal");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","quest_patrol_accepted_moves");
            yield return Intent("down");yield return Intent("bell");yield return Intent("talk");
            Check(room.Latest.update.view.gate_open&&room.GateOpenForVerification,"quest_patrol_existing_aid");
            foreach(string action in new [] {"right","attack","attack","rest","attack","up","left"})
                yield return Intent(action);
            Check(room.Latest.update.view.tick=="18"&&room.Latest.update.view.enemy_hp=="0"&&
                room.Latest.update.quest_stage=="2"&&room.Latest.update.quest_reward=="0","quest_patrol_unreported_defeat");
            CheckPatrolCell("7","quest_patrol_not_omniscient");
            yield return Intent("down");yield return Intent("talk");CheckPatrolCell("7","quest_patrol_report_hold");
            Check(room.Latest.update.quest_reward=="1"&&Array.IndexOf(room.Latest.update.messages,
                "NPC 의뢰 순찰 계획 · 완료 보고를 들어 원래 작업 지점으로 돌아갈 준비를 합니다.")>=0,"quest_patrol_reported_goal");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","quest_patrol_occupied_home_waits");
            Check(room.Latest.update.view.tick=="22","quest_patrol_blocked_time");yield return Intent("save");
            yield return Intent("up");yield return Intent("wait");CheckPatrolCell("6","quest_patrol_free_home_returns");
            Check(room.Latest.update.view.tick=="24","quest_patrol_return_time");
            string original=room.Latest.update.working_path,originalBytes=FileHash(room.Latest.update.working_path);
            yield return Intent("load");CheckPatrolCell("7","quest_patrol_saved_pending_return");
            string source=room.Latest.update.working_path,bytes=FileHash(source);int pid=room.BrainProcessId;
            room.Reconnect();yield return Ready();Check(room.NpcQuestPatrolEnabled&&room.BrainProcessId!=pid&&
                room.Latest.update.view.tick=="22","quest_patrol_reconnect_goal");
            yield return Intent("up");yield return Intent("wait");CheckPatrolCell("6","quest_patrol_reconnected_returns");
            room.SelectWaitDuration(3);yield return Intent("wait");room.SelectWaitDuration(0);
            Check(room.Latest.update.view.tick=="40"&&Array.IndexOf(room.Latest.update.messages,
                "NPC가 공동 작업 구역을 순찰했습니다.")<0,"quest_patrol_home_stays");CheckPatrolCell("6","quest_patrol_final_home");
            room.InspectActivity();yield return Ready();Check(Array.IndexOf(room.Latest.update.messages,
                "NPC 의뢰 순찰 계획 · 완료 보고를 들어 원래 작업 지점에서 기다립니다.")>=0,"quest_patrol_home_plan");
            Check(FileHash(source)!=bytes&&FileHash(original)==originalBytes,"quest_patrol_branch_advanced_source_preserved");
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-quest-patrol");room.SetDialogueFocus(false);
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator TalkPausePatrolFlow()
        {
            Check(room.NpcTalkPauseEnabled&&room.NpcPatrolEnabled&&room.NpcCallAidEnabled&&
                room.NpcModeLabel=="NPC 대화 대기·순찰·호출 지원·물자·반복 작업·기억 모드","talk_patrol_selection");
            yield return Intent("down");yield return Intent("talk");CheckPatrolCell("6","talk_patrol_initial_hold");
            Check(room.Latest.update.view.tick=="2"&&room.Latest.update.status=="COMMITTED"&&
                Array.IndexOf(room.Latest.update.messages,"NPC가 공동 작업 구역을 순찰했습니다.")<0,"talk_patrol_no_false_move");
            yield return Intent("save");yield return Intent("talk");yield return Intent("talk");
            CheckPatrolCell("6","talk_patrol_repeated_hold");Check(room.Latest.update.view.tick=="4","talk_patrol_repeated_time");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("7","talk_patrol_wait_resumes");
            string bytes=FileHash(room.Latest.update.working_path),view=JsonUtility.ToJson(room.Latest.update.view);
            yield return Intent("talk");
            Check(room.Latest.update.status=="OUT_OF_RANGE"&&JsonUtility.ToJson(room.Latest.update.view)==view&&
                FileHash(room.Latest.update.working_path)==bytes,"talk_patrol_rejected_talk_readonly");
            yield return Intent("down");yield return Intent("talk");CheckPatrolCell("7","talk_patrol_current_position_talk");
            yield return Intent("save");yield return Intent("bell");
            Check(room.Latest.update.view.tick=="9"&&room.Latest.update.view.gate_open&&room.GateOpenForVerification,
                "talk_patrol_existing_call_aid");
            yield return CallAidActivity("NPC 반복 작업: 물자 2/3개 · 준비 2회 · 사용 0회.",new [] {"9"},1,new [] {"9"});
            string source=room.Latest.update.working_path;bytes=FileHash(source);
            yield return Intent("load_previous");CheckPatrolCell("6","talk_patrol_previous_pose");
            int pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.NpcTalkPauseEnabled&&room.BrainProcessId!=pid&&room.Latest.update.view.tick=="2",
                "talk_patrol_reconnect_mode");CheckPatrolCell("6","talk_patrol_reconnect_pose");
            room.SelectWaitDuration(3);yield return Intent("wait");room.SelectWaitDuration(0);
            Check(room.Latest.update.view.tick=="18"&&
                Array.FindAll(room.Latest.update.messages,m=>m=="NPC가 공동 작업 구역을 순찰했습니다.").Length==8,
                "talk_patrol_long_wait_actual_moves");CheckPatrolCell("6","talk_patrol_long_wait_net_identity");
            Check(FileHash(source)==bytes,"talk_patrol_original_source_preserved");
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-talk-patrol");room.SetDialogueFocus(false);
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator PatrolFlow()
        {
            Check(room.NpcPatrolEnabled&&room.NpcCallAidEnabled&&room.NpcSupplyAidEnabled&&
                room.NpcModeLabel=="NPC 순찰·호출 지원·물자·반복 작업·기억 모드","patrol_mode_selection");
            yield return Intent("down");yield return Intent("talk");CheckPatrolCell("7","patrol_after_talk_moves");
            Check(room.Latest.update.view.tick=="2"&&room.Latest.update.status=="COMMITTED","patrol_talk_before_move");
            yield return Intent("save");
            string bytes=FileHash(room.Latest.update.working_path),view=JsonUtility.ToJson(room.Latest.update.view);
            yield return Intent("talk");
            Check(room.Latest.update.status=="OUT_OF_RANGE"&&JsonUtility.ToJson(room.Latest.update.view)==view&&
                FileHash(room.Latest.update.working_path)==bytes,"patrol_current_position_range_readonly");
            yield return Intent("down");yield return Intent("talk");
            CheckPatrolCell("7","patrol_player_blocks_destination");
            Check(room.Latest.update.view.tick=="4"&&room.Latest.update.view.actor_cell=="6"&&
                Array.IndexOf(room.Latest.update.messages,"NPC가 공동 작업 구역을 순찰했습니다.")<0,
                "patrol_blocked_wake_no_false_movement");
            yield return Intent("up");yield return Intent("wait");CheckPatrolCell("6","patrol_destination_freed");
            yield return Intent("wait");yield return Intent("wait");yield return Intent("bell");
            Check(room.Latest.update.view.tick=="9"&&room.Latest.update.view.gate_open&&room.GateOpenForVerification,
                "patrol_answered_call_support");
            yield return CallAidActivity("NPC 반복 작업: 물자 2/3개 · 준비 2회 · 사용 0회.",new [] {"9"},1,new [] {"9"});
            yield return Intent("save");string source=room.Latest.update.working_path;bytes=FileHash(source);
            yield return Intent("load_previous");CheckPatrolCell("7","patrol_previous_pose_restored");
            int pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.NpcPatrolEnabled&&room.BrainProcessId!=pid&&room.Latest.update.view.tick=="2",
                "patrol_reconnect_selection_and_branch");
            CheckPatrolCell("7","patrol_reconnect_pose");
            yield return Intent("wait");yield return Intent("wait");CheckPatrolCell("6","patrol_resumed_movement");
            room.SelectWaitDuration(3);yield return Intent("wait");room.SelectWaitDuration(0);
            Check(room.Latest.update.view.tick=="20"&&
                Array.FindAll(room.Latest.update.messages,m=>m=="NPC가 공동 작업 구역을 순찰했습니다.").Length==8,
                "patrol_long_wait_keeps_intermediate_moves");
            CheckPatrolCell("6","patrol_long_wait_net_identity");
            Check(FileHash(source)==bytes,"patrol_original_source_preserved");
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-patrol");room.SetDialogueFocus(false);
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator CallAidActivity(string summary,string[] calls,int callTotal,string[] aid,string checkpoint="0")
        {
            string view=JsonUtility.ToJson(room.Latest.update.view);
            string bytes=FileHash(room.Latest.update.working_path);
            room.InspectActivity();yield return Ready();if(failed)yield break;
            var update=room.Latest.update;var text=update.messages;
            Check(update.status=="ACTIVITY_INSPECTED"&&text.Length>0&&text[0]==summary,
                "call_aid_supply_counters");
            Check(Array.IndexOf(text,"확인한 호출 응답 "+callTotal+"건 중 최근 "+calls.Length+"건입니다.")>=0,
                "call_aid_confirmed_calls");
            var rows=Array.FindAll(text,m=>m.StartsWith("NPC 호출 회상 · ",StringComparison.Ordinal)&&m.Contains("초의"));
            Check(rows.Length==calls.Length,"call_aid_bounded_call_rows");
            for(int i=0;i<Math.Min(rows.Length,calls.Length);i++)
                Check(rows[i]=="NPC 호출 회상 · "+calls[i]+"초의 플레이어 호출에 "+calls[i]+"초에 응답했습니다.",
                    "call_aid_actual_reply_"+calls[i]);
            Check(Array.IndexOf(text,"NPC 의뢰 지원 · "+checkpoint+"초 이후 저장 구간의 최근 최대 3건입니다.")>=0,
                "call_aid_retained_source_boundary");
            var aidRows=Array.FindAll(text,m=>m.StartsWith("NPC 의뢰 지원 기록 · ",StringComparison.Ordinal));
            Check(aidRows.Length==aid.Length,"call_aid_retained_open_count");
            for(int i=0;i<Math.Min(aidRows.Length,aid.Length);i++)
                Check(aidRows[i]=="NPC 의뢰 지원 기록 · "+aid[i]+"초: 통행문을 열었습니다.",
                    "call_aid_retained_open_"+aid[i]);
            Check(JsonUtility.ToJson(update.view)==view&&FileHash(update.working_path)==bytes,
                "call_aid_activity_readonly");
        }

        IEnumerator CallAidFlow()
        {
            const string opened="NPC가 의뢰를 돕기 위해 통행문을 열었습니다.";
            Check(room.NpcCallAidEnabled&&room.NpcSupplyAidEnabled&&room.NpcAidEnabled&&
                room.NpcCycleEnabled&&room.NpcMemoryEnabled&&
                room.NpcModeLabel=="NPC 호출 지원·물자·반복 작업·기억 모드","call_aid_mode_selection");
            yield return Intent("down");yield return Intent("talk");yield return Intent("save");
            for(int i=0;i<5;i++)yield return Intent("wait");
            yield return Intent("bell");
            Check(room.Latest.update.view.tick=="8"&&!room.Latest.update.view.gate_open&&!room.GateOpenForVerification&&
                Array.IndexOf(room.Latest.update.messages,opened)<0,"call_aid_same_tick_preparation_waits");
            yield return CallAidActivity("NPC 반복 작업: 물자 2/3개 · 준비 2회 · 사용 0회.",new [] {"8"},1,new string[0]);
            yield return Intent("save");yield return Intent("bell");
            Check(room.Latest.update.view.tick=="9"&&room.Latest.update.view.gate_open&&room.GateOpenForVerification&&
                Array.FindAll(room.Latest.update.messages,m=>m==opened).Length==1,"call_aid_odd_answer_opens_once");
            string bytes=FileHash(room.Latest.update.working_path),view=JsonUtility.ToJson(room.Latest.update.view);
            yield return Intent("retry");
            Check(FileHash(room.Latest.update.working_path)==bytes&&JsonUtility.ToJson(room.Latest.update.view)==view&&
                Array.IndexOf(room.Latest.update.messages,opened)<0,"call_aid_retry_preserves_commit");
            yield return CallAidActivity("NPC 반복 작업: 물자 2/3개 · 준비 2회 · 사용 0회.",new [] {"8","9"},2,new [] {"9"});
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-call-aid-odd");room.SetDialogueFocus(false);
            yield return Intent("save");yield return Intent("talk");
            bytes=FileHash(room.Latest.update.working_path);view=JsonUtility.ToJson(room.Latest.update.view);
            room.InspectPreviousSlot();yield return Ready();
            Check(room.Latest.update.status=="SLOT_INSPECTED"&&
                Array.IndexOf(room.Latest.update.messages,"NPC 지원 계획 비교 · 현재 10초 / 선택 저장 8초")>=0&&
                Array.IndexOf(room.Latest.update.messages,"선택 저장 NPC 지원 계획 · 공동 물자가 확보되어 NPC 호출로 통행 지원을 요청할 수 있습니다.")>=0&&
                FileHash(room.Latest.update.working_path)==bytes&&JsonUtility.ToJson(room.Latest.update.view)==view,
                "call_aid_previous_ready_plan_readonly");
            string source=room.Latest.update.working_path;
            yield return Intent("load_previous");
            Check(room.Latest.update.view.tick=="8"&&!room.Latest.update.view.gate_open&&!room.GateOpenForVerification&&
                room.Latest.update.working_path!=source&&FileHash(source)==bytes,"call_aid_loaded_separate_branch");
            int pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.NpcCallAidEnabled&&room.BrainProcessId!=pid&&room.Latest.update.view.tick=="8",
                "call_aid_reconnect_current_branch");
            yield return Intent("bell");
            Check(room.Latest.update.view.tick=="9"&&room.Latest.update.view.gate_open&&room.GateOpenForVerification&&
                Array.FindAll(room.Latest.update.messages,m=>m==opened).Length==1,"call_aid_branch_real_odd_opening");
            yield return Intent("wait");yield return Intent("close");yield return Intent("bell");
            Check(room.Latest.update.view.tick=="12"&&!room.Latest.update.view.gate_open&&!room.GateOpenForVerification&&
                Array.IndexOf(room.Latest.update.messages,opened)<0,"call_aid_reprepared_stock_waits");
            yield return Intent("bell");
            Check(room.Latest.update.view.tick=="13"&&room.Latest.update.view.gate_open&&room.GateOpenForVerification&&
                Array.FindAll(room.Latest.update.messages,m=>m==opened).Length==1,"call_aid_prior_stock_reopens");
            yield return CallAidActivity("NPC 반복 작업: 물자 2/3개 · 준비 3회 · 사용 1회.",new [] {"9","12","13"},4,new [] {"9","13"});
            yield return Intent("save");yield return Intent("talk");
            CheckAidReturn("NPC 의뢰 지원 회상 · 지난 대화(2초) 뒤에 도운 기록입니다.",new [] {
                "확인한 문 열기 2건 중 최근 2건입니다.","NPC 의뢰 지원 회상 · 9초: 통행문을 열었습니다.",
                "NPC 의뢰 지원 회상 · 13초: 통행문을 열었습니다."},2);
            foreach(string action in new [] {"right","down","attack","attack","rest","attack","up","left","talk"})
                yield return Intent(action);
            Check(room.Latest.update.view.tick=="23"&&room.Latest.update.quest_reward=="1","call_aid_report_once");
            yield return Intent("close");yield return Intent("bell");
            Check(room.Latest.update.view.tick=="25"&&!room.Latest.update.view.gate_open&&!room.GateOpenForVerification&&
                Array.IndexOf(room.Latest.update.messages,opened)<0,"call_aid_report_stops_answered_support");
            yield return CallAidActivity("NPC 반복 작업: 물자 3/3개 · 준비 5회 · 사용 2회.",new [] {"12","13","25"},5,new [] {"9","13"});
            Check(FileHash(source)==bytes,"call_aid_original_source_preserved");
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-call-aid-completed");room.SetDialogueFocus(false);
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator SupplyAidFlow()
        {
            const string opened="NPC가 의뢰를 돕기 위해 통행문을 열었습니다.";
            Check(room.NpcSupplyAidEnabled&&room.NpcAidEnabled&&room.NpcCycleEnabled&&room.NpcMemoryEnabled&&
                room.NpcModeLabel=="NPC 물자 2개 확보 후 지원·반복 작업·기억 모드","supply_aid_mode_selection");
            yield return Intent("down");yield return Intent("talk");
            Check(room.Latest.update.view.tick=="2"&&!room.Latest.update.view.gate_open,"supply_aid_direct_acceptance_closed");
            CheckPlayerMemory("2",false,"supply_aid_direct_promise");
            CheckAidReturn("NPC 의뢰 지원 회상 · 0초 이후 저장 구간의 도움입니다.",new [] {
                "현재 저장 구간에 새로 확인된 의뢰 지원 기록이 없습니다."},0);
            yield return Intent("save");
            foreach(string tick in new [] {"4","6","8"}) {
                yield return Intent("wait");yield return Intent("wait");
                Check(room.Latest.update.view.tick==tick&&!room.Latest.update.view.gate_open&&!room.GateOpenForVerification,
                    "supply_aid_prior_barrier_closed_"+tick);
                Check(Array.IndexOf(room.Latest.update.messages,opened)<0,"supply_aid_no_false_open_"+tick);
            }
            yield return Intent("wait");yield return Intent("wait");
            Check(room.Latest.update.view.tick=="10"&&room.Latest.update.view.gate_open&&room.GateOpenForVerification&&
                Array.IndexOf(room.Latest.update.messages,opened)>=0,"supply_aid_prior_two_opens_during_consumption");
            string bytes=FileHash(room.Latest.update.working_path);
            yield return Intent("retry");
            Check(FileHash(room.Latest.update.working_path)==bytes&&Array.IndexOf(room.Latest.update.messages,opened)<0,
                "supply_aid_retry_no_action_or_write");
            yield return CycleActivity("NPC 반복 작업: 물자 1/3개 · 준비 2회 · 사용 1회.",new [] {
                "NPC 작업 기억 · 4초: 공동 물자 1개를 준비했습니다 · 물자 1/3개.",
                "NPC 작업 기억 · 8초: 공동 물자 1개를 준비했습니다 · 물자 2/3개.",
                "NPC 작업 기억 · 10초: 공동 물자 1개를 사용했습니다 · 물자 1/3개."},new [] {"10"},1);
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-supply-aid-open");room.SetDialogueFocus(false);
            yield return Intent("close");yield return Intent("wait");
            Check(room.Latest.update.view.tick=="12"&&!room.Latest.update.view.gate_open&&!room.GateOpenForVerification&&
                Array.IndexOf(room.Latest.update.messages,opened)<0,"supply_aid_same_barrier_preparation_waits");
            yield return Intent("wait");yield return Intent("wait");
            Check(room.Latest.update.view.tick=="14"&&room.Latest.update.view.gate_open&&room.GateOpenForVerification&&
                Array.IndexOf(room.Latest.update.messages,opened)>=0,"supply_aid_ready_reopens_after_preparation");
            yield return Intent("save");yield return Intent("talk");
            CheckAidReturn("NPC 의뢰 지원 회상 · 지난 대화(2초) 뒤에 도운 기록입니다.",new [] {
                "확인한 문 열기 2건 중 최근 2건입니다.","NPC 의뢰 지원 회상 · 10초: 통행문을 열었습니다.",
                "NPC 의뢰 지원 회상 · 14초: 통행문을 열었습니다."},2);
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-supply-aid-return");room.SetDialogueFocus(false);
            room.InspectPreviousSlot();yield return Ready();
            Check(room.Latest.update.status=="SLOT_INSPECTED","supply_aid_previous_preview");
            yield return Intent("load_previous");
            Check(room.Latest.update.view.tick=="2"&&!room.Latest.update.view.gate_open&&!room.GateOpenForVerification,
                "supply_aid_previous_branch_restored");
            int pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.NpcSupplyAidEnabled&&room.BrainProcessId!=pid&&room.Latest.update.view.tick=="2",
                "supply_aid_reconnect_preserves_selection");
            for(int i=0;i<6;i++)yield return Intent("wait");
            Check(room.Latest.update.view.tick=="8"&&!room.Latest.update.view.gate_open,
                "supply_aid_loaded_branch_does_not_open_early");
            yield return Intent("wait");yield return Intent("wait");
            Check(room.Latest.update.view.tick=="10"&&room.Latest.update.view.gate_open&&
                Array.IndexOf(room.Latest.update.messages,opened)>=0,"supply_aid_loaded_branch_real_opening");
            foreach(string action in new [] {"right","down","attack","attack","rest","attack","up","left","talk"})
                yield return Intent(action);
            Check(room.Latest.update.view.tick=="19"&&room.Latest.update.quest_reward=="1","supply_aid_report_once");
            CheckPlayerMemory("19",true,"supply_aid_heard_report");
            CheckAidReturn("NPC 의뢰 지원 회상 · 지난 대화(2초) 뒤에 도운 기록입니다.",new [] {
                "확인한 문 열기 1건 중 최근 1건입니다.","NPC 의뢰 지원 회상 · 10초: 통행문을 열었습니다."},1);
            yield return Intent("close");room.SelectWaitDuration(3);yield return Intent("wait");room.SelectWaitDuration(0);
            Check(room.Latest.update.view.tick=="36"&&!room.Latest.update.view.gate_open&&!room.GateOpenForVerification&&
                Array.IndexOf(room.Latest.update.messages,opened)<0,"supply_aid_report_stops_ready_support");
            yield return Intent("save");
            room.InspectActivity();yield return Ready();
            Check(room.Latest.update.status=="ACTIVITY_INSPECTED","supply_aid_current_source_query");
            CheckAidActivity(new [] {"10"},1);
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-supply-aid-completed");room.SetDialogueFocus(false);
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator AidFlow()
        {
            const string opened="NPC가 의뢰를 돕기 위해 통행문을 열었습니다.";
            Check(room.NpcAidEnabled&&room.NpcCycleEnabled&&room.NpcMemoryEnabled&&
                room.NpcModeLabel=="NPC 의뢰 지원·반복 작업·기억 모드","aid_mode_selection");
            yield return Intent("down");yield return Intent("talk");
            Check(room.Latest.update.view.tick=="2"&&!room.Latest.update.view.gate_open,
                "aid_acceptance_barrier_does_not_open_early");
            CheckPlayerMemory("2",false,"aid_direct_promise");
            CheckAidReturn("NPC 의뢰 지원 회상 · 0초 이후 저장 구간의 도움입니다.",new [] {
                "현재 저장 구간에 새로 확인된 의뢰 지원 기록이 없습니다."},0);
            yield return Intent("save");yield return Intent("wait");
            Check(!room.Latest.update.view.gate_open,"aid_odd_tick_closed");
            yield return Intent("right");
            Check(room.Latest.update.view.tick=="4"&&room.Latest.update.view.actor_cell=="3"&&
                room.Latest.update.view.gate_open&&room.GateOpenForVerification&&Array.IndexOf(room.Latest.update.messages,opened)>=0&&
                room.Latest.update.status=="COMMITTED","aid_blocked_move_then_real_wake_opens");
            string bytes=FileHash(room.Latest.update.working_path);
            yield return Intent("retry");
            Check(FileHash(room.Latest.update.working_path)==bytes&&
                Array.IndexOf(room.Latest.update.messages,opened)<0,"aid_retry_no_reopen_or_write");
            yield return CycleActivity("NPC 반복 작업: 물자 1/3개 · 준비 1회 · 사용 0회.",new [] {
                "NPC 작업 기억 · 4초: 공동 물자 1개를 준비했습니다 · 물자 1/3개."},new [] {"4"},1);
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-gate-aid-open");room.SetDialogueFocus(false);
            yield return Intent("close");
            Check(!room.Latest.update.view.gate_open,"aid_odd_close");
            yield return Intent("wait");
            Check(room.Latest.update.view.gate_open&&Array.IndexOf(room.Latest.update.messages,opened)>=0,
                "aid_next_wake_reopens");
            yield return Intent("wait");yield return Intent("close");
            Check(room.Latest.update.view.tick=="8"&&room.Latest.update.view.gate_open&&
                room.Latest.update.status=="COMMITTED"&&Array.IndexOf(room.Latest.update.messages,opened)>=0,
                "aid_even_close_and_reopen_projection");
            yield return Intent("save");
            room.InspectPreviousSlot();yield return Ready();
            Check(room.Latest.update.status=="SLOT_INSPECTED","aid_previous_preview");
            yield return Intent("load_previous");
            Check(room.Latest.update.view.tick=="2"&&!room.Latest.update.view.gate_open,
                "aid_previous_load_rewinds_gate");
            Check(!room.GateOpenForVerification,"aid_previous_load_restores_visible_gate");
            int pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.NpcAidEnabled&&room.BrainProcessId!=pid&&room.Latest.update.view.tick=="2",
                "aid_reconnect_retains_variant");
            yield return Intent("wait");yield return Intent("wait");
            Check(room.Latest.update.view.gate_open&&Array.IndexOf(room.Latest.update.messages,opened)>=0,
                "aid_loaded_promise_drives_new_action");
            yield return CycleActivity("NPC 반복 작업: 물자 1/3개 · 준비 1회 · 사용 0회.",new [] {
                "NPC 작업 기억 · 4초: 공동 물자 1개를 준비했습니다 · 물자 1/3개."},new [] {"4"},1);
            foreach(string action in new [] {"right","down","attack","attack","rest","attack","up","left","talk"})
                yield return Intent(action);
            Check(room.Latest.update.view.tick=="13"&&room.Latest.update.quest_reward=="1",
                "aid_combat_and_report_reward_once");
            CheckPlayerMemory("13",true,"aid_report_not_eyewitness");
            CheckAidReturn("NPC 의뢰 지원 회상 · 지난 대화(2초) 뒤에 도운 기록입니다.",new [] {
                "확인한 문 열기 1건 중 최근 1건입니다.",
                "NPC 의뢰 지원 회상 · 4초: 통행문을 열었습니다."},1);
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-gate-aid-return-talk");room.SetDialogueFocus(false);
            yield return Intent("close");room.SelectWaitDuration(3);yield return Intent("wait");
            Check(room.Latest.update.view.tick=="30"&&!room.Latest.update.view.gate_open&&
                !room.GateOpenForVerification&&Array.IndexOf(room.Latest.update.messages,opened)<0,"aid_report_stops_future_support");
            room.SelectWaitDuration(0);yield return Intent("save");
            room.InspectActivity();yield return Ready();
            Check(room.Latest.update.status=="ACTIVITY_INSPECTED","aid_current_replay_query");
            CheckAidActivity(new [] {"4"},1);
            room.SetDialogueFocus(true);yield return CaptureActivity("npc-gate-aid-completed");room.SetDialogueFocus(false);
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator CycleFlow()
        {
            Check(room.NpcCycleEnabled&&!room.NpcWorkEnabled&&room.NpcMemoryEnabled&&
                room.NpcModeLabel=="NPC 반복 작업·기억 모드","cycle_mode_badge_and_selection");
            Check(room.Latest.update.view.tick=="0","cycle_genesis");
            yield return PanelOcclusion();if(failed){Exit(1);yield break;}
            yield return CycleActivity("NPC 반복 작업: 물자 0/3개 · 준비 0회 · 사용 0회.",new string[0]);
            yield return Intent("save");
            yield return Intent("talk");
            Check(room.Latest.update.status=="OUT_OF_RANGE"&&room.Latest.update.view.tick=="0",
                "cycle_rejected_talk_preserves_time");
            room.SelectWaitDuration(3);yield return Intent("wait");
            room.SelectWaitDuration(1);yield return Intent("wait");
            string[] at20={
                "NPC 작업 기억 · 12초: 공동 물자 1개를 준비했습니다 · 물자 2/3개.",
                "NPC 작업 기억 · 16초: 공동 물자 1개를 준비했습니다 · 물자 3/3개.",
                "NPC 작업 기억 · 20초: 공동 물자 1개를 사용했습니다 · 물자 2/3개.",
                "NPC 작업 기억 · 20초: 공동 물자 1개를 준비했습니다 · 물자 3/3개."};
            string bytes=FileHash(room.Latest.update.working_path);
            yield return Intent("retry");
            Check(room.Latest.update.messages.Length==1&&room.Latest.update.messages[0]==
                "이미 처리된 명령의 결과를 확인했습니다. 행동은 다시 실행하지 않았습니다."&&
                FileHash(room.Latest.update.working_path)==bytes,
                "cycle_retry_no_duplicate_memory_or_write");
            yield return CycleActivity("NPC 반복 작업: 물자 3/3개 · 준비 5회 · 사용 2회.",at20);
            room.SetDialogueFocus(true);yield return CaptureActivity("cycle-tie-memory");room.SetDialogueFocus(false);
            yield return Intent("save");
            room.SelectWaitDuration(2);yield return Intent("wait");
            room.SelectWaitDuration(0);yield return Intent("wait");yield return Intent("wait");
            Check(room.Latest.update.view.tick=="30"&&room.Latest.update.quest_reward=="0",
                "cycle_offscreen_consumption_no_player_reward");
            yield return Intent("load");
            Check(room.Latest.update.view.tick=="20","cycle_load_rewinds_clock");
            yield return CycleActivity("NPC 반복 작업: 물자 3/3개 · 준비 5회 · 사용 2회.",at20);
            int pid=room.BrainProcessId;room.Reconnect();yield return Ready();
            Check(room.BrainProcessId!=pid&&room.NpcCycleEnabled&&room.Latest.update.view.tick=="20",
                "cycle_new_process_retains_mode_time");
            yield return CycleActivity("NPC 반복 작업: 물자 3/3개 · 준비 5회 · 사용 2회.",at20);
            foreach(string action in new [] {"down","talk","open","right","down","attack","attack","rest","attack"})
            {
                yield return Intent(action);
                if(action=="talk")CheckPlayerMemory("22",false,"cycle_player_promise_committed");
            }
            yield return Intent("left");yield return Intent("talk");
            Check(room.Latest.update.quest_stage=="3"&&room.Latest.update.quest_reward=="1",
                "cycle_quest_combat_report_reward_independent");
            Check(String.Join("\n",room.Latest.update.messages).Contains("NPC 작업 기억 · 30초: 공동 물자 1개를 사용"),
                "cycle_talk_uses_own_persisted_memory");
            CheckPlayerMemory("31",true,"cycle_player_report_not_eyewitness");
            string returnChange=String.Join("\n",room.Latest.update.messages);
            Check(returnChange.Contains("NPC 반복 작업 회상 · 지난 대화(22초) 뒤의 변화입니다.")&&
                returnChange.Contains("확인한 물자 변화 · 준비 0회 · 사용 1회."),"cycle_return_change_since22");
            room.SetDialogueFocus(true);yield return CaptureActivity("cycle-return-change");room.SetDialogueFocus(false);
            room.SetDialogueFocus(true);yield return CaptureActivity("cycle-player-report");room.SetDialogueFocus(false);
            yield return InspectMemory("cycle_player_conversation_separate",2,22,31);
            room.SetDialogueFocus(true);room.InspectActivity();yield return Ready();
            yield return CaptureActivity("cycle-after-report");room.SetDialogueFocus(false);
            for(int index=0;index<5;index++)yield return Intent("bell");
            yield return Intent("talk");
            CheckCallRecollection(new [] {"34","35","36"},
                "NPC 호출 회상 · 지난 대화(31초) 뒤에 끝낸 응답입니다.",
                "확인한 호출 응답 5건 중 최근 3건입니다.","cycle_talk_call_recall");
            returnChange=String.Join("\n",room.Latest.update.messages);
            Check(returnChange.Contains("NPC 반복 작업 회상 · 지난 대화(31초) 뒤의 변화입니다.")&&
                returnChange.Contains("확인한 물자 변화 · 준비 1회 · 사용 0회."),"cycle_return_change_since31");
            room.SetDialogueFocus(true);yield return CaptureActivity("cycle-talk-calls");room.SetDialogueFocus(false);
            string callTick=room.Latest.update.view.tick,callBytes=FileHash(room.Latest.update.working_path);
            room.SetDialogueFocus(true);room.InspectActivity();yield return Ready();
            string callText=String.Join("\n",room.Latest.update.messages);
            Check(callText.Contains("확인한 호출 응답 5건 중 최근 3건입니다."),"cycle_causal_call_count_and_cap");
            for(int tick=34;tick<=36;tick++)Check(callText.Contains("NPC 호출 회상 · "+tick+
                "초의 플레이어 호출에 "+tick+"초에 응답했습니다."),"cycle_causal_call_"+tick);
            Check(!callText.Contains("32초의 플레이어 호출에")&&!callText.Contains("33초의 플레이어 호출에"),
                "cycle_causal_calls_keep_latest_three");
            Check(callText.Contains("NPC 작업 기억 · ")&&callText.Contains("NPC 활동 기록 · "),
                "cycle_call_supply_and_mixed_sections_separate");
            Check(room.Latest.update.view.tick==callTick&&FileHash(room.Latest.update.working_path)==callBytes,
                "cycle_call_inspection_readonly");
            yield return CaptureActivity("cycle-causal-calls");room.SetDialogueFocus(false);
            room.Reconnect();yield return Ready();room.InspectActivity();yield return Ready();
            Check(String.Join("\n",room.Latest.update.messages)==callText,"cycle_causal_calls_reconnect");
            yield return HistoryReadingPosition();if(failed){Exit(1);yield break;}
            yield return SaveManagerFlow();
            yield return null;yield return new WaitForEndOfFrame();
            Check(room.HistoryScrollForVerification+room.HistoryViewport.height>=room.HistoryContentHeightForVerification-2,
                "history_load_reset_follows_new_branch");
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        IEnumerator WorkFlow()
        {
            yield return Ready();if(failed){Exit(1);yield break;}
            Check(room.NpcWorkEnabled&&room.NpcMemoryEnabled,"work_selected_memory_mode");
            Check(room.Latest.update.view.tick=="0"&&room.Latest.update.quest_stage=="0","work_genesis");
            yield return InspectWorkActivity("work_inspect_empty",new string[0],0);
            yield return Intent("talk");
            Check(room.Latest.update.status=="OUT_OF_RANGE"&&room.Latest.update.view.tick=="0","work_rejected_talk_no_time");
            yield return Intent("down");yield return Intent("talk");
            CheckWork("NPC 공동 비축: 물자 0/3개 · 4초마다 물자 1개를 준비합니다.","work_initial_stock_zero");
            CheckRecollection(new string[0],"NPC 작업 회상 · 현재 저장 구간에서 확인한 작업입니다.","recall_first");
            CheckPlayerMemory("2",false,"player_promise_committed");
            room.SelectWaitDuration(1);yield return Intent("wait");
            Check(room.Latest.update.view.tick=="6","work_offscreen_wait_tick6");
            Check(Array.IndexOf(room.Latest.update.messages,"NPC가 공동 비축 물자 1개를 준비했습니다. (재고 1/3개)")>=0,"work_first_production");
            yield return Intent("save");
            yield return Intent("talk");
            CheckWork("NPC 공동 비축: 물자 1/3개 · 4초마다 물자 1개를 준비합니다.","work_return_stock1");
            CheckRecollection(new [] {"4"},"NPC 작업 회상 · 지난 대화(2초) 뒤에 끝낸 작업입니다.","recall_first_return");
            string first=FileHash(room.Latest.update.working_path);
            yield return Intent("retry");
            bool quiet=true;
            foreach(string message in room.Latest.update.messages)
                if(message.Contains("공동 비축"))quiet=false;
            foreach(string message in room.Latest.update.messages)
                if(message.Contains("작업 회상"))quiet=false;
            Check(quiet&&FileHash(room.Latest.update.working_path)==first,"work_retry_quiet_unchanged");
            room.SelectWaitDuration(2);yield return Intent("wait");yield return Intent("talk");
            CheckWork("NPC 공동 비축: 물자 3/3개 · 가득 차 작업을 멈췄습니다.","work_capacity_return3");
            CheckRecollection(new [] {"8","12"},"NPC 작업 회상 · 지난 대화(7초) 뒤에 끝낸 작업입니다.","recall_later_return");
            yield return CaptureActivity("work-full");
            string working=room.Latest.update.working_path;
            string bytes=FileHash(working),tick=room.Latest.update.view.tick;
            room.InspectActivity();yield return Ready();
            bool production=false;
            foreach(string message in room.Latest.update.messages)
                if(message.Contains("12초: 공동 비축 물자 1개"))production=true;
            Check(production&&room.Latest.update.status=="ACTIVITY_INSPECTED"&&
                room.Latest.update.view.tick==tick&&FileHash(working)==bytes,"work_activity_source_readonly");
            yield return CaptureActivity("work-activity");
            yield return InspectWorkActivity("work_inspect_full",new [] {"4","8","12"},3);
            room.InspectSlot();yield return Ready();
            Check(Array.IndexOf(room.Latest.update.messages,
                "저장된 NPC 공동 비축: 물자 1/3개 · 4초마다 물자 1개를 준비합니다.")>=0&&
                FileHash(working)==bytes,"work_slot_preview_readonly_stock1");
            yield return InspectComparedSlot("work_slot_same_memory","6",1,0,0);
            yield return Intent("load");yield return Intent("talk");
            CheckWork("NPC 공동 비축: 물자 1/3개 · 4초마다 물자 1개를 준비합니다.","work_load_rewinds1");
            CheckRecollection(new [] {"4"},"NPC 작업 회상 · 지난 대화(2초) 뒤에 끝낸 작업입니다.","recall_load_branch");
            Check(room.Latest.update.view.tick=="7","work_load_time_rewinds");
            yield return InspectWorkActivity("work_inspect_loaded",new [] {"4"},1);
            room.SelectWaitDuration(0);yield return Intent("wait");yield return Intent("talk");
            CheckWork("NPC 공동 비축: 물자 2/3개 · 4초마다 물자 1개를 준비합니다.","work_resumed_production2");
            CheckRecollection(new [] {"8"},"NPC 작업 회상 · 지난 대화(7초) 뒤에 끝낸 작업입니다.","recall_resumed");
            room.Reconnect();yield return Ready();yield return Intent("talk");
            CheckWork("NPC 공동 비축: 물자 2/3개 · 4초마다 물자 1개를 준비합니다.","work_reconnect_preserves2");
            CheckRecollection(new string[0],"NPC 작업 회상 · 지난 대화(9초) 뒤에 끝낸 작업입니다.","recall_reconnect");
            Check(room.Latest.update.quest_stage=="1"&&room.Latest.update.quest_reward=="0","work_no_player_reward_grant");
            yield return CaptureActivity("work-reconnected");
            CheckCallRecollection(new string[0],"NPC 호출 회상 · 지난 대화(9초) 뒤에 끝낸 응답입니다.","","call_initial_empty");
            yield return InspectWorkActivity("work_inspect_reconnected",new [] {"4","8"},2);
            yield return Intent("bell");
            Check(room.Latest.update.view.npc_replies=="1","call_actual_response");
            room.SelectWaitDuration(3);yield return Intent("wait");yield return Intent("save");
            Check(room.Latest.update.view.tick=="27","call_saved_before_return");
            yield return InspectWorkActivity("work-inspect-late",new [] {"4","8","12"},3,true);
            yield return Intent("talk");
            CheckCallRecollection(new [] {"11"},"NPC 호출 회상 · 지난 대화(10초) 뒤에 끝낸 응답입니다.",
                "확인한 호출 응답 1건 중 최근 1건입니다.","call_old_return");
            yield return CaptureActivity("call-return");
            for(int i=0;i<5;i++)yield return Intent("bell");
            yield return Intent("talk");
            CheckCallRecollection(new [] {"31","32","33"},"NPC 호출 회상 · 지난 대화(28초) 뒤에 끝낸 응답입니다.",
                "확인한 호출 응답 5건 중 최근 3건입니다.","call_capped");
            yield return CaptureActivity("call-capped");
            string callBytes=FileHash(room.Latest.update.working_path);
            yield return Intent("retry");
            Check(!String.Join("\n",room.Latest.update.messages).Contains("호출 회상")&&
                FileHash(room.Latest.update.working_path)==callBytes,"call_retry_quiet_unchanged");
            yield return Intent("talk");
            CheckCallRecollection(new string[0],"NPC 호출 회상 · 지난 대화(34초) 뒤에 끝낸 응답입니다.","","call_next_empty");
            yield return Intent("load");
            Check(room.Latest.update.view.tick=="27"&&room.Latest.update.view.npc_replies=="1","call_load_rewinds");
            room.Reconnect();yield return Ready();yield return Intent("talk");
            CheckCallRecollection(new [] {"11"},"NPC 호출 회상 · 지난 대화(10초) 뒤에 끝낸 응답입니다.",
                "확인한 호출 응답 1건 중 최근 1건입니다.","call_loaded_reconnected");
            Check(room.Latest.update.quest_stage=="1"&&room.Latest.update.quest_reward=="0","call_no_added_reward");
            yield return CaptureActivity("call-restored");
            CheckPlayerMemory("2",false,"player_old_promise_retained");
            yield return CaptureActivity("player-promise");
            foreach(string action in new [] {"open","right","down","attack","attack","rest","attack"})
                yield return Intent(action);
            Check(room.Latest.update.view.tick=="35"&&room.Latest.update.view.enemy_hp=="0"&&
                room.Latest.update.quest_stage=="2"&&room.Latest.update.quest_reward=="0","player_unreported_defeat");
            yield return InspectMemory("player_unreported_memory",1);
            yield return Intent("save");yield return Intent("left");yield return Intent("talk");
            CheckPlayerMemory("37",true,"player_report_committed");
            Check(room.Latest.update.quest_reward=="1","player_report_reward_once");
            yield return Intent("talk");
            CheckPlayerMemory("37",true,"player_report_original_tick");
            yield return CaptureActivity("player-reported");
            yield return InspectComparedSlot("work-slot-memory-comparison","35",1,1,0,true);
            yield return InspectDialogueFocus();
            string playerBytes=FileHash(room.Latest.update.working_path);
            yield return Intent("retry");
            Check(!String.Join("\n",room.Latest.update.messages).Contains("NPC 플레이어 기억")&&
                room.Latest.update.quest_reward=="1"&&FileHash(room.Latest.update.working_path)==playerBytes,
                "player_retry_quiet_unchanged");
            yield return Intent("load");room.Reconnect();yield return Ready();
            Check(room.Latest.update.view.tick=="35"&&room.Latest.update.quest_stage=="2"&&
                room.Latest.update.quest_reward=="0","player_load_reconnect_unreported");
            yield return InspectMemory("player_loaded_promise",1);
            room.SelectWaitDuration(0);yield return Intent("wait");yield return Intent("left");yield return Intent("talk");
            CheckPlayerMemory("38",true,"player_loaded_report_new_tick");
            Check(room.Latest.update.quest_reward=="1","player_loaded_report_reward_once");
            yield return CaptureActivity("player-restored");
            room.Send("wait");Check(room.Busy,"focus_inflight_started");room.SetDialogueFocus(true);
            yield return Ready();
            Check(room.DialogueFocused&&room.Latest.update.view.tick=="39","focus_inflight_response_polled");
            yield return Intent("load");
            Check(room.DialogueFocused&&room.Latest.update.view.tick=="35"&&
                room.Latest.update.quest_reward=="0"&&
                !room.HistoryForVerification.Contains("NPC 플레이어 기억 · 38초:"),"focus_load_retained_rewinds_history");
            string focusedView=JsonUtility.ToJson(room.Latest.update.view);
            room.Reconnect();yield return Ready();
            Check(room.DialogueFocused&&JsonUtility.ToJson(room.Latest.update.view)==focusedView,
                "focus_reconnect_retained");
            string focusedBytes=FileHash(room.Latest.update.working_path);
            room.SendMalformedForVerification();yield return Ready();
            yield return null;yield return new WaitForEndOfFrame();
            Check(room.DialogueFocused&&room.TransportError=="INVALID_REQUEST"&&
                room.ControlsViewport.height==24,"focus_transport_error_visible_strip");
            Check(JsonUtility.ToJson(room.Latest.update.view)==focusedView&&
                FileHash(room.Latest.update.working_path)==focusedBytes,"focus_transport_error_readonly");
            yield return CaptureActivity("focus-error");
            room.SetDialogueFocus(false);
            Check(!room.DialogueFocused,"focus_can_return_after_reconnect");
            yield return SaveManagerFlow();
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");Exit(failed?1:0);
        }

        static string SelectionError(string selectionCase)
        {
            switch(selectionCase) {
                case "invalid-aid":return "NPC_AID_CONTENT";
                case "invalid-aid-selection":return "NPC_AID_SELECTION";
                case "invalid-supply-aid":return "NPC_SUPPLY_AID_CONTENT";
                case "invalid-supply-aid-selection":return "NPC_SUPPLY_AID_SELECTION";
                case "invalid-call-pause":return "NPC_CALL_PAUSE_CONTENT";
                case "invalid-call-pause-selection":return "NPC_CALL_PAUSE_SELECTION";
                case "invalid-ready-patrol":return "NPC_READY_PATROL_CONTENT";
                case "invalid-ready-patrol-selection":return "NPC_READY_PATROL_SELECTION";
                case "invalid-quest-patrol":return "NPC_QUEST_PATROL_CONTENT";
                case "invalid-quest-patrol-selection":return "NPC_QUEST_PATROL_SELECTION";
                case "invalid-talk-pause":return "NPC_TALK_PAUSE_CONTENT";
                case "invalid-talk-pause-selection":return "NPC_TALK_PAUSE_SELECTION";
                case "invalid-patrol":return "NPC_PATROL_CONTENT";
                case "invalid-patrol-selection":return "NPC_PATROL_SELECTION";
                case "invalid-call-aid":return "NPC_CALL_AID_CONTENT";
                case "invalid-call-aid-selection":return "NPC_CALL_AID_SELECTION";
                default:return null;
            }
        }

        public IEnumerator Run()
        {
            room=FindFirstObjectByType<PlayRoom>();
            room.IsolatePhysicalInputForVerification=true;
            string selectionCase=Environment.GetEnvironmentVariable("REVERIE_UNITY_CASE");
            string expected=SelectionError(selectionCase);
            if(expected!=null) {
                float until=Time.realtimeSinceStartup+12;
                while(room.Failure==""&&Time.realtimeSinceStartup<until)yield return null;
                Check(room.Failure.Contains(expected),selectionCase+"_visible");
                Check(!room.HasBrainForVerification,selectionCase+"_no_child");
                Check(!File.Exists(Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING")),selectionCase+"_no_save");
                Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");
                Exit(failed?1:0);yield break;
            }
            if(Environment.GetEnvironmentVariable("REVERIE_UNITY_CASE")=="invalid-scenario") {
                float until=Time.realtimeSinceStartup+12;
                while(room.Failure==""&&Time.realtimeSinceStartup<until)yield return null;
                Check(room.Failure.Contains("UNKNOWN_SCENARIO"),"invalid_scenario_visible");
                Check(!room.HasBrainForVerification,"invalid_scenario_no_child");
                Check(!File.Exists(Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING")),"invalid_scenario_no_save");
                Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");
                Exit(failed?1:0);yield break;
            }

            if(Environment.GetEnvironmentVariable("REVERIE_UNITY_CASE")!="corrupt") {
                yield return Ready();if(failed){Exit(1);yield break;}
                Check(room.CanInspectMemory==room.NpcMemoryEnabled,"memory_control_mode");
                yield return InspectSlot("initial_slot_missing",null);
            }
            if(room.Latest!=null&&room.Latest.update.quest_id=="quest:harbor-sentinel") {
                if(room.NpcReadyPatrolEnabled){yield return ReadyPatrolFlow();yield break;}
                if(room.NpcCallPauseEnabled){yield return CallPausePatrolFlow();yield break;}
                if(room.NpcQuestPatrolEnabled){yield return QuestPatrolFlow();yield break;}
                if(room.NpcTalkPauseEnabled){yield return TalkPausePatrolFlow();yield break;}
                if(room.NpcPatrolEnabled){yield return PatrolFlow();yield break;}
                if(room.NpcCallAidEnabled){yield return CallAidFlow();yield break;}
                if(room.NpcSupplyAidEnabled){yield return SupplyAidFlow();yield break;}
                if(room.NpcAidEnabled){yield return AidFlow();yield break;}
                if(room.NpcCycleEnabled){yield return CycleFlow();yield break;}
                if(room.NpcWorkEnabled){yield return WorkFlow();yield break;}
                if(Environment.GetEnvironmentVariable("REVERIE_UNITY_EXPECT_MEMORY")=="1")
                    Check(room.NpcMemoryEnabled,"quest_memory_mode_forwarded");
                yield return QuestFlow();yield break;
            }
            string scenario=Environment.GetEnvironmentVariable("REVERIE_UNITY_SCENARIO");
            if(scenario=="harbor"||scenario=="grove") {
                yield return ScenarioFlow(scenario);yield break;
            }
            if(Environment.GetEnvironmentVariable("REVERIE_UNITY_CASE")=="corrupt") {
                float until=Time.realtimeSinceStartup+12;
                while(room.Failure==""&&Time.realtimeSinceStartup<until)yield return null;
                Check(room.Failure.Contains("SAVE_CORRUPT"),"corrupt_status_visible");
                Check(!room.CanSelectSlot&&!room.SelectSlot(7)&&room.SelectedSlot=="slot01",
                      "slots_failure_selection_disabled");
                Check(!room.CanSelectWaitDuration&&!room.SelectWaitDuration(3)&&room.SelectedWaitSeconds==1,
                      "wait_failure_selection_disabled");
                Debug.Log("CORRUPT_DIAGNOSTIC "+room.Failure);
                Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");
                Exit(failed?1:0);yield break;
            }
            yield return Ready();if(failed){Exit(1);yield break;}
            if(Environment.GetEnvironmentVariable("REVERIE_UNITY_CASE")=="courtyard") {
                yield return Courtyard();yield break;
            }
            Check(room.Latest.has_view&&room.Latest.narratives.Length==6,"catalog_loaded");
            Check(room.Latest.update.view.actor_cell=="0","initial_actor");
            string output=Path.Combine(Path.GetDirectoryName(
                Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING")),"evidence");
            Directory.CreateDirectory(output);
            yield return InspectLayout(output);
            if(!Application.isBatchMode) {
                ScreenCapture.CaptureScreenshot(Path.Combine(output,"initial-room.png"));
                yield return new WaitForSecondsRealtime(1);
                Check(File.Exists(Path.Combine(output,"initial-room.png")),"initial_door_enemy_capture");
            }
            string initial=JsonUtility.ToJson(room.Latest.update.view);
            yield return Intent("load");
            Check(JsonUtility.ToJson(room.Latest.update.view)==initial&&room.Latest.update.status=="SAVE_NOT_FOUND","failed_load_preserves_state");
            int originalPid=room.BrainProcessId;
            room.SendMalformedForVerification();yield return Ready();
            Check(room.TransportError=="INVALID_REQUEST"&&room.BrainProcessId==originalPid&&
                  JsonUtility.ToJson(room.Latest.update.view)==initial,"malformed_request_visible_child_alive");
            var changed=JsonUtility.FromJson<WireView>(initial);changed.width="4";
            bool rejected=false;
            try {room.ApplyForVerification(changed);}catch(IOException e) {rejected=e.Message=="PROTOTYPE_BOARD_BOUNDS";}
            Check(rejected,"changed_board_dimensions_rejected");
            changed=JsonUtility.FromJson<WireView>(initial);changed.walls=new [] {"2"};rejected=false;
            try {room.ApplyForVerification(changed);}catch(IOException e) {rejected=e.Message=="PROTOTYPE_BOARD_CHANGED";}
            Check(rejected,"changed_board_walls_rejected");
            yield return Intent("wait");
            Check(room.Latest.update.view.tick=="1","logical_time_advances");
            yield return Intent("bell");
            Check(room.Latest.update.view.npc_replies=="1","npc_reply_committed");
            yield return Intent("right");
            Check(room.Latest.update.view.actor_cell=="0","wall_blocks");
            yield return Intent("down");yield return Intent("right");
            Check(room.Latest.update.view.actor_cell=="3","door_blocks");
            yield return Intent("open");yield return Intent("right");yield return Intent("down");
            Check(room.Latest.update.view.actor_cell=="7","opened_door_passes");
            string beforeAttack=JsonUtility.ToJson(room.Latest.update.view);
            var afterAttack=JsonUtility.FromJson<WireView>(beforeAttack);
            afterAttack.actor_hp="2";afterAttack.enemy_hp="3";afterAttack.stamina="1";
            afterAttack.tick=(PlayRoom.Number(afterAttack.tick)+1).ToString();
            afterAttack.revision=(PlayRoom.Number(afterAttack.revision)+1).ToString();
            room.Send("attack");
            Check(room.Busy,"attack_in_flight_before_kill");
            System.Diagnostics.Process.GetProcessById(room.BrainProcessId).Kill();
            float crashLimit=Time.realtimeSinceStartup+12;
            while(room.Failure==""&&Time.realtimeSinceStartup<crashLimit)yield return null;
            Check(room.Failure!="","in_flight_disconnect_visible");
            room.Reconnect();yield return Ready();
            string resumed=JsonUtility.ToJson(room.Latest.update.view);
            Check(resumed==beforeAttack||resumed==JsonUtility.ToJson(afterAttack),"in_flight_pre_or_single_commit");
            if(resumed==beforeAttack)yield return Intent("attack");
            Check(room.Latest.update.view.actor_hp=="2"&&room.Latest.update.view.enemy_hp=="3"&&
                  room.Latest.update.view.stamina=="1","attack_and_counter");
            string saved=JsonUtility.ToJson(room.Latest.update.view);
            string savedTick=room.Latest.update.view.tick;
            yield return Intent("save");yield return InspectSlot("legacy_slot",savedTick);
            yield return Intent("attack");yield return Intent("load");
            Check(JsonUtility.ToJson(room.Latest.update.view)==saved,"load_restores");
            yield return Intent("attack");string once=JsonUtility.ToJson(room.Latest.update.view);
            yield return Intent("retry");
            Check(JsonUtility.ToJson(room.Latest.update.view)==once,"retry_no_duplicate");
            yield return Intent("rest");yield return Intent("attack");
            Check(room.Latest.update.view.enemy_hp=="0","enemy_defeated");
            yield return Intent("right");
            Check(room.Latest.update.view.actor_cell=="8","defeated_enemy_cell_passable");

            string committed=JsonUtility.ToJson(room.Latest.update.view);
            int childId=room.BrainProcessId;
            System.Diagnostics.Process.GetProcessById(childId).Kill();
            float disconnectStart=Time.realtimeSinceStartup;
            while(room.Failure==""&&Time.realtimeSinceStartup-disconnectStart<12)yield return null;
            Check(room.Failure!="","disconnect_visible");
            room.Reconnect();yield return Ready();
            Check(JsonUtility.ToJson(room.Latest.update.view)==committed,"reconnect_committed_branch");
            int oldTick=PlayRoom.Number(room.Latest.update.view.tick);
            yield return Intent("wait");
            Check(room.Latest.update.status=="COMMITTED"&&room.Latest.update.view.tick==(oldTick+1).ToString(),"input_after_reconnect");
            Directory.CreateDirectory(output);
            yield return SelectSlots(output);
            yield return SelectWait(output);
            if(!Application.isBatchMode) {
                ScreenCapture.CaptureScreenshot(Path.Combine(output,"playroom.png"));
                yield return new WaitForSecondsRealtime(2);
                Check(File.Exists(Path.Combine(output,"playroom.png")),"actual_screen_capture");
            }
            var frameTimes=new float[120];
            for(int i=0;i<frameTimes.Length;i++) {yield return null;frameTimes[i]=Time.unscaledDeltaTime;}
            Array.Sort(frameTimes);
            File.WriteAllText(Path.Combine(output,"performance.json"),
                "{\"frames\":120,\"median_ms\":"+(frameTimes[60]*1000).ToString(System.Globalization.CultureInfo.InvariantCulture)+
                ",\"p95_ms\":"+(frameTimes[114]*1000).ToString(System.Globalization.CultureInfo.InvariantCulture)+
                ",\"graphics_device\":\""+SystemInfo.graphicsDeviceName+"\",\"batch_mode\":"+
                (Application.isBatchMode?"true":"false")+"}");
            File.WriteAllText(Path.Combine(output,"final-view.json"),JsonUtility.ToJson(room.Latest));
            Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");
            Exit(failed?1:0);
        }
    }
}

#endif
