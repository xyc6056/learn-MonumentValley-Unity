using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// Runtime-only compatibility layer for the game second level, Scene 2.
/// It keeps the serialized scene untouched and recreates the SampleScene
/// behavior for the renamed l_1 nodes.
/// </summary>
public sealed class RecoveredSceneSampleAdapter : MonoBehaviour
{
    private const string TargetSceneName = "Scene 2";
    private const string Chain19Name = "l_1 (19)";
    private const string Chain21Name = "l_1 (21)";
    private const string Chain22Name = "l_1 (22)";
    private const string Node24Name = "l_1 (24)";
    private const string Node25Name = "l_1 (25)";
    private const string Node0Name = "0";
    private const string Node18FinalName = "18final";
    private const string MovingNodeName = "l_1 (28)";

    private const float ScreenAlignmentThresholdRatio = 0.065f;
    private const float MinimumWorldGap = 0.75f;
    private static readonly Color SpecificPink = new Color(.90f, .36f, .72f, 1f);

    private static readonly Vector3 Sample13LocalPosition = new Vector3(0f, 6f, 4f);
    private static readonly Vector3 Sample14LocalPosition = new Vector3(0f, 6f, 5f);
    private static readonly Vector3 Sample15LocalPosition = new Vector3(0f, 6f, 6f);

    private readonly List<Walkable> chainNodes = new List<Walkable>();
    private readonly List<Walkable> alignmentNodes = new List<Walkable>();
    private readonly List<Walkable> movingNodes = new List<Walkable>();
    private Camera viewCamera;
    private Walkable chain19;
    private Walkable chain21;
    private Walkable chain22;
    private Walkable node24;
    private Walkable node25;
    private Walkable node0;
    private Walkable node18Final;
    private Walkable node16;
    private Walkable p1;
    private Walkable p2;
    private Walkable p3;
    private Walkable activeSource;
    private Walkable activeTarget;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    private static void Install()
    {
        SceneManager.sceneLoaded -= HandleSceneLoaded;
        SceneManager.sceneLoaded += HandleSceneLoaded;
    }

    private static void HandleSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        if (scene.name != TargetSceneName)
            return;

        if (FindObjectOfType<RecoveredSceneSampleAdapter>() != null)
            return;

        GameObject adapterObject = new GameObject("[Recovered Scene Sample Adapter]");
        adapterObject.hideFlags = HideFlags.DontSave;
        SceneManager.MoveGameObjectToScene(adapterObject, scene);
        adapterObject.AddComponent<RecoveredSceneSampleAdapter>();
    }

    private void Awake()
    {
        if (gameObject.scene.name != TargetSceneName)
        {
            Destroy(gameObject);
            return;
        }

        ResolveNodes();
        EnsureSampleRelationships();
        ApplySampleSceneFlags();
        NormalizeMovingLinks();
        KeepPermanentMovingConnections();
    }

    private void Start()
    {
        ApplySpecificPinkNodes();
    }
    private void LateUpdate()
    {
        KeepPermanentMovingConnections();
        SetPair(chain19, node25, false);
        SetPair(node25, node18Final, false);
        SetPair(node0, node18Final, false);
        MirrorConditionalLinks();

        if (viewCamera == null)
            viewCamera = Camera.main;

        UpdateVisualIllusionLink();
    }

    private void ApplySpecificPinkNodes()
    {
        Walkable[] allNodes = FindObjectsOfType<Walkable>();
        for (int i = 0; i < allNodes.Length; i++)
        {
            Walkable node = allNodes[i];
            if (node == null || !IsSpecificPinkNode(node.name))
                continue;

            MeshRenderer[] renderers = node.GetComponentsInChildren<MeshRenderer>(true);
            for (int j = 0; j < renderers.Length; j++)
            {
                MeshRenderer renderer = renderers[j];
                if (renderer == null || renderer.sharedMaterials == null)
                    continue;

                Material[] materials = renderer.sharedMaterials;
                for (int k = 0; k < materials.Length; k++)
                {
                    Material source = materials[k];
                    if (source == null || !source.HasProperty("_Color"))
                        continue;

                    Material pinkMaterial = new Material(source);
                    pinkMaterial.color = SpecificPink;
                    materials[k] = pinkMaterial;
                }

                renderer.sharedMaterials = materials;
            }
        }
    }

    private static bool IsSpecificPinkNode(string nodeName)
    {
        return nodeName == "l_1 (24)" ||
               nodeName == "l_1 (25)" ||
               nodeName == "l_1 (26)" ||
               nodeName == "l_1 (27)" ||
               nodeName == "l_1 (28)";
    }
    private void ResolveNodes()
    {
        chain19 = FindClosestExpected(Chain19Name, Sample13LocalPosition);
        chain21 = FindClosestExpected(Chain21Name, Sample14LocalPosition);
        chain22 = FindClosestExpected(Chain22Name, Sample15LocalPosition);
        node24 = FindSingleNode(Node24Name);
        node25 = FindSingleNode(Node25Name);
        node0 = FindSingleNode(Node0Name);
        node18Final = FindSingleNode(Node18FinalName);
        node16 = FindSingleNode("16");
        p1 = FindSingleNode("p1");
        p2 = FindSingleNode("p2");
        p3 = FindSingleNode("p3");

        alignmentNodes.Clear();
        AddIfNotNull(alignmentNodes, p1);
        AddIfNotNull(alignmentNodes, p2);
        AddIfNotNull(alignmentNodes, p3);

        chainNodes.Clear();
        AddIfNotNull(chainNodes, chain19);
        AddIfNotNull(chainNodes, chain21);
        AddIfNotNull(chainNodes, chain22);

        movingNodes.Clear();
        Walkable[] allNodes = FindObjectsOfType<Walkable>();
        for (int i = 0; i < allNodes.Length; i++)
        {
            Walkable node = allNodes[i];
            if (node != null && node.name == MovingNodeName)
                movingNodes.Add(node);
        }

        if (chain19 != null && chain21 != null)
            SetPair(chain19, chain21, true);

        if (chain21 != null && chain22 != null)
            SetPair(chain21, chain22, true);
    }

    private void EnsureSampleRelationships()
    {
        EnsureEdgePair(chain19, chain21, true);
        EnsureEdgePair(chain21, chain22, true);
        EnsureEdgePair(chain19, node25, false);
        EnsureEdgePair(node25, node18Final, false);
        EnsureEdgePair(node0, node18Final, false);
        EnsureEdgePair(chain22, node16, false);
        EnsureEdgePair(node16, p1, false);
        EnsureEdgePair(p1, p2, true);
        EnsureEdgePair(p2, p3, true);

    }

    private void KeepPermanentMovingConnections()
    {
        for (int i = 0; i < movingNodes.Count; i++)
            EnsureEdgePair(node24, movingNodes[i], true);
    }
    private void MirrorConditionalLinks()
    {
        MirrorEdge(node16, chain22);
        MirrorEdge(node16, p1);

    }
    private void ApplySampleSceneFlags()
    {
        SetFlags(chain19, false, false);
        SetFlags(chain21, false, false);
        SetFlags(chain22, false, false);

        for (int i = 0; i < movingNodes.Count; i++)
            SetFlags(movingNodes[i], true, true);
    }

    private void NormalizeMovingLinks()
    {
        Walkable[] allNodes = FindObjectsOfType<Walkable>();

        for (int i = 0; i < movingNodes.Count; i++)
        {
            Walkable targetNode = movingNodes[i];
            if (targetNode == null)
                continue;

            for (int j = 0; j < targetNode.possiblePaths.Count; j++)
                targetNode.possiblePaths[j].active = false;

            for (int j = 0; j < allNodes.Length; j++)
                SetEdge(allNodes[j], targetNode, false);
        }
    }

    private void UpdateVisualIllusionLink()
    {
        if (viewCamera == null || alignmentNodes.Count == 0 || movingNodes.Count == 0)
            return;

        Walkable bestSource = null;
        Walkable bestTarget = null;
        float bestScreenDistance = float.MaxValue;
        float bestWorldGap = 0f;

        for (int i = 0; i < alignmentNodes.Count; i++)
        {
            Walkable source = alignmentNodes[i];
            if (source == null)
                continue;

            Vector3 sourceScreen = viewCamera.WorldToScreenPoint(source.GetWalkPoint());
            if (sourceScreen.z <= 0f)
                continue;

            for (int j = 0; j < movingNodes.Count; j++)
            {
                Walkable target = movingNodes[j];
                if (target == null)
                    continue;

                Vector3 targetScreen = viewCamera.WorldToScreenPoint(target.GetWalkPoint());
                if (targetScreen.z <= 0f)
                    continue;

                float worldGap = Vector3.Distance(
                    source.GetWalkPoint(),
                    target.GetWalkPoint());

                if (worldGap < MinimumWorldGap)
                    continue;

                float screenDistance = Vector2.Distance(sourceScreen, targetScreen);
                if (screenDistance >= bestScreenDistance)
                    continue;

                bestScreenDistance = screenDistance;
                bestWorldGap = worldGap;
                bestSource = source;
                bestTarget = target;
            }
        }

        float alignmentThreshold = Mathf.Max(24f, Screen.height * ScreenAlignmentThresholdRatio);
        bool aligned = bestSource != null &&
                       bestTarget != null &&
                       bestScreenDistance <= alignmentThreshold &&
                       bestWorldGap >= MinimumWorldGap;

        SetAlignedPair(aligned ? bestSource : null, aligned ? bestTarget : null);
    }

    private void SetAlignedPair(Walkable source, Walkable target)
    {
        if (activeSource == source && activeTarget == target)
            return;

        if (activeSource != null && activeTarget != null)
            EnsureEdgePair(activeSource, activeTarget, false);

        activeSource = source;
        activeTarget = target;

        if (activeSource != null && activeTarget != null)
            EnsureEdgePair(activeSource, activeTarget, true);
    }

    private Walkable FindSingleNode(string nodeName)
    {
        Walkable[] allNodes = FindObjectsOfType<Walkable>();
        for (int i = 0; i < allNodes.Length; i++)
        {
            if (allNodes[i] != null && allNodes[i].name == nodeName)
                return allNodes[i];
        }

        return null;
    }
    private Walkable FindClosestExpected(string nodeName, Vector3 expectedLocalPosition)
    {
        GameObject levelObject = GameObject.Find("Level");
        Vector3 expectedWorldPosition = levelObject != null
            ? levelObject.transform.TransformPoint(expectedLocalPosition)
            : expectedLocalPosition;

        Walkable closest = null;
        float closestDistance = float.MaxValue;
        Walkable[] allNodes = FindObjectsOfType<Walkable>();

        for (int i = 0; i < allNodes.Length; i++)
        {
            Walkable node = allNodes[i];
            if (node == null || node.name != nodeName)
                continue;

            float distance = Vector3.Distance(node.GetWalkPoint(), expectedWorldPosition);
            if (distance >= closestDistance)
                continue;

            closestDistance = distance;
            closest = node;
        }

        return closest;
    }

    private static void AddIfNotNull(List<Walkable> nodes, Walkable node)
    {
        if (node != null)
            nodes.Add(node);
    }

    private static void SetFlags(Walkable node, bool movingGround, bool dontRotate)
    {
        if (node == null)
            return;

        node.movingGround = movingGround;
        node.dontRotate = dontRotate;
    }

    private static bool IsEdgeActive(Walkable from, Walkable to)
    {
        if (from == null || to == null || from.possiblePaths == null)
            return false;

        for (int i = 0; i < from.possiblePaths.Count; i++)
        {
            WalkPath path = from.possiblePaths[i];
            if (path != null && path.target == to.transform)
                return path.active;
        }

        return false;
    }

    private static void EnsureEdge(Walkable from, Walkable to, bool active)
    {
        if (from == null || to == null || from.possiblePaths == null)
            return;

        for (int i = 0; i < from.possiblePaths.Count; i++)
        {
            WalkPath path = from.possiblePaths[i];
            if (path != null && path.target == to.transform)
            {
                path.active = active;
                return;
            }
        }

        from.possiblePaths.Add(new WalkPath
        {
            target = to.transform,
            active = active
        });
    }

    private static void EnsureEdgePair(Walkable first, Walkable second, bool active)
    {
        EnsureEdge(first, second, active);
        EnsureEdge(second, first, active);
    }

    private static void MirrorEdge(Walkable authoritativeFrom, Walkable mirroredTo)
    {
        if (authoritativeFrom == null || mirroredTo == null)
            return;

        SetEdge(mirroredTo, authoritativeFrom, IsEdgeActive(authoritativeFrom, mirroredTo));
    }
    private static void SetPair(Walkable first, Walkable second, bool active)
    {
        SetEdge(first, second, active);
        SetEdge(second, first, active);
    }

    private static void SetEdge(Walkable from, Walkable to, bool active)
    {
        if (from == null || to == null || from.possiblePaths == null)
            return;

        for (int i = 0; i < from.possiblePaths.Count; i++)
        {
            WalkPath path = from.possiblePaths[i];
            if (path != null && path.target == to.transform)
                path.active = active;
        }
    }
}