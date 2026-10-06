using UnityEngine;
using UnityEngine.SceneManagement;

public static class SecondLevelPalette
{
    private static readonly Color GroundPurple = new Color(.46f, .22f, .76f, 1f);
    private static readonly Color DetailPurple = new Color(.64f, .42f, .94f, 1f);

    public static void Apply()
    {
        string sceneName = SceneManager.GetActiveScene().name;
        if (sceneName != "Scene 2" && !sceneName.StartsWith("Scene 2_"))
            return;

        Renderer[] renderers = Object.FindObjectsOfType<Renderer>();
        for (int i = 0; i < renderers.Length; i++)
        {
            Renderer renderer = renderers[i];
            if (renderer == null || renderer.sharedMaterial == null)
                continue;

            string materialName = renderer.sharedMaterial.name;
            if (materialName != "Ground" &&
                materialName != "TexturedCube" &&
                materialName != "New Material")
            {
                continue;
            }

            Material purpleMaterial = new Material(renderer.sharedMaterial);
            if (!purpleMaterial.HasProperty("_Color"))
                continue;

            purpleMaterial.color = materialName == "TexturedCube" ? DetailPurple : GroundPurple;
            renderer.material = purpleMaterial;
        }
    }
}
