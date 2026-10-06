using DG.Tweening;
using UnityEngine;
using UnityEngine.EventSystems;

public class IslandRotator : MonoBehaviour
{
    public Transform islandRoot;
    public Level02Controller levelController;
    public float dragSensitivity = .35f;
    public float snapDuration = .45f;
    public float dragThreshold = 14f;

    public static bool IsDragging { get; private set; }
    public static bool IsSnapping { get; private set; }
    public static int LastDragFrame { get; private set; } = -1000;

    private bool candidate;
    private bool dragging;
    private float startMouseX;
    private float startYaw;

    private void Update()
    {
        if (islandRoot == null)
            return;

        if (!candidate && GameManager.instance != null && GameManager.instance.IsInteractionLocked)
            return;

        if (!candidate && levelController != null && levelController.IsTransitioning)
            return;

        if (!candidate && IsSnapping)
            return;

        if (Input.GetMouseButtonDown(0) && !IsPointerOverUi())
        {
            candidate = true;
            dragging = false;
            startMouseX = Input.mousePosition.x;
            startYaw = islandRoot.eulerAngles.y;
        }

        if (!candidate)
            return;

        if (Input.GetMouseButton(0))
        {
            float delta = Input.mousePosition.x - startMouseX;
            if (!dragging && Mathf.Abs(delta) >= dragThreshold)
            {
                dragging = true;
                IsDragging = true;
            }

            if (dragging)
            {
                LastDragFrame = Time.frameCount;
                float yaw = startYaw + delta * dragSensitivity;
                islandRoot.rotation = Quaternion.Euler(0f, yaw, 0f);
            }
        }

        if (Input.GetMouseButtonUp(0))
        {
            candidate = false;

            if (!dragging)
            {
                IsDragging = false;
                return;
            }

            LastDragFrame = Time.frameCount;
            IsDragging = false;
            dragging = false;
            IsSnapping = true;

            float currentYaw = islandRoot.eulerAngles.y;
            float snappedYaw = Mathf.Round(currentYaw / 90f) * 90f;

            DOVirtual
                .Float(currentYaw, snappedYaw, snapDuration, value =>
                {
                    islandRoot.rotation = Quaternion.Euler(0f, value, 0f);
                })
                .SetEase(Ease.OutCubic)
                .SetTarget(this)
                .OnComplete(() =>
                {
                    islandRoot.rotation = Quaternion.Euler(0f, snappedYaw, 0f);
                    IsSnapping = false;
                    if (levelController != null)
                        levelController.OnIslandSnapCompleted();
                });
        }
    }

    private static bool IsPointerOverUi()
    {
        return EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
    }

    private void OnDisable()
    {
        IsDragging = false;
        IsSnapping = false;
    }
}
