using UnityEngine;

public static class LevelValidator
{
    public static void Validate(GameManager manager)
    {
        if (manager == null)
            return;

        int issues = 0;
        Walkable[] nodes = Object.FindObjectsOfType<Walkable>();

        if (nodes.Length == 0)
        {
            Debug.LogWarning("[Monument Valley] Level contains no Walkable nodes.");
            return;
        }

        int goalCount = 0;
        for (int i = 0; i < nodes.Length; i++)
        {
            Walkable node = nodes[i];
            if (node == null)
                continue;

            if (node.isGoal)
                goalCount++;

            if (node.possiblePaths == null)
            {
                Debug.LogWarning("[Monument Valley] Walkable has a null path list: " + node.name, node);
                issues++;
                continue;
            }

            for (int pathIndex = 0; pathIndex < node.possiblePaths.Count; pathIndex++)
            {
                WalkPath path = node.possiblePaths[pathIndex];
                if (path == null || node.GetPathTarget(path) == null)
                {
                    Debug.LogWarning(
                        "[Monument Valley] Invalid path target on " + node.name + " at index " + pathIndex,
                        node);
                    issues++;
                }
            }
        }

        if (goalCount != 1)
        {
            Debug.LogWarning("[Monument Valley] Expected exactly one goal node, found " + goalCount + ".");
            issues++;
        }

        if (manager.allowPivotRotation && (manager.pivots == null || manager.pivots.Count == 0))
        {
            Debug.LogWarning("[Monument Valley] Level has no configured pivots.");
            issues++;
        }

        if (manager.pathConditions == null)
            return;

        for (int groupIndex = 0; groupIndex < manager.pathConditions.Count; groupIndex++)
        {
            PathCondition group = manager.pathConditions[groupIndex];
            if (group == null || group.conditions == null || group.paths == null)
            {
                Debug.LogWarning("[Monument Valley] Invalid path condition group at index " + groupIndex + ".");
                issues++;
                continue;
            }

            for (int pathIndex = 0; pathIndex < group.paths.Count; pathIndex++)
            {
                SinglePath path = group.paths[pathIndex];
                if (path == null || path.block == null || path.block.possiblePaths == null ||
                    path.index < 0 || path.index >= path.block.possiblePaths.Count)
                {
                    Debug.LogWarning(
                        "[Monument Valley] Invalid SinglePath in group '" + group.pathConditionName + "'.",
                        manager);
                    issues++;
                }
            }
        }

        if (issues == 0)
            Debug.Log("[Monument Valley] Level validation passed for " + nodes.Length + " nodes.", manager);
    }
}
