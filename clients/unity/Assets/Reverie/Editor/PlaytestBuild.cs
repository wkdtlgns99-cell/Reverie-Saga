using System;
using System.Collections;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace ReverieSaga
{
    public static class PlaytestBuild
    {
        public static void Prepare()
        {
            Directory.CreateDirectory("Assets/Reverie/Scenes");
            Directory.CreateDirectory("Assets/Reverie/Resources");
            AssetDatabase.Refresh();
            string materialPath="Assets/Reverie/Resources/Placeholder.mat";
            if(AssetDatabase.LoadAssetAtPath<Material>(materialPath)==null) {
                var shader=Shader.Find("Unlit/Color");
                if(shader==null)throw new IOException("Editor placeholder shader unavailable");
                AssetDatabase.CreateAsset(new Material(shader),materialPath);
            }
            var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var room=new GameObject("Reverie Play Room");room.AddComponent<PlayRoom>();
            EditorSceneManager.SaveScene(scene,"Assets/Reverie/Scenes/PlayRoom.unity");
            EditorBuildSettings.scenes=new [] {
                new EditorBuildSettingsScene("Assets/Reverie/Scenes/PlayRoom.unity",true)
            };
            PlayerSettings.productName="Reverie Saga Playtest";
            PlayerSettings.companyName="Reverie Saga";
            PlayerSettings.runInBackground=true;
            PlayerSettings.defaultScreenWidth=1280;PlayerSettings.defaultScreenHeight=720;
            AssetDatabase.SaveAssets();
        }

        public static void Build()
        {
            Prepare();
            string output=Path.GetFullPath(Path.Combine(Application.dataPath,"..","..","..","tmp","unity-build","ReverieSaga.exe"));
            Directory.CreateDirectory(Path.GetDirectoryName(output));
            var report=BuildPipeline.BuildPlayer(new [] {"Assets/Reverie/Scenes/PlayRoom.unity"},output,
                BuildTarget.StandaloneWindows64,BuildOptions.None);
            if(report.summary.result!=UnityEditor.Build.Reporting.BuildResult.Succeeded)
                throw new IOException("Native player build failed: "+report.summary.result);
            var assembly=System.Reflection.Assembly.ReflectionOnlyLoadFrom(
                Path.Combine(Path.GetDirectoryName(output),"ReverieSaga_Data","Managed","Assembly-CSharp.dll"));
            if(assembly.GetType("ReverieSaga.LiveVerification",false)!=null)
                throw new IOException("Release contains verification hook");
            Debug.Log("RELEASE_VERIFICATION_HOOK_ABSENT");
            Debug.Log("ENGINE_BUILD_PASSED bytes="+report.summary.totalSize);
        }

        public static void BuildAndVerify() { Build(); Verify(); }

        public static void Verify()
        {
            string working=Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING");
            if(String.IsNullOrEmpty(working))throw new IOException("Verification requires a fresh working directory");
            string parent=Path.GetDirectoryName(Path.GetFullPath(working));
            if(Directory.Exists(parent)&&Directory.GetFileSystemEntries(parent).Length!=0)
                throw new IOException("Verification directory must be empty;existing saves are preserved");
            Prepare();
            SessionState.SetBool("Reverie.Verify",true);
            if(!Application.isBatchMode)EditorApplication.ExecuteMenuItem("Window/General/Game");
            EditorApplication.isPlaying=true;
        }

        public static void VerifyCorrupt()
        {
            Verify();
            string working=Environment.GetEnvironmentVariable("REVERIE_UNITY_WORKING");
            Directory.CreateDirectory(Path.GetDirectoryName(working));
            File.WriteAllBytes(working,new byte[]{1,2,3,4});
        }

        public static void VerifyCourtyard()
        {
            if(Environment.GetEnvironmentVariable("REVERIE_UNITY_SCENARIO")!=WireScenarios.Courtyard)
                throw new IOException("Courtyard verification requires the selected scenario");
            Environment.SetEnvironmentVariable("REVERIE_UNITY_CASE","courtyard");
            Verify();
        }

        public static void VerifyInvalidScenario()
        {
            string selected=Environment.GetEnvironmentVariable("REVERIE_UNITY_SCENARIO");
            if(String.IsNullOrEmpty(selected)||selected==WireScenarios.Legacy||selected==WireScenarios.Courtyard)
                throw new IOException("Invalid-scenario verification requires an unknown ID");
            Environment.SetEnvironmentVariable("REVERIE_UNITY_CASE","invalid-scenario");
            Verify();
        }

        [InitializeOnLoadMethod]
        static void Initialize() { EditorApplication.playModeStateChanged+=Changed; }

        static void Changed(PlayModeStateChange state)
        {
            if(state!=PlayModeStateChange.EnteredPlayMode||!SessionState.GetBool("Reverie.Verify",false))return;
            SessionState.SetBool("Reverie.Verify",false);
            EditorApplication.playModeStateChanged-=Changed;
            var runner=new GameObject("Verification Runner").AddComponent<LiveVerification>();
            runner.StartCoroutine(runner.Run());
        }
    }

}
