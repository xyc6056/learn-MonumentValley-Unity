using System.Collections.Generic;
using DG.Tweening;
using UnityEngine;

public class Level02Controller : MonoBehaviour
{
    public Camera targetCamera;
    public Transform upperTowerMovingHalf;
    public Vector3 assembledWorldPosition;
    public Walkable lowerJunction;
    public Walkable upperBase;
    public List<Walkable> upperNodes = new List<Walkable>();
    public List<Walkable> bridgeSegments = new List<Walkable>();
    public List<Walkable> farNodes = new List<Walkable>();
    public List<Walkable> allNodes = new List<Walkable>();
    public float screenAlignmentThreshold = 60f;
    public float minimum3DGap = 2.5f;
    public float bridgeExtendedScaleX = 1.8f;

    public bool IsTransitioning { get; private set; }

    private bool activated;
    private bool combined;
    private bool bridgeExtended;
    private bool illusionAligned;

    private void Start()
    {
        RecalculateScreenConnections();
    }

    public void Configure(
        Camera camera,
        Transform towerHalf,
        Vector3 assembledPosition,
        Walkable junction,
        Walkable baseNode,
        List<Walkable> upper,
        List<Walkable> bridge,
        List<Walkable> far,
        List<Walkable> all)
    {
        targetCamera = camera;
        upperTowerMovingHalf = towerHalf;
        assembledWorldPosition = assembledPosition;
        lowerJunction = junction;
        upperBase = baseNode;
        upperNodes = upper;
        bridgeSegments = bridge;
        farNodes = far;
        allNodes = all;
    }

    public void ActivateSplitTower()
    {
        if (activated || IsTransitioning)
            return;

        activated = true;
        IsTransitioning = true;
        combined = false;
        bridgeExtended = false;

        upperTowerMovingHalf
            .DOMove(assembledWorldPosition, .75f)
            .SetEase(Ease.OutCubic)
            .SetTarget(this)
            .OnComplete(() =>
            {
                combined = true;
                RecalculateScreenConnections();
                ExtendBridge();
            });
    }

    public void OnIslandSnapCompleted()
    {
        RecalculateScreenConnections();
    }

    public void RecalculateScreenConnections()
    {
        if (targetCamera == null || lowerJunction == null || upperBase == null)
            return;

        for (int i = 0; i < allNodes.Count; i++)
        {
            if (allNodes[i] == null)
                continue;

            targetCamera.WorldToScreenPoint(allNodes[i].GetWalkPoint());
        }

        Vector3 lowerScreen = targetCamera.WorldToScreenPoint(lowerJunction.GetWalkPoint());
        Vector3 upperScreen = targetCamera.WorldToScreenPoint(upperBase.GetWalkPoint());
        float screenDistance = Vector2.Distance(lowerScreen, upperScreen);
        float worldDistance = Vector3.Distance(
            lowerJunction.GetWalkPoint(),
            upperBase.GetWalkPoint());

        illusionAligned = screenDistance <= screenAlignmentThreshold &&
                          worldDistance >= minimum3DGap;

        UpdateConnections();
    }

    private void ExtendBridge()
    {
        Sequence sequence = DOTween.Sequence();
        sequence.SetTarget(this);

        for (int i = 0; i < bridgeSegments.Count; i++)
        {
            Transform segment = bridgeSegments[i].transform;
            sequence.Join(segment.DOScaleX(bridgeExtendedScaleX, .45f).SetEase(Ease.OutCubic));
        }

        sequence.OnComplete(() =>
        {
            bridgeExtended = true;
            IsTransitioning = false;
            RecalculateScreenConnections();
        });
    }

    private void UpdateConnections()
    {
        SetPair(lowerJunction, upperBase, activated && illusionAligned);

        for (int i = 1; i < upperNodes.Count; i++)
            SetPair(upperNodes[i - 1], upperNodes[i], combined);

        if (upperNodes.Count > 0 && bridgeSegments.Count > 0)
            SetPair(upperNodes[upperNodes.Count - 1], bridgeSegments[0], combined && bridgeExtended);

        for (int i = 1; i < bridgeSegments.Count; i++)
            SetPair(bridgeSegments[i - 1], bridgeSegments[i], combined && bridgeExtended);

        if (bridgeSegments.Count > 0 && farNodes.Count > 0)
            SetPair(bridgeSegments[bridgeSegments.Count - 1], farNodes[0], combined && bridgeExtended);
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
            {
                path.active = active;
                return;
            }
        }
    }
}
