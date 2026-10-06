using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class RecoveredSceneLinkFix
{
    [InitializeOnLoadMethod]
    private static void Initialize()
    {
        EditorApplication.delayCall += Apply;
    }

    [MenuItem("Tools/Monument Valley/Fix Recovered Scene Links")]
    public static void Apply()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            return;

        Scene scene = SceneManager.GetActiveScene();
        if (!scene.IsValid() || !scene.name.StartsWith("Scene 2"))
            return;

        Dictionary<string, Walkable> nodes = new Dictionary<string, Walkable>();
        Walkable[] walkables = Object.FindObjectsOfType<Walkable>();
        for (int i = 0; i < walkables.Length; i++)
        {
            Walkable node = walkables[i];
            if (node != null && !nodes.ContainsKey(node.name))
                nodes.Add(node.name, node);
        }

        bool changed = false;
        changed |= EnsureLink(nodes, "0", "18final");
        changed |= EnsureLink(nodes, "3 (19)", "8stair (3)");
        changed |= EnsureLink(nodes, "middle (227)", "l_1 (19)");
        changed |= EnsureAllLinks(walkables, "l_1 (19)", "l_1 (21)");

        if (!changed)
            return;

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        Debug.Log("[Monument Valley] Recovered Scene2 links updated and saved.");
    }

    private static bool EnsureLink(
        Dictionary<string, Walkable> nodes,
        string firstName,
        string secondName)
    {
        Walkable first;
        Walkable second;
        if (!nodes.TryGetValue(firstName, out first) ||
            !nodes.TryGetValue(secondName, out second))
        {
            return false;
        }

        bool changed = false;
        changed |= AddMissingEdge(first, second);
        changed |= AddMissingEdge(second, first);
        return changed;
    }

    private static bool EnsureAllLinks(
        Walkable[] walkables,
        string firstName,
        string secondName)
    {
        bool changed = false;
        for (int i = 0; i < walkables.Length; i++)
        {
            Walkable first = walkables[i];
            if (first == null || first.name != firstName)
                continue;

            for (int j = 0; j < walkables.Length; j++)
            {
                Walkable second = walkables[j];
                if (second == null || second.name != secondName)
                    continue;

                changed |= AddMissingEdge(first, second);
                changed |= AddMissingEdge(second, first);
            }
        }

        return changed;
    }

    private static bool AddMissingEdge(Walkable from, Walkable to)
    {
        for (int i = 0; i < from.possiblePaths.Count; i++)
        {
            WalkPath path = from.possiblePaths[i];
            if (path != null && path.target == to.transform)
            {
                if (!path.active)
                {
                    path.active = true;
                    return true;
                }

                return false;
            }
        }

        from.possiblePaths.Add(new WalkPath
        {
            target = to.transform,
            active = true
        });
        return true;
    }
}
