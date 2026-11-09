using System;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace ReverieSaga
{
    internal sealed class SeededVillageWindow : EditorWindow
    {
        string seed;

        [MenuItem("Reverie/시드로 새 마을 열기")]
        static void Open()
        {
            var window = GetWindow<SeededVillageWindow>(true, "시드로 새 마을 열기");
            window.seed = NewSeed();
            window.minSize = new Vector2(490, 100);
        }

        static string NewSeed() => Guid.NewGuid().ToString("N") + Guid.NewGuid().ToString("N");

        void OnGUI()
        {
            seed = EditorGUILayout.TextField("시드", seed ?? "");
            if (GUILayout.Button("새 시드 만들기"))
                seed = NewSeed();
            using (new EditorGUI.DisabledScope(!Regex.IsMatch(seed, VillageLayout.SeedPattern)))
                if (GUILayout.Button("이 시드로 열기"))
                {
                    WorldVillageWindow.OpenSeeded(seed);
                    Close();
                }
        }
    }
}
