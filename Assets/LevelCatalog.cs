using System.Collections.Generic;
using UnityEngine;

[CreateAssetMenu(menuName = "Monument Valley/Level Catalog", fileName = "LevelCatalog")]
public class LevelCatalog : ScriptableObject
{
    public List<LevelDefinition> levels = new List<LevelDefinition>();

    public int IndexOfScene(string sceneName)
    {
        if (string.IsNullOrEmpty(sceneName) || levels == null)
            return -1;

        for (int i = 0; i < levels.Count; i++)
        {
            if (levels[i] != null && levels[i].sceneName == sceneName)
                return i;
        }

        return -1;
    }

    public LevelDefinition GetLevel(int index)
    {
        if (levels == null || index < 0 || index >= levels.Count)
            return null;

        return levels[index];
    }
}
