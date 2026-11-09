using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace ReverieSaga
{
    internal sealed class Village3DPreview : IDisposable
    {
        const string Art = "Assets/Reverie/VillageArt/";
        const string Rig = "Assets/Reverie/LocalVillageArt/";
        internal const string RigInstructions = "3D 모델 준비: LocalVillageArt에 Y Bot 및 검·방패 FBX 3개를 넣어 주세요.";
        const float StrikeSeconds = .54f;
        const float BodyGap = .035f;
        static readonly Vector3 DungeonOffset = new Vector3(64, 0, 0);
        readonly Scene scene;
        readonly Camera camera;
        readonly RenderTexture target;
        readonly List<Material> materials = new List<Material>();
        readonly Dictionary<string, GameObject> residents = new Dictionary<string, GameObject>();
        readonly GameObject model;
        readonly AnimationClip idle;
        readonly AnimationClip strike;
        readonly GameObject player;
        readonly GameObject bandit;
        readonly GameObject playerRig;
        readonly Vector3 rigRestPosition;
        readonly Quaternion rigRestRotation;
        readonly Vector3 rigRestScale;
        readonly Transform hips;
        readonly Vector3 hipsRest;
        readonly VillageBodyProfile idleBody;
        readonly VillageBodyProfile strikeBody;
        readonly Transform swordTip;
        readonly LineRenderer trail;
        readonly GameObject spark;
        readonly Material sparkMaterial;
        readonly Material blue;
        readonly Material red;
        GameObject dungeonOrc;
        Bounds orcBody;
        Vector3 orcRestPosition;
        readonly Queue<(float time, Vector3 position)> dungeonTrail = new();
        Vector3 heading = Vector3.forward;
        double hitAt = double.NegativeInfinity;
        bool playerHit;
        bool pommelHit;

        internal static bool HasRig =>
            AssetDatabase.LoadAssetAtPath<GameObject>(Rig + "Y Bot.fbx") != null &&
            Clip("Idle") != null && Clip("Attack") != null;

        static AnimationClip Clip(string action) => AssetDatabase.LoadAllAssetsAtPath(
            Rig + "Y Bot@Sword And Shield " + action + ".fbx").OfType<AnimationClip>()
            .FirstOrDefault(clip => !clip.name.StartsWith("__preview__", StringComparison.Ordinal));

        internal Village3DPreview(string[] rows, VillageLayout layout)
        {
            model = AssetDatabase.LoadAssetAtPath<GameObject>(Rig + "Y Bot.fbx");
            idle = Clip("Idle");
            strike = Clip("Attack");
            scene = EditorSceneManager.NewPreviewScene();
            try
            {
                camera = Make("Pixel camera").AddComponent<Camera>();
                camera.scene = scene;
                camera.enabled = false;
                camera.orthographic = true;
                camera.orthographicSize = 2.85f;
                camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = new Color(.12f, .19f, .24f);
                camera.allowHDR = camera.allowMSAA = false;
                target = new RenderTexture(320, 180, 24)
                    { filterMode = FilterMode.Point, name = "Mulbeodeul 320x180" };
                camera.targetTexture = target;
                Light(new Vector3(47, -30, 0), new Color(1f, .88f, .72f), 1.0f);
                Light(new Vector3(22, 145, 0), new Color(.62f, .79f, 1f), .55f);
                var town = Material("Standard", Color.white);
                town.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(Art + "colormap.png");
                BuildTown(rows, layout, town);
                BuildDungeon(layout);
                blue = Material("Standard", new Color(.24f, .62f, 1f));
                red = Material("Standard", new Color(.89f, .30f, .20f));
                player = Actor("Player", blue, out playerRig);
                bandit = Actor("Bandit", red, out _);
                rigRestPosition = playerRig.transform.localPosition;
                rigRestRotation = playerRig.transform.localRotation;
                rigRestScale = playerRig.transform.localScale;
                var playerBody = playerRig.GetComponentsInChildren<SkinnedMeshRenderer>();
                if (playerBody.Length == 0)
                    throw new InvalidOperationException("Y Bot skinned mesh missing");
                var bones = playerRig.GetComponentsInChildren<Transform>();
                hips = bones.FirstOrDefault(bone => bone.name.EndsWith("Hips", StringComparison.Ordinal));
                var hand = bones.FirstOrDefault(bone => bone.name.EndsWith("RightHand", StringComparison.Ordinal));
                if (hips == null || hand == null)
                    throw new InvalidOperationException("Y Bot hips or right hand missing");
                hipsRest = player.transform.InverseTransformPoint(hips.position);
                idleBody = new VillageBodyProfile(player.transform, playerBody, t => SampleDungeonPose(idle, t));
                strikeBody = new VillageBodyProfile(player.transform, playerBody, t => SampleDungeonPose(strike, t));
                var sword = Make("Sword grip");
                sword.transform.SetParent(hand, false);
                sword.transform.localPosition = new Vector3(0, .07f, 0);
                var blade = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "sword.fbx");
                if (blade == null)
                    throw new InvalidOperationException("Sword model missing");
                var steel = Material("Standard", Color.white);
                steel.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(Art + "sword-colormap.png");
                var swordModel = Fit(blade, Vector3.zero, .65f, steel, sword.transform);
                swordTip = Make("Sword tip").transform;
                swordTip.SetParent(swordModel.transform, false);
                swordTip.position = sword.transform.TransformPoint(0, .62f, 0);
                trail = Make("Sword trail").AddComponent<LineRenderer>();
                trail.sharedMaterial = Material("Sprites/Default", Color.white);
                trail.startColor = new Color(.46f, .82f, 1f, 0);
                trail.endColor = new Color(.87f, .97f, 1f);
                trail.startWidth = .02f;
                trail.endWidth = .09f;
                trail.numCapVertices = 2;
                trail.enabled = false;
                sparkMaterial = Material("Sprites/Default", Color.white);
                sparkMaterial.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(Art + "spark_01.png");
                spark = Primitive("Hit spark", PrimitiveType.Quad, Vector3.zero, Vector3.one, sparkMaterial);
                spark.SetActive(false);
            }
            catch
            {
                Dispose();
                throw;
            }
        }

        GameObject Make(string name)
        {
            var go = new GameObject(name);
            SceneManager.MoveGameObjectToScene(go, scene);
            return go;
        }

        Material Material(string shader, Color color)
        {
            var material = new Material(Shader.Find(shader)) { color = color };
            materials.Add(material);
            return material;
        }

        void Light(Vector3 rotation, Color color, float intensity)
        {
            var light = Make("Lane light").AddComponent<Light>();
            light.type = LightType.Directional;
            light.color = color;
            light.intensity = intensity;
            light.transform.rotation = Quaternion.Euler(rotation);
        }

        GameObject Primitive(string name, PrimitiveType shape, Vector3 position, Vector3 scale, Material material)
        {
            var go = GameObject.CreatePrimitive(shape);
            go.name = name;
            SceneManager.MoveGameObjectToScene(go, scene);
            go.transform.SetPositionAndRotation(position, Quaternion.identity);
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = material;
            Object.DestroyImmediate(go.GetComponent<Collider>());
            return go;
        }

        GameObject Fit(GameObject asset, Vector3 position, float size, Material material, Transform parent,
            bool horizontal = false)
        {
            var go = Object.Instantiate(asset);
            SceneManager.MoveGameObjectToScene(go, scene);
            var renderers = go.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0)
                throw new InvalidOperationException("No mesh: " + asset.name);
            var bounds = renderers[0].bounds;
            foreach (var renderer in renderers)
            {
                bounds.Encapsulate(renderer.bounds);
                if (material != null)
                    renderer.sharedMaterials = renderer.sharedMaterials.Select(_ => material).ToArray();
            }
            float span = horizontal ? Mathf.Max(bounds.size.x, bounds.size.z) : bounds.size.y;
            float scale = size / Mathf.Max(.001f, span);
            go.transform.SetParent(parent, false);
            go.transform.localScale *= scale;
            go.transform.localPosition = position - scale * new Vector3(bounds.center.x, bounds.min.y, bounds.center.z);
            return go;
        }

        GameObject Actor(string name, Material material, out GameObject rig)
        {
            var actor = Make(name);
            rig = Fit(model, Vector3.zero, 1.14f, material, actor.transform);
            return actor;
        }

        internal static Vector3 Tile(float x, float y) => new Vector3(x, 0, -y);

        void BuildTown(string[] rows, VillageLayout layout, Material material)
        {
            var grass = Material("Standard", layout.terrain.Contains("범람원") ?
                new Color(.21f, .30f, .19f) : new Color(.28f, .30f, .22f));
            var roads = new[] { new Color(.45f, .31f, .22f), new Color(.51f, .40f, .32f),
                new Color(.48f, .36f, .28f) }.Select(color => Material("Standard", color)).ToArray();
            var walls = new[] { new Color(.65f, .45f, .31f), new Color(.54f, .39f, .30f),
                new Color(.70f, .55f, .37f) }.Select(color => Material("Standard", color)).ToArray();
            int width = rows[0].Length;
            Primitive("Ground", PrimitiveType.Cube, Tile((width - 1) * .5f, (rows.Length - 1) * .5f)
                + Vector3.down * .14f, new Vector3(width + 5, .24f, rows.Length + 4), grass);
            var wall = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "wall.fbx");
            var door = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "wall-wood-door.fbx");
            var roof = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "roof.fbx");
            var tree = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "tree.fbx");
            var rock = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "rock-small.fbx");
            var gate = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "dungeon-gate.fbx");
            var dungeonMaterial = Material("Standard", Color.white);
            dungeonMaterial.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(Art + "sword-colormap.png");
            foreach (var item in layout.village)
            {
                var tile = Tile(item.x, item.y);
                switch (item.kind)
                {
                    case "road":
                        Primitive("Path", PrimitiveType.Cube, tile + Vector3.down * .04f,
                            new Vector3(.99f, .08f, .99f), roads[item.variant]);
                        break;
                    case "wall":
                        Fit(wall, tile, .65f, material, null);
                        break;
                    case "house":
                        var facing = Quaternion.Euler(0, -90f * item.facing, 0);
                        float height = .78f + .06f * item.variant;
                        Primitive("Building body", PrimitiveType.Cube, tile + Vector3.up * .43f,
                            new Vector3(.86f, height, .82f), walls[item.variant]);
                        Fit(door, tile + facing * Vector3.back * .43f, height, material, null)
                            .transform.rotation = facing;
                        Fit(roof, tile + Vector3.up * height, .35f, material, null)
                            .transform.rotation = facing;
                        break;
                    case "gate":
                        var entrance = Fit(gate, tile, 1.18f, dungeonMaterial, null);
                        entrance.transform.rotation = Quaternion.Euler(0, 180, 0);
                        entrance.name = "Dungeon entrance";
                        break;
                    case "tree":
                        Fit(tree, tile, .9f, material, null);
                        break;
                    case "rock":
                        Fit(rock, tile, .22f, material, null);
                        break;
                }
            }
        }

        void BuildDungeon(VillageLayout layout)
        {
            var material = Material("Standard", Color.white);
            material.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(Art + "sword-colormap.png");
            var wall = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "dungeon-wall.fbx");
            var orc = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "dungeon-orc.fbx");
            var floors = new[] {
                AssetDatabase.LoadAssetAtPath<GameObject>(Art + "dungeon-floor.fbx"),
                AssetDatabase.LoadAssetAtPath<GameObject>(Art + "dungeon-floor-detail.fbx")
            };
            foreach (var item in layout.dungeon)
            {
                var tile = DungeonOffset + Tile(item.x, item.y);
                if (item.kind == "orc")
                {
                    dungeonOrc = Fit(orc, tile + Vector3.up * .14f, 1.05f, material, null);
                    dungeonOrc.name = "Dungeon orc";
                    orcRestPosition = dungeonOrc.transform.position;
                    orcBody = VillageBodyProfile.RestBounds(dungeonOrc);
                    continue;
                }
                Fit(floors[item.variant], tile, 1f, material, null, horizontal: true);
                if (item.kind == "dungeon-wall")
                {
                    var piece = Fit(wall, tile + Vector3.up * .12f, .85f, material, null);
                    if (item.x == 0 || item.x == VillageLayout.RoomSize - 1)
                        piece.transform.rotation = Quaternion.Euler(0, 90, 0);
                }
            }
        }

        internal void Hit(bool playerAttacked, double now, bool pommel = false)
        {
            hitAt = now;
            playerHit = playerAttacked;
            pommelHit = pommel;
            dungeonTrail.Clear();
        }

        internal bool IsPlaying(double now) => now - hitAt < StrikeSeconds;
        internal bool ShowDefeated(double now) => playerHit && IsPlaying(now);

        internal void SetResident(string id, int x, int y)
        {
            if (!residents.TryGetValue(id, out var resident))
            {
                resident = Actor(id, blue, out _);
                residents.Add(id, resident);
            }
            resident.transform.position = Tile(x, y);
        }

        void SampleDungeonPose(AnimationClip clip, float normalized)
        {
            clip.SampleAnimation(playerRig, normalized * clip.length);
            playerRig.transform.SetLocalPositionAndRotation(rigRestPosition, rigRestRotation);
            playerRig.transform.localScale = rigRestScale;
            var root = player.transform;
            var motion = root.InverseTransformPoint(hips.position);
            hips.position = root.TransformPoint(hipsRest.x, motion.y, hipsRest.z);
        }

        void SeparateDungeonBodies(Vector3 axis, Vector3 origin, Bounds playerBox)
        {
            float nearOrc = Vector3.Dot(dungeonOrc.transform.position + orcBody.center - origin, axis) -
                VillageBodyProfile.Radius(orcBody.extents, axis);
            var root = player.transform;
            float nearPlayer = Vector3.Dot(root.TransformPoint(playerBox.center) - origin, axis) +
                VillageBodyProfile.Radius(playerBox.extents, root.InverseTransformDirection(axis));
            player.transform.position -= axis * Mathf.Max(0, nearPlayer - nearOrc + BodyGap);
        }

        void PoseDungeon(Vector3 feet, Vector3 opponent, bool showOrc, bool swinging,
            float elapsed, float impact, double now)
        {
            dungeonOrc.SetActive(showOrc);
            dungeonOrc.transform.position = orcRestPosition;
            float progress = Mathf.Clamp01(elapsed / StrikeSeconds);
            float idleSeconds = Mathf.Max(.01f, idle.length);
            float pose = swinging ? (pommelHit ? .45f * Mathf.Sin(progress * Mathf.PI) : progress) :
                (float)(now % idleSeconds / idleSeconds);
            SampleDungeonPose(swinging ? strike : idle, pose);

            var axis = (opponent - feet).normalized;
            if (showOrc && axis.sqrMagnitude > .01f)
            {
                if (impact >= 0 && impact < .24f)
                {
                    float recoil = Mathf.Sin(Mathf.PI * impact / .24f);
                    player.transform.position -= axis * (recoil * (playerHit ? .045f : .12f));
                    dungeonOrc.transform.position += axis * (recoil * (playerHit ? .12f : .045f));
                }
                SeparateDungeonBodies(axis, feet, (swinging ? strikeBody : idleBody).At(pose));
            }

            if (swinging && !pommelHit)
            {
                while (dungeonTrail.Count > 0 && elapsed - dungeonTrail.Peek().time > .15f)
                    dungeonTrail.Dequeue();
                dungeonTrail.Enqueue((elapsed, swordTip.position));
                trail.enabled = elapsed >= .10f && dungeonTrail.Count > 1;
                if (trail.enabled)
                {
                    trail.positionCount = dungeonTrail.Count;
                    int i = 0;
                    foreach (var point in dungeonTrail)
                        trail.SetPosition(i++, point.position);
                }
            }
            else
                trail.enabled = false;
        }

        internal RenderTexture Render(Vector2 point, Vector2 direction, bool walking,
            bool visible, bool showBandit, Vector2 banditTile, double now, bool dungeon = false)
        {
            var offset = dungeon ? DungeonOffset + Vector3.up * .14f : Vector3.zero;
            var feet = offset + Tile(point.x, point.y);
            var opponent = offset + Tile(banditTile.x, banditTile.y);
            if (direction.sqrMagnitude > .01f)
                heading = Tile(direction.x, direction.y).normalized;
            if (showBandit && (opponent - feet).sqrMagnitude > .01f)
                heading = (opponent - feet).normalized;
            player.SetActive(visible);
            bandit.SetActive(visible && showBandit && !dungeon);
            foreach (var resident in residents.Values)
                resident.SetActive(visible && !dungeon);
            player.transform.SetPositionAndRotation(feet, Quaternion.LookRotation(heading));
            bandit.transform.position = opponent;
            float elapsed = (float)(now - hitAt);
            float impact = elapsed - (playerHit ? (pommelHit ? .17f : .25f) : .06f);
            bool swinging = playerHit && elapsed < StrikeSeconds;
            trail.enabled = swinging && elapsed >= .10f;
            if (dungeon)
                PoseDungeon(feet, opponent, showBandit, swinging, elapsed, impact, now);
            else if (swinging)
            {
                trail.positionCount = 8;
                for (int i = 0; i < 8; i++)
                {
                    float sample = Mathf.Clamp01((elapsed - .15f * (7 - i) / 7) / StrikeSeconds);
                    strike.SampleAnimation(playerRig, sample * strike.length);
                    trail.SetPosition(i, swordTip.position);
                }
            }
            else if (visible)
            {
                idle.SampleAnimation(playerRig, (float)(now % Mathf.Max(.01f, idle.length)));
                if (walking)
                    player.transform.position += Vector3.up * (.04f * Mathf.Abs(Mathf.Sin((float)now * 30)));
            }
            var focus = DungeonOffset + Tile(2, 2);
            if (!dungeon)
            {
                focus = Vector3.Lerp(feet, opponent, showBandit ? .38f : 0);
                focus.x = Mathf.Clamp(focus.x, 3.4f, 9.5f);
                focus.z = Mathf.Clamp(focus.z, -6.2f, -1.8f);
            }
            camera.transform.position = focus + (dungeon ? new Vector3(2.4f, 6.2f, -6.1f) :
                new Vector3(1.7f, 5.6f, -7.2f));
            camera.transform.LookAt(focus + Vector3.up * .2f);
            spark.SetActive(visible && impact >= 0 && impact < .24f);
            if (spark.activeSelf)
            {
                var struck = playerHit ? opponent : feet;
                if (dungeon)
                    struck = Vector3.Lerp(player.transform.position, dungeonOrc.transform.position,
                        playerHit ? .78f : .22f);
                spark.transform.position = struck + Vector3.up * .78f;
                spark.transform.rotation = camera.transform.rotation;
                spark.transform.localScale = Vector3.one * (.58f + 3 * impact);
                sparkMaterial.color = new Color(1f, pommelHit ? .93f : .73f,
                    pommelHit ? .68f : .26f, 1f - impact / .24f);
            }
            camera.Render();
            return target;
        }

        public void Dispose()
        {
            if (target != null)
            {
                target.Release();
                Object.DestroyImmediate(target);
            }
            if (scene.IsValid())
                EditorSceneManager.ClosePreviewScene(scene);
            foreach (var material in materials)
                Object.DestroyImmediate(material);
        }
    }
}
