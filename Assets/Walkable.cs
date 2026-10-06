using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

public class Walkable : MonoBehaviour
{

    public List<WalkPath> possiblePaths = new List<WalkPath>();

    [Space]

    public Transform previousBlock;

    [Space]

    [Header("Booleans")]
    public bool isStair = false;
    public bool movingGround = false;
    public bool isButton;
    public bool dontRotate;
    public bool isGoal;

    [Header("Button Action")]
    public int buttonPivotIndex = 1;
    public int buttonStep = 1;
    public bool buttonOnlyOnce = true;

    [System.NonSerialized]
    public bool buttonTriggered;

    public UnityEvent onReached = new UnityEvent();

    [Space]

    [Header("Offsets")]
    public float walkPointOffset = .5f;
    public float stairOffset = .4f;

    public Vector3 GetWalkPoint()
    {
        float stair = isStair ? stairOffset : 0;
        return transform.position + transform.up * walkPointOffset - transform.up * stair;
    }

    public Walkable GetPathTarget(WalkPath path)
    {
        if (path == null || path.target == null)
            return null;

        return path.target.GetComponentInParent<Walkable>();
    }

    public void NotifyReached(PlayerController player)
    {
        if (onReached != null)
            onReached.Invoke();
    }

    private void OnDrawGizmos()
    {
        Gizmos.color = Color.gray;
        float stair = isStair ? .4f : 0;
        Gizmos.DrawSphere(GetWalkPoint(), .1f);

        if (possiblePaths == null)
            return;

        foreach (WalkPath p in possiblePaths)
        {
            if (p.target == null)
                continue;

            Walkable target = p.target.GetComponentInParent<Walkable>();
            if (target == null)
                continue;
            Gizmos.color = p.active ? Color.black : Color.clear;
            Gizmos.DrawLine(GetWalkPoint(), target.GetWalkPoint());
        }
    }
}

[System.Serializable]
public class WalkPath
{
    public Transform target;
    public bool active = true;
}
