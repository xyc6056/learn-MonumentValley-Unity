using System;
using DG.Tweening;
using UnityEngine;

[DisallowMultipleComponent]
public class CameraController : MonoBehaviour
{
    public Camera controlledCamera;
    public Transform focusPoint;
    public float pitch = 35.264f;
    public float baseYaw = -45f;
    public float distance = 35f;
    public float orthographicSize = 13f;
    public float rotationDuration = .5f;

    public int QuarterTurn { get; private set; }
    public bool IsRotating { get; private set; }

    public event Action<int> OnTurnCompleted;

    private float currentYaw;
    private Tween rotationTween;

    private void Awake()
    {
        if (controlledCamera == null)
            controlledCamera = GetComponent<Camera>();

        currentYaw = baseYaw;
        QuarterTurn = 0;
    }

    public void Configure(Transform focus, float size, int initialQuarterTurn)
    {
        focusPoint = focus;
        orthographicSize = size;
        SetQuarterTurnImmediate(initialQuarterTurn);
    }

    public bool RotateQuarter(int direction)
    {
        if (IsRotating || direction == 0)
            return false;

        int targetQuarter = NormalizeQuarter(QuarterTurn + (direction > 0 ? 1 : -1));
        float targetYaw = currentYaw + (direction > 0 ? 90f : -90f);
        float startYaw = currentYaw;

        IsRotating = true;
        rotationTween = DOVirtual
            .Float(startYaw, targetYaw, rotationDuration, ApplyYaw)
            .SetEase(Ease.InOutSine)
            .SetTarget(this)
            .OnComplete(() => CompleteTurn(targetQuarter));

        return true;
    }

    public void SetQuarterTurnImmediate(int quarterTurn)
    {
        KillTween();
        QuarterTurn = NormalizeQuarter(quarterTurn);
        currentYaw = baseYaw + QuarterTurn * 90f;
        ApplyYaw(currentYaw);
        IsRotating = false;
    }

    public void SnapToFocus()
    {
        ApplyYaw(currentYaw);
    }

    public static int NormalizeQuarter(int quarterTurn)
    {
        int result = quarterTurn % 4;
        if (result < 0)
            result += 4;

        return result;
    }

    private void ApplyYaw(float yaw)
    {
        if (focusPoint == null)
            return;

        Quaternion rotation = Quaternion.Euler(pitch, yaw, 0f);
        transform.rotation = rotation;
        transform.position = focusPoint.position - rotation * Vector3.forward * distance;

        if (controlledCamera != null)
        {
            controlledCamera.orthographic = true;
            controlledCamera.orthographicSize = orthographicSize;
        }
    }

    private void CompleteTurn(int quarterTurn)
    {
        QuarterTurn = NormalizeQuarter(quarterTurn);
        currentYaw = baseYaw + QuarterTurn * 90f;
        ApplyYaw(currentYaw);
        IsRotating = false;
        rotationTween = null;

        if (OnTurnCompleted != null)
            OnTurnCompleted(QuarterTurn);
    }

    private void KillTween()
    {
        if (rotationTween != null && rotationTween.IsActive())
            rotationTween.Kill(false);

        rotationTween = null;
    }

    private void OnDisable()
    {
        KillTween();
        IsRotating = false;
    }
}
