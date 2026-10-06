using System;
using System.Collections.Generic;
using DG.Tweening;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;

[SelectionBase]
public class PlayerController : MonoBehaviour
{
    public bool walking = false;

    [Space]
    public Transform currentCube;
    public Transform clickedCube;
    public Transform indicator;

    [Space]
    public List<Transform> finalPath = new List<Transform>();

    [Header("Input")]
    public Camera inputCamera;

    [Header("Movement")]
    public float normalStepDuration = .2f;
    public float stairStepDuration = .3f;
    public float turnDuration = .1f;
    public Color validIndicatorColor = Color.white;
    public Color invalidIndicatorColor = Color.red;

    public Walkable CurrentNode { get; private set; }
    public bool IsBusy { get { return state != MoveState.Idle; } }

    public event Action<Walkable> OnNodeReached;
    public event Action OnPathStarted;
    public event Action OnPathCompleted;

    private enum MoveState
    {
        Idle,
        Moving,
        Locked
    }

    private MoveState state = MoveState.Idle;
    private Sequence moveSequence;
    private Sequence indicatorSequence;
    private Animator animator;
    private bool mousePressActive;
    private Walkable rotationTarget;
    private Vector3 lastFacing = Vector3.forward;
    private bool alignToWalkableSurface;
    private Vector2 mouseDownPosition;

    private void Awake()
    {
        string activeSceneName = SceneManager.GetActiveScene().name;
        alignToWalkableSurface = activeSceneName == "Scene 2" || activeSceneName.StartsWith("Scene 2_");
        animator = GetComponentInChildren<Animator>();
        if (inputCamera == null)
            inputCamera = Camera.main;
    }

    private void Start()
    {
        RayCastDown();
    }

    private void Update()
    {
        if (IsPaused())
            return;

        if (currentCube == null)
            RayCastDown();

        if (state != MoveState.Idle || currentCube == null || IslandRotator.IsSnapping)
            return;

        if (Input.GetMouseButtonDown(0))
        {
            mousePressActive = true;
            mouseDownPosition = Input.mousePosition;
        }

        if (mousePressActive && Input.GetMouseButtonUp(0))
        {
            mousePressActive = false;

            if (IslandRotator.LastDragFrame >= Time.frameCount - 1)
                return;

            if (Vector2.Distance(mouseDownPosition, Input.mousePosition) > 14f)
                return;

            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
                return;

            Camera rayCamera = inputCamera != null ? inputCamera : Camera.main;
            if (rayCamera == null)
                return;

            Ray mouseRay = rayCamera.ScreenPointToRay(Input.mousePosition);
            RaycastHit mouseHit;

            if (Physics.Raycast(mouseRay, out mouseHit, 1000f))
            {
                Walkable target = mouseHit.collider.GetComponentInParent<Walkable>();
                if (target != null)
                    TryMoveTo(target);
            }
        }
    }

    private void LateUpdate()
    {
        if (!alignToWalkableSurface || rotationTarget == null)
            return;

        Vector3 surfaceNormal = rotationTarget.transform.up.normalized;
        if (surfaceNormal.sqrMagnitude < .001f)
            surfaceNormal = Vector3.up;

        Vector3 moveDirection = rotationTarget.GetWalkPoint() - transform.position;
        Vector3 facing = Vector3.ProjectOnPlane(moveDirection, surfaceNormal);

        if (facing.sqrMagnitude > .001f)
            lastFacing = facing.normalized;
        else
            facing = Vector3.ProjectOnPlane(lastFacing, surfaceNormal);

        if (facing.sqrMagnitude < .001f)
            facing = Vector3.ProjectOnPlane(rotationTarget.transform.forward, surfaceNormal);

        if (facing.sqrMagnitude < .001f)
            facing = Vector3.ProjectOnPlane(transform.forward, surfaceNormal);

        if (facing.sqrMagnitude < .001f)
            facing = Vector3.Cross(surfaceNormal, Vector3.right);

        transform.rotation = Quaternion.LookRotation(facing.normalized, surfaceNormal);
    }

    public bool TryMoveTo(Walkable target)
    {
        if (target == null || CurrentNode == null || IsBusy)
            return false;

        if (target == CurrentNode)
            return false;

        List<Walkable> path = WalkGraph.FindPath(CurrentNode, target);
        if (path == null || path.Count < 2)
        {
            ShowIndicator(target.GetWalkPoint(), false);
            return false;
        }

        clickedCube = target.transform;
        finalPath.Clear();
        for (int i = 0; i < path.Count; i++)
            finalPath.Add(path[i].transform);

        ShowIndicator(target.GetWalkPoint(), true);
        BeginMove(path);
        return true;
    }

    public void Lock()
    {
        state = MoveState.Locked;
        walking = false;
    }

    public void Unlock()
    {
        state = MoveState.Idle;
    }

    public void RayCastDown()
    {
        if (IsBusy)
            return;

        Transform origin = transform.childCount > 0 ? transform.GetChild(0) : transform;
        Ray playerRay = new Ray(origin.position, -transform.up);
        RaycastHit playerHit;

        if (Physics.Raycast(playerRay, out playerHit, 1000f))
        {
            Walkable node = playerHit.collider.GetComponentInParent<Walkable>();
            if (node != null)
            {
                rotationTarget = node;

                CurrentNode = node;
                currentCube = node.transform;
            }
        }
    }

    private void BeginMove(List<Walkable> path)
    {
        state = MoveState.Moving;
        walking = true;

        if (moveSequence != null)
            moveSequence.Kill(false);

        moveSequence = DOTween.Sequence();
        moveSequence.SetTarget(transform);

        for (int i = 1; i < path.Count; i++)
            AppendStep(moveSequence, path[i - 1], path[i]);

        moveSequence.OnComplete(CompleteMove);

        if (OnPathStarted != null)
            OnPathStarted();
    }

    private void AppendStep(Sequence sequence, Walkable from, Walkable to)
    {
        sequence.AppendCallback(() =>
        {
            SetParentForNode(from);
            SetBlendForStep(from, to);
            rotationTarget = to;
        });

        float duration = to.isStair ? stairStepDuration : normalStepDuration;
        sequence.Append(transform
            .DOMove(to.GetWalkPoint(), duration)
            .SetEase(Ease.Linear)
            .SetTarget(transform));

        if (!to.dontRotate && !alignToWalkableSurface)
        {
            sequence.Join(transform
                .DOLookAt(to.GetWalkPoint(), turnDuration, AxisConstraint.Y, Vector3.up)
                .SetTarget(transform));
        }

        sequence.AppendCallback(() =>
        {
            CurrentNode = to;
            currentCube = to.transform;
            SetParentForNode(to);
            SetBlend(0f);

            if (OnNodeReached != null)
                OnNodeReached(to);

            to.NotifyReached(this);
        });
    }

    private void CompleteMove()
    {
        state = MoveState.Idle;
        walking = false;
        clickedCube = null;
        finalPath.Clear();
        moveSequence = null;

        if (OnPathCompleted != null)
            OnPathCompleted();
    }

    private void SetParentForNode(Walkable node)
    {
        Transform targetParent = node != null && node.movingGround && node.transform.parent != null
            ? node.transform.parent
            : null;

        if (transform.parent != targetParent)
            transform.SetParent(targetParent, true);
    }

    private Quaternion GetSurfaceFacingRotation(Walkable from, Walkable to)
    {
        Vector3 surfaceNormal = to != null ? to.transform.up.normalized : Vector3.up;
        if (surfaceNormal.sqrMagnitude < .001f)
            surfaceNormal = Vector3.up;

        Vector3 moveDirection = from != null && to != null
            ? to.GetWalkPoint() - from.GetWalkPoint()
            : Vector3.zero;
        Vector3 facing = Vector3.ProjectOnPlane(moveDirection, surfaceNormal);

        if (facing.sqrMagnitude < .001f && to != null)
            facing = Vector3.ProjectOnPlane(to.transform.forward, surfaceNormal);

        if (facing.sqrMagnitude < .001f)
            facing = Vector3.ProjectOnPlane(transform.forward, surfaceNormal);

        if (facing.sqrMagnitude < .001f)
            facing = Vector3.Cross(surfaceNormal, Vector3.right);

        return Quaternion.LookRotation(facing.normalized, surfaceNormal);
    }

    private void SetBlendForStep(Walkable from, Walkable to)
    {
        float fromY = from.GetWalkPoint().y;
        float toY = to.GetWalkPoint().y;
        float blend = to.isStair && Mathf.Abs(toY - fromY) > .01f
            ? Mathf.Sign(toY - fromY)
            : 0f;

        SetBlend(blend);
    }

    private void ShowIndicator(Vector3 position, bool valid)
    {
        if (indicator == null)
            return;

        if (indicatorSequence != null)
            indicatorSequence.Kill(false);

        indicator.position = position;

        ParticleSystem particles = indicator.GetComponentInChildren<ParticleSystem>();
        if (particles != null)
            particles.Play();

        Renderer indicatorRenderer = indicator.GetComponentInChildren<Renderer>();
        if (indicatorRenderer == null)
            return;

        Material material = indicatorRenderer.material;
        Color startColor = valid ? validIndicatorColor : invalidIndicatorColor;
        Color endColor = valid ? validIndicatorColor : Color.clear;

        material.color = startColor;
        indicatorSequence = DOTween.Sequence();
        indicatorSequence.Append(material.DOColor(startColor, .1f));
        indicatorSequence.Append(material.DOColor(endColor, .3f).SetDelay(.2f));
        indicatorSequence.Append(material.DOColor(Color.clear, .3f));
    }

    private void SetBlend(float value)
    {
        if (animator != null)
            animator.SetFloat("Blend", value);
    }

    private bool IsPaused()
    {
        return GameSessionManager.Instance != null && GameSessionManager.Instance.IsPaused;
    }

    private void OnDestroy()
    {
        if (moveSequence != null)
            moveSequence.Kill(false);

        if (indicatorSequence != null)
            indicatorSequence.Kill(false);

        DOTween.Kill(transform);
    }

    private void OnDrawGizmos()
    {
        if (transform.childCount == 0)
            return;

        Gizmos.color = Color.blue;
        Ray ray = new Ray(transform.GetChild(0).position, -transform.up);
        Gizmos.DrawRay(ray);
    }
}
