using UnityEngine;
using UnityEngine.SceneManagement;

public static class Level02Bootstrap
{
    private static void Setup()
    {
        if (SceneManager.GetActiveScene().name != "Level02")
            return;

        if (Object.FindObjectOfType<Level02SceneSetup>() != null)
            return;

        GameObject setupObject = new GameObject("Level02Setup");
        setupObject.AddComponent<Level02SceneSetup>();
    }
}
