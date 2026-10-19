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

        IEnumerator InspectMemory(string label,int count)
        {
            yield return InspectMemorySelection(label,count,false);
            yield return InspectMemorySelection(label+"_recent",count==0?0:1,true);
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

        IEnumerator InspectMemorySelection(string label,int count,bool recent)
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
                after.messages.Length==count&&after.messages[0].Contains("2초:")&&
                after.messages[0].Contains("직접 들었습니다")&&
                (count==1||after.messages[1].Contains("12초:")&&
                 after.messages[1].Contains("완료 보고를 받았습니다")&&
                 after.messages[1].Contains("직접 본 기억은 아닙니다"));
            if(recent&&count!=0) {
                bool reported=before.quest_stage=="3";
                expected=after.messages.Length==1&&text.StartsWith("최근 NPC 대화 기억")&&
                    (reported?text.Contains("12초:")&&text.Contains("완료 보고를 받았습니다")&&
                              text.Contains("직접 본 기억은 아닙니다"):
                              text.Contains("2초:")&&text.Contains("직접 들었습니다"));
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

        public IEnumerator Run()
        {
            room=FindFirstObjectByType<PlayRoom>();
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
