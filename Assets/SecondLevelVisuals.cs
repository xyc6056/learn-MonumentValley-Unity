using UnityEngine;
using UnityEngine.Rendering;

public static class SecondLevelVisuals
{
    private static readonly Color TopPurple = new Color(.34f, .16f, .58f, 1f);
    private static readonly Color BottomPurple = new Color(.08f, .05f, .16f, 1f);

    public static void Apply()
    {
        string sceneName = UnityEngine.SceneManagement.SceneManager.GetActiveScene().name;
        if (sceneName != "Scene 2" && !sceneName.StartsWith("Scene 2_"))
            return;

        RemoveDecorations();
        ConfigureLighting();
        ConfigureShadows();
        CreateGradientBackground();
    }

    private static void RemoveDecorations()
    {
        GameObject[] objects = Object.FindObjectsOfType<GameObject>();
        for (int i = 0; i < objects.Length; i++)
        {
            GameObject target = objects[i];
            if (target == null)
                continue;

            if (target.name.StartsWith("LilyPad") || target.name.StartsWith("Particle System"))
            {
                if (target.transform.parent != null && target.transform.parent.name == "Indicator")
                    continue;

                target.SetActive(false);
                Object.Destroy(target);
            }
        }
    }

    private static void ConfigureLighting()
    {
        Light[] lights = Object.FindObjectsOfType<Light>();
        Light mainLight = null;

        for (int i = 0; i < lights.Length; i++)
        {
            if (lights[i] != null && lights[i].type == LightType.Directional)
            {
                mainLight = lights[i];
                break;
            }
        }

        if (mainLight != null)
        {
            mainLight.intensity = 1.05f;
            mainLight.color = new Color(1f, .96f, .90f, 1f);
            mainLight.shadows = LightShadows.Soft;
            mainLight.shadowStrength = .55f;
            mainLight.shadowBias = .05f;
            mainLight.shadowNormalBias = .4f;
            mainLight.shadowNearPlane = .1f;
        }

        GameObject fillObject = new GameObject("Purple Fill Light");
        Light fill = fillObject.AddComponent<Light>();
        fill.type = LightType.Directional;
        fill.color = new Color(.62f, .42f, .95f, 1f);
        fill.intensity = .28f;
        fill.shadows = LightShadows.None;
        fillObject.transform.rotation = Quaternion.Euler(24f, 145f, 0f);

        RenderSettings.ambientMode = AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = new Color(.34f, .23f, .54f, 1f);
        RenderSettings.ambientEquatorColor = new Color(.16f, .12f, .28f, 1f);
        RenderSettings.ambientGroundColor = new Color(.05f, .04f, .10f, 1f);
    }

    private static void ConfigureShadows()
    {
        QualitySettings.shadows = ShadowQuality.All;
        QualitySettings.shadowDistance = 70f;
        QualitySettings.shadowCascades = 2;
        QualitySettings.shadowResolution = ShadowResolution.High;

        Renderer[] renderers = Object.FindObjectsOfType<Renderer>();
        for (int i = 0; i < renderers.Length; i++)
        {
            Renderer renderer = renderers[i];
            if (renderer == null || renderer.sharedMaterial == null)
                continue;

            if (renderer.sharedMaterial.renderQueue >= 3000)
                continue;

            renderer.shadowCastingMode = ShadowCastingMode.On;
            renderer.receiveShadows = true;
        }
    }

    private static void CreateGradientBackground()
    {
        Camera camera = FindMainCamera();
        if (camera == null)
            return;

        Transform existing = camera.transform.Find("Gradient Background");
        if (existing != null)
            Object.Destroy(existing.gameObject);

        Shader shader = Resources.Load<Shader>("GradientBackground");
        if (shader == null)
            shader = Shader.Find("MonumentValley/GradientBackground");

        if (shader == null)
            return;

        GameObject background = new GameObject("Gradient Background");
        background.transform.SetParent(camera.transform, false);
        background.transform.localPosition = new Vector3(0f, 0f, Mathf.Min(camera.farClipPlane * .75f, 800f));
        background.transform.localRotation = Quaternion.identity;

        float height = camera.orthographicSize * 2f * 1.25f;
        float width = height * Mathf.Max(1f, camera.aspect) * 1.15f;
        background.transform.localScale = new Vector3(width, height, 1f);

        MeshFilter filter = background.AddComponent<MeshFilter>();
        filter.sharedMesh = CreateQuadMesh();

        Material material = new Material(shader);
        material.SetColor("_TopColor", TopPurple);
        material.SetColor("_BottomColor", BottomPurple);

        MeshRenderer renderer = background.AddComponent<MeshRenderer>();
        renderer.sharedMaterial = material;
        renderer.shadowCastingMode = ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
    }

    private static Mesh CreateQuadMesh()
    {
        Mesh mesh = new Mesh();
        mesh.name = "Gradient Quad";
        mesh.vertices = new[]
        {
            new Vector3(-.5f, -.5f, 0f),
            new Vector3(.5f, -.5f, 0f),
            new Vector3(-.5f, .5f, 0f),
            new Vector3(.5f, .5f, 0f)
        };
        mesh.uv = new[]
        {
            new Vector2(0f, 0f),
            new Vector2(1f, 0f),
            new Vector2(0f, 1f),
            new Vector2(1f, 1f)
        };
        mesh.triangles = new[] { 0, 2, 1, 2, 3, 1 };
        mesh.RecalculateBounds();
        return mesh;
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
}
