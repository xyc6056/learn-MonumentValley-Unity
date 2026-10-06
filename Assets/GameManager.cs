using System;
using System.Collections.Generic;
using DG.Tweening;
using UnityEngine;
using UnityEngine.SceneManagement;

[DefaultExecutionOrder(-100)]
public class GameManager : MonoBehaviour
{
    public static GameManager instance;

    public PlayerController player;
    public List<PathCondition> pathConditions = new List<PathCondition>();
    public List<Transform> pivots;
    public Transform[] objectsToHide;

    [Header("Level")]
    public CameraController cameraController;
    public Transform levelFocus;
    public int mainPivotIndex = 0;
    public float cameraSize = 13f;
    public int initialCameraQuarterTurn;
    public bool allowCameraRotation = true;
    public bool allowPivotRotation = true;

    public event Action OnConnectivityChanged;

    private readonly List<PivotController> pivotControllers = new List<PivotController>();
    private Walkable pendingButtonNode;
    private Walkable pendingGoalNode;
    private bool cameraDragging;
    private float cameraDragAnchor;

    public bool IsInteractionLocked
    {
        get
        {
            if (player != null && player.IsBusy)
                return true;

            for (int i = 0; i < pivotControllers.Count; i++)
            {
                if (pivotControllers[i] != null && pivotControllers[i].IsRotating)
                    return true;
            }

            return cameraController != null && cameraController.IsRotating;
        }
    }

    private void Awake()
    {
        instance = this;

        if (player == null)
            player = FindObjectOfType<PlayerController>();

        if (pivots == null)
            pivots = new List<Transform>();

        ConfigurePivotControllers();
        ResolveCamera();

        if (player != null)
        {
            player.OnNodeReached += HandleNodeReached;
            player.OnPathCompleted += HandlePathCompleted;
        }
    }

    private void Start()
    {
        EnsureGoalFallback();
        SecondLevelPalette.Apply();
        SecondLevelVisuals.Apply();
        LevelValidator.Validate(this);
        EvaluateConditions();
    }

    private void Update()
    {
        if (GameSessionManager.Instance != null && GameSessionManager.Instance.IsPaused)
            return;

        if (Input.GetKeyDown(KeyCode.R))
        {
            SceneManager.LoadSceneAsync(SceneManager.GetActiveScene().name);
            return;
        }

        if (Input.GetKeyDown(KeyCode.Escape))
        {
            if (GameSessionManager.Instance != null)
                GameSessionManager.Instance.TogglePause();

            return;
        }

        HandleCameraInput();

        if (IsInteractionLocked)
            return;

        if (Input.GetKeyDown(KeyCode.LeftArrow) || Input.GetKeyDown(KeyCode.RightArrow))
        {
            int direction = Input.GetKeyDown(KeyCode.RightArrow) ? 1 : -1;
            RotatePivot(mainPivotIndex, direction);
        }
    }

    public bool RotatePivot(int index, int direction)
    {
        if (!allowPivotRotation)
            return false;

        if (IsInteractionLocked)
            return false;

        PivotController pivot = GetPivotController(index);
        if (pivot == null)
            return false;

        return pivot.RotateStep(direction);
    }

    public bool RotateCamera(int direction)
    {
        if (cameraController == null || cameraController.IsRotating)
            return false;

        return cameraController.RotateQuarter(direction);
    }

    private void HandleCameraInput()
    {
        if (!allowCameraRotation)
            return;

        if (cameraController == null)
            return;

        if (Input.GetKeyDown(KeyCode.Q) || Input.GetKeyDown(KeyCode.A))
            RotateCamera(-1);

        if (Input.GetKeyDown(KeyCode.E) || Input.GetKeyDown(KeyCode.D))
            RotateCamera(1);

        bool dragging = Input.GetMouseButton(1) || Input.GetMouseButton(2);
        if (!dragging)
        {
            cameraDragging = false;
            return;
        }

        if (!cameraDragging)
        {
            cameraDragging = true;
            cameraDragAnchor = Input.mousePosition.x;
            return;
        }

        float delta = Input.mousePosition.x - cameraDragAnchor;
        if (Mathf.Abs(delta) < 80f)
            return;

        if (RotateCamera(delta > 0f ? 1 : -1))
            cameraDragAnchor = Input.mousePosition.x;
    }

    public void RotateRightPivot()
    {
        RotatePivot(1, 1);
    }

    public void EvaluateConditions()
    {
        if (pathConditions != null)
        {
            foreach (PathCondition conditionGroup in pathConditions)
            {
                if (conditionGroup == null || conditionGroup.conditions == null)
                    continue;

                bool allSatisfied = true;
                for (int i = 0; i < conditionGroup.conditions.Count; i++)
                {
                    Condition condition = conditionGroup.conditions[i];
                    if (condition == null || !condition.IsSatisfied(cameraController))
                    {
                        allSatisfied = false;
                        break;
                    }
                }

                if (conditionGroup.paths == null)
                    continue;

                foreach (SinglePath path in conditionGroup.paths)
                {
                    if (path == null || path.block == null || path.block.possiblePaths == null)
                        continue;

                    if (path.index < 0 || path.index >= path.block.possiblePaths.Count)
                        continue;

                    path.block.possiblePaths[path.index].active = allSatisfied;
                }
            }
        }

        UpdateObjectVisibility();

        if (OnConnectivityChanged != null)
            OnConnectivityChanged();
    }

    private void ConfigurePivotControllers()
    {
        pivotControllers.Clear();

        for (int i = 0; i < pivots.Count; i++)
        {
            Transform pivot = pivots[i];
            if (pivot == null)
            {
                pivotControllers.Add(null);
                continue;
            }

            PivotController controller = pivot.GetComponent<PivotController>();
            if (controller == null)
                controller = pivot.gameObject.AddComponent<PivotController>();

            if (i == 0)
            {
                controller.rotationAxis = Vector3.up;
                controller.minStep = -1000;
                controller.maxStep = 1000;
                controller.ease = Ease.OutBack;
            }
            else if (i == 1)
            {
                controller.rotationAxis = Vector3.forward;
                controller.minStep = 0;
                controller.maxStep = 1;
                controller.ease = Ease.OutBack;
            }

            controller.OnRotationCompleted -= HandlePivotRotationCompleted;
            controller.OnRotationCompleted += HandlePivotRotationCompleted;
            pivotControllers.Add(controller);
        }
    }

    private void ResolveCamera()
    {
        if (levelFocus == null && pivots.Count > 0)
            levelFocus = pivots[0];

        if (cameraController == null)
        {
            Camera mainCamera = FindMainCamera();
            if (mainCamera == null)
            {
                GameObject cameraObject = new GameObject("Main Camera");
                mainCamera = cameraObject.AddComponent<Camera>();
                cameraObject.tag = "MainCamera";
            }

            cameraController = mainCamera.GetComponent<CameraController>();
            if (cameraController == null)
                cameraController = mainCamera.gameObject.AddComponent<CameraController>();
        }

        if (cameraController != null)
        {
            cameraController.Configure(levelFocus, cameraSize, initialCameraQuarterTurn);
            cameraController.OnTurnCompleted -= HandleCameraTurnCompleted;
            cameraController.OnTurnCompleted += HandleCameraTurnCompleted;
        }

        if (player != null && player.inputCamera == null && cameraController != null)
            player.inputCamera = cameraController.controlledCamera;
    }

    private Camera FindMainCamera()
    {
        Camera[] cameras = Camera.allCameras;
        for (int i = 0; i < cameras.Length; i++)
        {
            if (cameras[i] != null && cameras[i].name == "Main Camera")
                return cameras[i];
        }

        return Camera.main;
    }

    private void EnsureGoalFallback()
    {
        Walkable[] allWalkables = FindObjectsOfType<Walkable>();
        bool hasGoal = false;

        for (int i = 0; i < allWalkables.Length; i++)
        {
            if (allWalkables[i] != null && allWalkables[i].isGoal)
            {
                hasGoal = true;
                break;
            }
        }

        if (hasGoal)
            return;

        for (int i = 0; i < allWalkables.Length; i++)
        {
            if (allWalkables[i] != null && allWalkables[i].name.Contains("final"))
            {
                allWalkables[i].isGoal = true;
                break;
            }
        }

        for (int i = 0; i < allWalkables.Length; i++)
        {
            Walkable node = allWalkables[i];
            if (node != null && node.isButton && node.name == "17button")
            {
                node.buttonPivotIndex = 1;
                node.buttonStep = 1;
                node.buttonOnlyOnce = true;
            }
        }
    }

    private PivotController GetPivotController(int index)
    {
        if (index < 0 || index >= pivotControllers.Count)
            return null;

        return pivotControllers[index];
    }

    private void HandleNodeReached(Walkable node)
    {
        if (node == null)
            return;

        if (node.isButton)
            pendingButtonNode = node;

        if (node.isGoal)
            pendingGoalNode = node;
    }

    private void HandlePathCompleted()
    {
        if (pendingButtonNode != null)
        {
            Walkable button = pendingButtonNode;
            pendingButtonNode = null;

            if (!button.buttonOnlyOnce || !button.buttonTriggered)
            {
                button.buttonTriggered = true;
                RotatePivot(button.buttonPivotIndex, button.buttonStep);
            }
        }

        if (pendingGoalNode != null)
        {
            pendingGoalNode = null;

            if (player != null)
                player.Lock();

            if (GameSessionManager.Instance != null)
                GameSessionManager.Instance.CompleteCurrentLevel();
        }
    }

    private void HandlePivotRotationCompleted(int step)
    {
        EvaluateConditions();
    }

    private void HandleCameraTurnCompleted(int quarterTurn)
    {
        EvaluateConditions();
    }

    private void UpdateObjectVisibility()
    {
        if (objectsToHide == null || objectsToHide.Length == 0)
            return;

        bool visible = false;
        if (pivots.Count > 0 && pivots[0] != null)
        {
            float angle = Mathf.Repeat(pivots[0].localEulerAngles.y, 360f);
            visible = angle > 45f && angle < 135f;
        }

        for (int i = 0; i < objectsToHide.Length; i++)
        {
            if (objectsToHide[i] != null)
                objectsToHide[i].gameObject.SetActive(visible);
        }
    }

    private void OnDestroy()
    {
        if (player != null)
        {
            player.OnNodeReached -= HandleNodeReached;
            player.OnPathCompleted -= HandlePathCompleted;
        }

        for (int i = 0; i < pivotControllers.Count; i++)
        {
            if (pivotControllers[i] != null)
                pivotControllers[i].OnRotationCompleted -= HandlePivotRotationCompleted;
        }

        if (cameraController != null)
            cameraController.OnTurnCompleted -= HandleCameraTurnCompleted;

        if (instance == this)
            instance = null;
    }
}

public enum LevelConditionType
{
    ObjectAngle = 0,
    CameraQuarterTurn = 1
}

[System.Serializable]
public class PathCondition
{
    public string pathConditionName;
    public List<Condition> conditions = new List<Condition>();
    public List<SinglePath> paths = new List<SinglePath>();
}

[System.Serializable]
public class Condition
{
    public Transform conditionObject;
    public Vector3 eulerAngle;
    public LevelConditionType conditionType = LevelConditionType.ObjectAngle;
    public int cameraQuarterTurn;
    public float angleTolerance = 1f;

    public bool IsSatisfied(CameraController camera)
    {
        if (conditionType == LevelConditionType.CameraQuarterTurn)
        {
            return camera != null &&
                   CameraController.NormalizeQuarter(camera.QuarterTurn) ==
                   CameraController.NormalizeQuarter(cameraQuarterTurn);
        }

        if (conditionObject == null)
            return false;

        Vector3 current = conditionObject.eulerAngles;
        float tolerance = Mathf.Max(.01f, angleTolerance);

        return AngleMatches(current.x, eulerAngle.x, tolerance) &&
               AngleMatches(current.y, eulerAngle.y, tolerance) &&
               AngleMatches(current.z, eulerAngle.z, tolerance);
    }

    private static bool AngleMatches(float current, float target, float tolerance)
    {
        return Mathf.Abs(Mathf.DeltaAngle(current, target)) <= tolerance;
    }
}

[System.Serializable]
public class SinglePath
{
    public Walkable block;
    public int index;
}
