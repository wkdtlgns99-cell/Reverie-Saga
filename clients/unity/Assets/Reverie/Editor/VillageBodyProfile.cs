using System;
using UnityEngine;
using Object = UnityEngine.Object;

namespace ReverieSaga
{
    // Sample editor assets when the preview opens. Frame rendering only reads two boxes.
    internal sealed class VillageBodyProfile
    {
        const int Intervals = 48;
        const float SamplePadding = .02f;
        readonly Bounds[] poses = new Bounds[Intervals + 1];

        internal VillageBodyProfile(Transform root, SkinnedMeshRenderer[] skins, Action<float> sample)
        {
            var mesh = new Mesh();
            try
            {
                for (int i = 0; i <= Intervals; i++)
                {
                    sample((float)i / Intervals);
                    for (int j = 0; j < skins.Length; j++)
                    {
                        var box = Measure(skins[j], mesh, root.worldToLocalMatrix);
                        if (j == 0) poses[i] = box;
                        else poses[i].Encapsulate(box);
                    }
                }
            }
            finally
            {
                Object.DestroyImmediate(mesh);
            }
        }

        internal static Bounds RestBounds(GameObject actor)
        {
            var worldToOffset = Matrix4x4.Translate(-actor.transform.position);
            var mesh = new Mesh();
            Bounds? combined = null;
            try
            {
                foreach (var renderer in actor.GetComponentsInChildren<Renderer>())
                {
                    var box = renderer is SkinnedMeshRenderer skin ? Measure(skin, mesh, worldToOffset) :
                        TransformBounds(renderer.bounds, worldToOffset);
                    if (combined.HasValue)
                        box.Encapsulate(combined.Value);
                    combined = box;
                }
            }
            finally
            {
                Object.DestroyImmediate(mesh);
            }
            return combined ?? throw new InvalidOperationException("Actor mesh missing");
        }

        internal Bounds At(float normalized)
        {
            int first = Mathf.Clamp(Mathf.FloorToInt(normalized * Intervals), 0, Intervals - 1);
            var box = poses[first];
            box.Encapsulate(poses[first + 1]);
            box.Expand(SamplePadding * 2);
            return box;
        }

        internal static float Radius(Vector3 extents, Vector3 axis) =>
            extents.x * Mathf.Abs(axis.x) + extents.y * Mathf.Abs(axis.y) + extents.z * Mathf.Abs(axis.z);

        static Bounds Measure(SkinnedMeshRenderer skin, Mesh scratch, Matrix4x4 worldToRoot)
        {
            skin.BakeMesh(scratch, false);
            return TransformBounds(scratch.bounds, worldToRoot * skin.localToWorldMatrix);
        }

        static Bounds TransformBounds(Bounds box, Matrix4x4 localToRoot)
        {
            var projection = localToRoot.transpose;
            return new Bounds(localToRoot.MultiplyPoint3x4(box.center), 2 * new Vector3(
                Radius(box.extents, projection.MultiplyVector(Vector3.right)),
                Radius(box.extents, projection.MultiplyVector(Vector3.up)),
                Radius(box.extents, projection.MultiplyVector(Vector3.forward))));
        }
    }
}
