#if UNITY_EDITOR || DEVELOPMENT_BUILD
using System;
using System.Collections;
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
            EditorApplication.Exit(code);
#else
            Application.Quit(code);
#endif
        }
        PlayRoom room;
        bool failed;
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

        public IEnumerator Run()
        {
            room=FindFirstObjectByType<PlayRoom>();
            if(Environment.GetEnvironmentVariable("REVERIE_UNITY_CASE")=="corrupt") {
                float until=Time.realtimeSinceStartup+12;
                while(room.Failure==""&&Time.realtimeSinceStartup<until)yield return null;
                Check(room.Failure.Contains("SAVE_CORRUPT"),"corrupt_status_visible");
                Debug.Log("CORRUPT_DIAGNOSTIC "+room.Failure);
                Debug.Log(failed?"ENGINE_VERIFY_FAILED":"ENGINE_VERIFY_PASSED");
                Exit(failed?1:0);yield break;
            }
            yield return Ready();if(failed){Exit(1);yield break;}
            Check(room.Latest.has_view&&room.Latest.narratives.Length==6,"catalog_loaded");
            Check(room.Latest.update.view.actor_cell=="0","initial_actor");
            string output=Path.GetFullPath(Path.Combine(Application.dataPath,"..","..","..","tmp","cp04-native"));
            Directory.CreateDirectory(output);
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
            yield return Intent("save");yield return Intent("attack");yield return Intent("load");
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
