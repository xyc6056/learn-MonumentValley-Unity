using UnityEngine;

[CreateAssetMenu(menuName = "Monument Valley/Level Definition", fileName = "LevelDefinition")]
public class LevelDefinition : ScriptableObject
{
    public string levelId = "level-01";
    public string displayName = "Level 01";
    public string sceneName = "SampleScene";
    public LevelDefinition nextLevel;
}
