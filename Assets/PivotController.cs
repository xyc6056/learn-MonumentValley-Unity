using System;
using DG.Tweening;
using UnityEngine;

[DisallowMultipleComponent]
public class PivotController : MonoBehaviour
{
    public Vector3 rotationAxis = Vector3.up;
    public float stepDegrees = 90f;
    public float duration = .6f;
    public Ease ease = Ease.OutBack;
    public int minStep = -1000;
    public int maxStep = 1000;

    public int CurrentStep { get; private set; }
    public bool IsRotating { get; private set; }

    public event Action<int> OnRotationStarted;
    public event Action<int> OnRotationCompleted;

    private Vector3 startingLocalEuler;
    private Tween rotationTween;

    private void Awake()
    {
        startingLocalEuler = transform.localEulerAngles;
    }

    public bool RotateStep(int direction)
    {
        if (IsRotating || direction == 0)
            return false;

        int targetStep = CurrentStep + (direction > 0 ? 1 : -1);
        if (targetStep < minStep || targetStep > maxStep)
            return false;

        return RotateToStep(targetStep);
    }

    public bool RotateToStep(int targetStep)
    {
        if (IsRotating)
            return false;

        targetStep = Mathf.Clamp(targetStep, minStep, maxStep);
        if (targetStep == CurrentStep)
            return false;

        IsRotating = true;
        int requestedStep = targetStep;
        if (OnRotationStarted != null)
            OnRotationStarted(requestedStep);

        Vector3 targetEuler = startingLocalEuler + rotationAxis * (stepDegrees * requestedStep);
        rotationTween = transform
            .DOLocalRotate(targetEuler, duration, RotateMode.Fast)
            .SetEase(ease)
            .SetTarget(this)
            .OnComplete(() => CompleteRotation(requestedStep));

        return true;
    }

    public void SetStepImmediate(int step, bool notify = false)
    {
        KillTween();
        CurrentStep = Mathf.Clamp(step, minStep, maxStep);
        transform.localEulerAngles = startingLocalEuler + rotationAxis * (stepDegrees * CurrentStep);
        IsRotating = false;

        if (notify && OnRotationCompleted != null)
            OnRotationCompleted(CurrentStep);
    }

    public float GetAxisAngle()
    {
        return Vector3.Dot(transform.localEulerAngles, rotationAxis);
    }

    private void CompleteRotation(int completedStep)
    {
        CurrentStep = completedStep;
        transform.localEulerAngles = startingLocalEuler + rotationAxis * (stepDegrees * CurrentStep);
        IsRotating = false;
        rotationTween = null;

        if (OnRotationCompleted != null)
            OnRotationCompleted(CurrentStep);
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
