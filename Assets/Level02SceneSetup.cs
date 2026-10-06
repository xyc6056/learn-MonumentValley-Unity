using System.Collections.Generic;
using UnityEngine;

public class Level02SceneSetup : MonoBehaviour
{
    private void Awake()
    {
        Build();
    }

    private void Build()
    {
        GameObject oldLevel = GameObject.Find("Level");
        GameObject props = GameObject.Find("Props");
        GameObject environment = GameObject.Find("Env");
        GameObject template = FindBlockTemplate(oldLevel);

        if (template == null)
        {
            Debug.LogError("Level02 setup could not find a Level01 middle block template.");
            return;
        }

        GameObject root = new GameObject("Level02_Reused");
        GameObject islandRoot = new GameObject("Rotating Island");
        islandRoot.transform.SetParent(root.transform, false);

        Transform focus = new GameObject("Level02Focus").transform;
        focus.SetParent(root.transform, false);
        focus.position = new Vector3(2f, 2f, 0f);

        Camera camera = FindMainCamera();
        CameraController cameraController = camera.GetComponent<CameraController>();
        if (cameraController == null)
            cameraController = camera.gameObject.AddComponent<CameraController>();

        cameraController.controlledCamera = camera;
        cameraController.focusPoint = focus;
        cameraController.orthographicSize = 9f;
        cameraController.distance = 35f;
        cameraController.SetQuarterTurnImmediate(0);

        Vector3 targetJunctionWorld = new Vector3(-3f, 2f, 0f);
        Vector3 assembledUpperPosition = targetJunctionWorld - camera.transform.forward * 6f;

        GameObject upperTower = new GameObject("UpperTowerMovingHalf");
        upperTower.transform.SetParent(root.transform, false);
        upperTower.transform.position = assembledUpperPosition + new Vector3(0f, 4.5f, 3f);

        GameObject farIslandRoot = new GameObject("FarIsland");
        farIslandRoot.transform.SetParent(root.transform, false);
        farIslandRoot.transform.position = assembledUpperPosition + new Vector3(8.5f, 0f, 0f);

        Material white = CreateTintedMaterial(template, new Color(.92f, .94f, 1f, 1f));
        Material blue = CreateTintedMaterial(template, new Color(.24f, .46f, .92f, 1f));
        Material purple = CreateTintedMaterial(template, new Color(.48f, .22f, .82f, 1f));
        Material pink = CreateTintedMaterial(template, new Color(.90f, .36f, .72f, 1f));

        Walkable n01 = CloneNode(template, "L2_01_Start", islandRoot.transform, new Vector3(0f, 0f, 0f), white);
        Walkable n02 = CloneNode(template, "L2_02_Lower", islandRoot.transform, new Vector3(1.5f, 0f, 0f), blue);
        Walkable n03 = CloneNode(template, "L2_03_Lower", islandRoot.transform, new Vector3(3f, 0f, 0f), purple);
        Walkable n04 = CloneNode(template, "L2_04_Lower", islandRoot.transform, new Vector3(4.5f, 1f, 0f), pink);
        Walkable n05 = CloneNode(template, "L2_05_Junction", islandRoot.transform, new Vector3(3f, 2f, 0f), white);
        Walkable n06 = CloneNode(template, "L2_06_Gallery", islandRoot.transform, new Vector3(4.5f, 1.5f, 1.5f), blue);
        Walkable n07 = CloneNode(template, "L2_07_Control", islandRoot.transform, new Vector3(4.5f, 2f, 3f), purple);

        Walkable n08 = CloneNode(template, "L2_08_Upper", upperTower.transform, Vector3.zero, pink);
        Walkable n09 = CloneNode(template, "L2_09_Upper", upperTower.transform, new Vector3(1.5f, 1f, 0f), white);
        Walkable n10 = CloneNode(template, "L2_10_Upper", upperTower.transform, new Vector3(3f, 2f, 0f), blue);
        Walkable n11 = CloneNode(template, "L2_11_BridgeBase", upperTower.transform, new Vector3(4.5f, 3f, 0f), purple);

        Walkable n12 = CloneNode(template, "L2_12_Bridge_A", upperTower.transform, new Vector3(5.7f, 3f, 0f), pink);
        Walkable n13 = CloneNode(template, "L2_13_Bridge_B", upperTower.transform, new Vector3(7.1f, 3f, 0f), blue);
        n12.transform.localScale = new Vector3(.05f, .5f, 1.6f);
        n13.transform.localScale = new Vector3(.05f, .5f, 1.6f);

        Walkable n14 = CloneNode(template, "L2_14_FarEdge", farIslandRoot.transform, new Vector3(0f, 3f, 0f), white);
        Walkable n15 = CloneNode(template, "L2_15_Far", farIslandRoot.transform, new Vector3(1.5f, 3f, 0f), purple);
        Walkable n16 = CloneNode(template, "L2_16_Float", farIslandRoot.transform, new Vector3(3f, 4.2f, 0f), blue);
        Walkable n17 = CloneNode(template, "L2_17_Approach", farIslandRoot.transform, new Vector3(4.5f, 4.2f, 0f), pink);
        Walkable n18 = CloneNode(template, "L2_18_Goal", farIslandRoot.transform, new Vector3(6f, 4.2f, 0f), white);
        n18.isGoal = true;

        Link(n01, n02, true);
        Link(n02, n03, true);
        Link(n03, n04, true);
        Link(n04, n05, true);
        Link(n05, n06, true);
        Link(n06, n07, true);
        Link(n07, n05, true);

        Link(n05, n08, false);
        Link(n08, n09, false);
        Link(n09, n10, false);
        Link(n10, n11, false);
        Link(n11, n12, false);
        Link(n12, n13, false);
        Link(n13, n14, false);

        Link(n14, n15, true);
        Link(n15, n16, true);
        Link(n16, n17, true);
        Link(n17, n18, true);

        List<Walkable> upperNodes = new List<Walkable> { n08, n09, n10, n11 };
        List<Walkable> bridgeNodes = new List<Walkable> { n12, n13 };
        List<Walkable> farNodes = new List<Walkable> { n14, n15, n16, n17, n18 };
        List<Walkable> allNodes = new List<Walkable>
        {
            n01, n02, n03, n04, n05, n06, n07,
            n08, n09, n10, n11, n12, n13,
            n14, n15, n16, n17, n18
        };

        if (oldLevel != null)
            oldLevel.SetActive(false);

        if (props != null)
            props.SetActive(false);

        if (environment != null)
            environment.SetActive(false);

        PlayerController player = Object.FindObjectOfType<PlayerController>();
        if (player != null)
        {
            player.transform.SetParent(root.transform, true);
            player.transform.position = n01.transform.position + new Vector3(0f, .5f, 0f);
            player.currentCube = null;
            player.clickedCube = null;
            player.RayCastDown();
        }

        GameManager manager = Object.FindObjectOfType<GameManager>();
        if (manager != null)
        {
            manager.player = player;
            manager.pathConditions = new List<PathCondition>();
            manager.pivots = new List<Transform>();
            manager.objectsToHide = new Transform[0];
            manager.cameraController = cameraController;
            manager.levelFocus = focus;
            manager.cameraSize = 9f;
            manager.allowCameraRotation = false;
            manager.allowPivotRotation = false;
        }

        GameObject mechanism = new GameObject("Level02Mechanism");
        mechanism.transform.SetParent(root.transform, false);
        Level02Controller controller = mechanism.AddComponent<Level02Controller>();
        controller.Configure(
            camera,
            upperTower.transform,
            assembledUpperPosition,
            n05,
            n08,
            upperNodes,
            bridgeNodes,
            farNodes,
            allNodes);

        IslandRotator rotator = mechanism.AddComponent<IslandRotator>();
        rotator.islandRoot = islandRoot.transform;
        rotator.levelController = controller;

        n07.onReached.AddListener(controller.ActivateSplitTower);
    }

    private static GameObject FindBlockTemplate(GameObject oldLevel)
    {
        if (oldLevel == null)
            return null;

        Transform[] transforms = oldLevel.GetComponentsInChildren<Transform>(true);
        for (int i = 0; i < transforms.Length; i++)
        {
            Transform candidate = transforms[i];
            if (candidate.name == "middle" &&
                candidate.GetComponentInChildren<MeshRenderer>() != null &&
                candidate.GetComponent<Walkable>() == null)
            {
                return candidate.gameObject;
            }
        }

        return null;
    }

    private static Walkable CloneNode(
        GameObject template,
        string name,
        Transform parent,
        Vector3 localPosition,
        Material material)
    {
        GameObject clone = Object.Instantiate(template, parent, false);
        clone.name = name;
        clone.transform.localPosition = localPosition;
        clone.transform.localRotation = Quaternion.identity;
        clone.transform.localScale = new Vector3(1.6f, .5f, 1.6f);

        Renderer[] renderers = clone.GetComponentsInChildren<Renderer>();
        for (int i = 0; i < renderers.Length; i++)
            renderers[i].material = material;

        if (clone.GetComponentInChildren<Collider>() == null)
            clone.AddComponent<BoxCollider>();

        Walkable walkable = clone.AddComponent<Walkable>();
        walkable.possiblePaths = new List<WalkPath>();
        walkable.movingGround = true;
        return walkable;
    }

    private static Material CreateTintedMaterial(GameObject template, Color color)
    {
        Renderer renderer = template.GetComponentInChildren<Renderer>();
        Material source = renderer != null ? renderer.sharedMaterial : null;
        Material material = source != null ? new Material(source) : new Material(Shader.Find("Standard"));

        if (material.HasProperty("_Color"))
            material.color = color;

        return material;
    }

    private static Camera FindMainCamera()
    {
        Camera[] cameras = Camera.allCameras;
        for (int i = 0; i < cameras.Length; i++)
        {
            if (cameras[i] != null && cameras[i].name == "Main Camera")
                return cameras[i];
        }

        return Camera.main;
    }

    private static void Link(Walkable first, Walkable second, bool active)
    {
        AddEdge(first, second, active);
        AddEdge(second, first, active);
    }

    private static void AddEdge(Walkable from, Walkable to, bool active)
    {
        from.possiblePaths.Add(new WalkPath
        {
            target = to.transform,
            active = active
        });
    }
}
