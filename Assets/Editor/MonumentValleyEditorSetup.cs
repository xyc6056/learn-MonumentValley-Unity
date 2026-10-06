using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class MonumentValleyEditorSetup
{
    private const string ScenesFolder = "Assets/Scenes";
    private const string ResourcesFolder = "Assets/Resources";
    private const string LevelsFolder = "Assets/Resources/Levels";
    private const string SampleScenePath = ScenesFolder + "/SampleScene.unity";
    private const string Level02ScenePath = ScenesFolder + "/Level02.unity";
    private const string CatalogPath = ResourcesFolder + "/LevelCatalog.asset";
    private const string Level01Path = LevelsFolder + "/Level01.asset";
    private const string Level02Path = LevelsFolder + "/Level02.asset";

    [InitializeOnLoadMethod]
    private static void EnsureBuildScenesRegistered()
    {
        if (!File.Exists(SampleScenePath) || !File.Exists(Level02ScenePath))
            return;

        List<EditorBuildSettingsScene> scenes = new List<EditorBuildSettingsScene>(EditorBuildSettings.scenes);
        bool changed = false;

        changed |= EnsureScene(scenes, SampleScenePath);
        changed |= EnsureScene(scenes, Level02ScenePath);

        if (changed)
            EditorBuildSettings.scenes = scenes.ToArray();
    }

    private static bool EnsureScene(List<EditorBuildSettingsScene> scenes, string path)
    {
        for (int i = 0; i < scenes.Count; i++)
        {
            if (scenes[i].path == path)
            {
                if (scenes[i].enabled)
                    return false;

                scenes[i] = new EditorBuildSettingsScene(path, true);
                return true;
            }
        }

        scenes.Add(new EditorBuildSettingsScene(path, true));
        return true;
    }

    [MenuItem("Tools/Monument Valley/Setup Project")]
    public static void BuildProject()
    {
        ConfigureSampleScene();
        CreateLevelAssets();
        ConfigureBuildSettings();
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Monument Valley setup complete.");
    }

    private static void ConfigureSampleScene()
    {
        Scene scene = EditorSceneManager.OpenScene(SampleScenePath, OpenSceneMode.Single);
        GameManager manager = Object.FindObjectOfType<GameManager>();
        PlayerController player = Object.FindObjectOfType<PlayerController>();
        Transform centerPivot = FindTransform("CenterPivot");
        Transform rightPivot = FindTransform("RightPivot");
        Camera mainCamera = FindMainCamera();

        if (manager != null)
        {
            manager.player = player;
            manager.pivots = new List<Transform> { centerPivot, rightPivot };
            manager.mainPivotIndex = 0;
            manager.cameraSize = 13f;
            manager.levelFocus = centerPivot;
            manager.cameraController = EnsureCameraController(mainCamera, centerPivot, 13f);
        }

        EnsurePivotController(centerPivot, Vector3.up, -1000, 1000);
        EnsurePivotController(rightPivot, Vector3.forward, 0, 1);

        foreach (Walkable walkable in Object.FindObjectsOfType<Walkable>())
        {
            if (walkable.name == "18final")
                walkable.isGoal = true;

            if (walkable.name == "17button")
            {
                walkable.isButton = true;
                walkable.buttonPivotIndex = 1;
                walkable.buttonStep = 1;
                walkable.buttonOnlyOnce = true;
            }
        }

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
    }

    private static void BuildLevel02()
    {
        if (File.Exists(Level02ScenePath))
        {
            Debug.Log("Level02 already exists; generated level creation was skipped.");
            return;
        }
        if (File.Exists(Level02ScenePath))
            AssetDatabase.DeleteAsset(Level02ScenePath);

        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        Material blockMaterial = AssetDatabase.LoadAssetAtPath<Material>(
            "Assets/MaxTurnbull/MonumentValleyFiles/Materials/box.mat");

        GameObject levelRoot = new GameObject("Level02");
        GameObject cameraObject = new GameObject("Main Camera");
        Camera camera = cameraObject.AddComponent<Camera>();
        cameraObject.AddComponent<AudioListener>();
        cameraObject.tag = "MainCamera";

        GameObject lightObject = new GameObject("Directional Light");
        Light light = lightObject.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = .85f;
        lightObject.transform.rotation = Quaternion.Euler(35.264f, -45f, 0f);

        GameObject managerObject = new GameObject("GameManager");
        GameManager manager = managerObject.AddComponent<GameManager>();

        GameObject centerPivotObject = new GameObject("CenterPivot");
        centerPivotObject.transform.SetParent(levelRoot.transform, false);
        centerPivotObject.transform.localPosition = new Vector3(2f, .2f, 1f);
        CreatePivotBlade(centerPivotObject.transform, blockMaterial, new Vector3(.3f, .3f, 3f));
        PivotController centerPivot = centerPivotObject.AddComponent<PivotController>();
        centerPivot.rotationAxis = Vector3.up;
        centerPivot.minStep = -1000;
        centerPivot.maxStep = 1000;
        centerPivot.ease = DG.Tweening.Ease.OutBack;

        GameObject rightPivotObject = new GameObject("RightPivot");
        rightPivotObject.transform.SetParent(levelRoot.transform, false);
        rightPivotObject.transform.localPosition = new Vector3(8f, 1.2f, 1f);
        CreatePivotBlade(rightPivotObject.transform, blockMaterial, new Vector3(.3f, 3f, .3f));
        PivotController rightPivot = rightPivotObject.AddComponent<PivotController>();
        rightPivot.rotationAxis = Vector3.forward;
        rightPivot.minStep = 0;
        rightPivot.maxStep = 1;
        rightPivot.ease = DG.Tweening.Ease.OutBack;

        Walkable start = CreateNode("S", levelRoot.transform, new Vector3(0f, 0f, 0f), blockMaterial, false, false);
        Walkable a = CreateNode("A", levelRoot.transform, new Vector3(2f, 0f, 0f), blockMaterial, false, false);
        Walkable b = CreateNode("B", levelRoot.transform, new Vector3(4f, 0f, 0f), blockMaterial, false, false);
        Walkable c = CreateNode("C", levelRoot.transform, new Vector3(6f, 0f, 0f), blockMaterial, false, false);
        Walkable button = CreateNode("Button", levelRoot.transform, new Vector3(8f, 0f, 0f), blockMaterial, false, true);
        Walkable d = CreateNode("D", levelRoot.transform, new Vector3(8f, 2f, 0f), blockMaterial, false, false);
        Walkable goal = CreateNode("Goal", levelRoot.transform, new Vector3(10f, 2f, 0f), blockMaterial, false, false);
        Walkable sideA = CreateNode("S_side", levelRoot.transform, new Vector3(0f, 0f, 2f), blockMaterial, false, false);
        Walkable sideB = CreateNode("B_side", levelRoot.transform, new Vector3(4f, 0f, 2f), blockMaterial, false, false);
        Walkable sideC = CreateNode("C_side", levelRoot.transform, new Vector3(6f, 0f, 2f), blockMaterial, false, false);

        goal.isGoal = true;
        button.isButton = true;
        button.buttonPivotIndex = 1;
        button.buttonStep = 1;
        button.buttonOnlyOnce = true;

        EdgeInfo startEdge = AddBidirectionalEdge(start, a, false);
        EdgeInfo cameraQ1Edge = AddBidirectionalEdge(a, b, false);
        EdgeInfo cameraQ3Edge = AddBidirectionalEdge(b, c, false);
        EdgeInfo buttonEdge = AddBidirectionalEdge(c, button, false);
        EdgeInfo doorEdge = AddBidirectionalEdge(d, goal, false);

        AddBidirectionalEdge(button, d, true);
        AddBidirectionalEdge(start, sideA, true);
        AddBidirectionalEdge(b, sideB, true);
        AddBidirectionalEdge(c, sideC, true);

        manager.pathConditions = new List<PathCondition>
        {
            CreateConditionGroup(
                "Start Gate",
                centerPivotObject.transform,
                Vector3.zero,
                0,
                startEdge),
            CreateConditionGroup(
                "Camera Quarter 1",
                null,
                Vector3.zero,
                1,
                cameraQ1Edge),
            CreateConditionGroup(
                "Camera Quarter 3",
                null,
                Vector3.zero,
                3,
                cameraQ3Edge),
            CreateConditionGroup(
                "Button Gate",
                centerPivotObject.transform,
                new Vector3(0f, 90f, 0f),
                0,
                buttonEdge),
            CreateConditionGroup(
                "Door Gate",
                rightPivotObject.transform,
                new Vector3(0f, 0f, 90f),
                0,
                doorEdge)
        };

        manager.pivots = new List<Transform> { centerPivotObject.transform, rightPivotObject.transform };
        manager.levelFocus = centerPivotObject.transform;
        manager.mainPivotIndex = 0;
        manager.cameraSize = 8f;
        manager.initialCameraQuarterTurn = 0;
        manager.cameraController = EnsureCameraController(camera, centerPivotObject.transform, 8f);

        PlayerController player = CreatePlayer(levelRoot.transform, start, blockMaterial);
        manager.player = player;

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene, Level02ScenePath);
    }

    private static void CreateLevelAssets()
    {
        if (!AssetDatabase.IsValidFolder(ResourcesFolder))
            AssetDatabase.CreateFolder("Assets", "Resources");

        if (!AssetDatabase.IsValidFolder(LevelsFolder))
            AssetDatabase.CreateFolder(ResourcesFolder, "Levels");

        LevelDefinition level01 = AssetDatabase.LoadAssetAtPath<LevelDefinition>(Level01Path);
        if (level01 == null)
        {
            level01 = ScriptableObject.CreateInstance<LevelDefinition>();
            AssetDatabase.CreateAsset(level01, Level01Path);
        }

        LevelDefinition level02 = AssetDatabase.LoadAssetAtPath<LevelDefinition>(Level02Path);
        if (level02 == null)
        {
            level02 = ScriptableObject.CreateInstance<LevelDefinition>();
            AssetDatabase.CreateAsset(level02, Level02Path);
        }

        level01.levelId = "level-01";
        level01.displayName = "Level 01";
        level01.sceneName = "SampleScene";
        level01.nextLevel = level02;

        level02.levelId = "level-02";
        level02.displayName = "Level 02";
        level02.sceneName = "Level02";
        level02.nextLevel = null;

        LevelCatalog catalog = AssetDatabase.LoadAssetAtPath<LevelCatalog>(CatalogPath);
        if (catalog == null)
        {
            catalog = ScriptableObject.CreateInstance<LevelCatalog>();
            AssetDatabase.CreateAsset(catalog, CatalogPath);
        }

        catalog.levels = new List<LevelDefinition> { level01, level02 };
        EditorUtility.SetDirty(level01);
        EditorUtility.SetDirty(level02);
        EditorUtility.SetDirty(catalog);
    }

    private static void ConfigureBuildSettings()
    {
        EditorBuildSettings.scenes = new[]
        {
            new EditorBuildSettingsScene(SampleScenePath, true),
            new EditorBuildSettingsScene(Level02ScenePath, true)
        };
    }

    private static Walkable CreateNode(
        string name,
        Transform parent,
        Vector3 position,
        Material material,
        bool isStair,
        bool isButton)
    {
        GameObject nodeObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
        nodeObject.name = name;
        nodeObject.transform.SetParent(parent, false);
        nodeObject.transform.localPosition = position;
        nodeObject.transform.localScale = new Vector3(1.8f, .5f, 1.8f);

        Renderer renderer = nodeObject.GetComponent<Renderer>();
        if (renderer != null && material != null)
            renderer.sharedMaterial = material;

        Walkable walkable = nodeObject.AddComponent<Walkable>();
        walkable.isStair = isStair;
        walkable.isButton = isButton;
        walkable.possiblePaths = new List<WalkPath>();
        return walkable;
    }

    private static PlayerController CreatePlayer(Transform parent, Walkable startNode, Material material)
    {
        GameObject playerObject = new GameObject("Player");
        playerObject.transform.SetParent(parent, false);
        playerObject.transform.localPosition = startNode.transform.localPosition + new Vector3(0f, .5f, 0f);

        GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        body.name = "PlayerBody";
        body.transform.SetParent(playerObject.transform, false);
        body.transform.localPosition = new Vector3(0f, 0f, 0f);
        body.transform.localScale = new Vector3(.35f, .5f, .35f);
        Collider bodyCollider = body.GetComponent<Collider>();
        if (bodyCollider != null)
            Object.DestroyImmediate(bodyCollider);

        Renderer renderer = body.GetComponent<Renderer>();
        if (renderer != null && material != null)
            renderer.sharedMaterial = material;

        GameObject indicatorObject = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        indicatorObject.name = "Indicator";
        indicatorObject.transform.SetParent(parent, false);
        indicatorObject.transform.localScale = new Vector3(.25f, .25f, .25f);
        Collider indicatorCollider = indicatorObject.GetComponent<Collider>();
        if (indicatorCollider != null)
            Object.DestroyImmediate(indicatorCollider);
        Material indicatorMaterial = AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Indicator.mat");
        if (indicatorMaterial != null)
            indicatorObject.GetComponent<Renderer>().sharedMaterial = indicatorMaterial;

        PlayerController player = playerObject.AddComponent<PlayerController>();
        player.indicator = indicatorObject.transform;
        player.inputCamera = null;
        playerObject.AddComponent<PlayerAnimation>();
        return player;
    }

    private static void CreatePivotBlade(Transform parent, Material material, Vector3 scale)
    {
        GameObject blade = GameObject.CreatePrimitive(PrimitiveType.Cube);
        blade.name = "Blade";
        blade.transform.SetParent(parent, false);
        blade.transform.localScale = scale;
        Renderer renderer = blade.GetComponent<Renderer>();
        if (renderer != null && material != null)
            renderer.sharedMaterial = material;
    }

    private static CameraController EnsureCameraController(Camera camera, Transform focus, float size)
    {
        if (camera == null)
            return null;

        CameraController controller = camera.GetComponent<CameraController>();
        if (controller == null)
            controller = camera.gameObject.AddComponent<CameraController>();

        controller.controlledCamera = camera;
        controller.focusPoint = focus;
        controller.pitch = 35.264f;
        controller.baseYaw = -45f;
        controller.distance = 35f;
        controller.orthographicSize = size;
        controller.rotationDuration = .5f;
        return controller;
    }

    private static void EnsurePivotController(Transform pivot, Vector3 axis, int minStep, int maxStep)
    {
        if (pivot == null)
            return;

        PivotController controller = pivot.GetComponent<PivotController>();
        if (controller == null)
            controller = pivot.gameObject.AddComponent<PivotController>();

        controller.rotationAxis = axis;
        controller.minStep = minStep;
        controller.maxStep = maxStep;
        controller.ease = DG.Tweening.Ease.OutBack;
    }

    private static Transform FindTransform(string name)
    {
        foreach (Transform transform in Object.FindObjectsOfType<Transform>())
        {
            if (transform.name == name)
                return transform;
        }

        return null;
    }

    private static Camera FindMainCamera()
    {
        Camera[] cameras = Object.FindObjectsOfType<Camera>();
        for (int i = 0; i < cameras.Length; i++)
        {
            if (cameras[i] != null && cameras[i].name == "Main Camera")
                return cameras[i];
        }

        return Camera.main;
    }

    private static EdgeInfo AddBidirectionalEdge(Walkable first, Walkable second, bool active)
    {
        int firstIndex = AddEdge(first, second, active);
        int secondIndex = AddEdge(second, first, active);
        return new EdgeInfo
        {
            block = first,
            forwardIndex = firstIndex,
            backwardBlock = second,
            backwardIndex = secondIndex
        };
    }

    private static int AddEdge(Walkable from, Walkable to, bool active)
    {
        from.possiblePaths.Add(new WalkPath { target = to.transform, active = active });
        return from.possiblePaths.Count - 1;
    }

    private static PathCondition CreateConditionGroup(
        string name,
        Transform objectTransform,
        Vector3 angle,
        int cameraQuarterTurn,
        EdgeInfo edge)
    {
        PathCondition group = new PathCondition
        {
            pathConditionName = name,
            conditions = new List<Condition>(),
            paths = new List<SinglePath>()
        };

        if (objectTransform != null)
        {
            group.conditions.Add(new Condition
            {
                conditionObject = objectTransform,
                eulerAngle = angle,
                conditionType = LevelConditionType.ObjectAngle,
                angleTolerance = 1f
            });
        }
        else
        {
            group.conditions.Add(new Condition
            {
                conditionType = LevelConditionType.CameraQuarterTurn,
                cameraQuarterTurn = cameraQuarterTurn
            });
        }

        group.paths.Add(new SinglePath { block = edge.block, index = edge.forwardIndex });
        group.paths.Add(new SinglePath { block = edge.backwardBlock, index = edge.backwardIndex });
        return group;
    }

    private struct EdgeInfo
    {
        public Walkable block;
        public int forwardIndex;
        public Walkable backwardBlock;
        public int backwardIndex;
    }
}
