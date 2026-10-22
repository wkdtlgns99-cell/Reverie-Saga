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
                JsonUtility.ToJson(room.Latest.update.view)==resumedView&&room.NpcMemoryEnabled&&room.NpcWorkEnabled,
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
