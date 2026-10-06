using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class GameSessionManager : MonoBehaviour
{
    public static GameSessionManager Instance { get; private set; }

    private const string HighestUnlockedKey = "MV.Progress.HighestUnlocked";
    private const string LastLevelKey = "MV.Progress.LastLevel";

    public LevelCatalog catalog;
    public LevelUIController ui;

    public bool IsPaused { get; private set; }
    public int CurrentLevelIndex { get; private set; }

    public LevelDefinition CurrentLevel
    {
        get { return catalog != null ? catalog.GetLevel(CurrentLevelIndex) : null; }
    }

    public int HighestUnlockedIndex
    {
        get { return Mathf.Max(0, PlayerPrefs.GetInt(HighestUnlockedKey, 0)); }
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    private static void EnsureInstance()
    {
        if (Instance != null)
            return;

        GameObject root = new GameObject("GameSessionManager");
        root.AddComponent<GameSessionManager>();
    }

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        DontDestroyOnLoad(gameObject);

        if (catalog == null)
            catalog = Resources.Load<LevelCatalog>("LevelCatalog");

        if (catalog == null)
            catalog = CreateFallbackCatalog();

        EnsureUi();
    }

    private void OnEnable()
    {
        SceneManager.sceneLoaded += HandleSceneLoaded;
    }

    private void OnDisable()
    {
        SceneManager.sceneLoaded -= HandleSceneLoaded;
    }

    private void Start()
    {
        ResolveCurrentScene();
    }

    public bool IsUnlocked(int levelIndex)
    {
        return levelIndex >= 0 && levelIndex <= HighestUnlockedIndex;
    }

    public void LoadLevel(int levelIndex)
    {
        if (catalog == null)
            return;

        LevelDefinition level = catalog.GetLevel(levelIndex);
        if (level == null || !IsUnlocked(levelIndex))
            return;

        CurrentLevelIndex = levelIndex;
        IsPaused = false;
        PlayerPrefs.SetInt(LastLevelKey, levelIndex);
        PlayerPrefs.Save();

        if (ui != null)
            ui.HideAllOverlays();

        if (ui != null)
            ui.FadeOut(.35f, () => SceneManager.LoadSceneAsync(level.sceneName));
        else
            SceneManager.LoadSceneAsync(level.sceneName);
    }

    public void LoadNextLevel()
    {
        int nextIndex = CurrentLevelIndex + 1;
        if (catalog != null && nextIndex < catalog.levels.Count)
            LoadLevel(nextIndex);
    }

    public void RestartCurrentLevel()
    {
        IsPaused = false;
        if (ui != null)
            ui.HideAllOverlays();

        if (ui != null)
            ui.FadeOut(.35f, () => SceneManager.LoadSceneAsync(SceneManager.GetActiveScene().name));
        else
            SceneManager.LoadSceneAsync(SceneManager.GetActiveScene().name);
    }

    public void CompleteCurrentLevel()
    {
        int nextIndex = CurrentLevelIndex + 1;
        bool hasNext = catalog != null && nextIndex < catalog.levels.Count;

        if (hasNext && HighestUnlockedIndex < nextIndex)
        {
            PlayerPrefs.SetInt(HighestUnlockedKey, nextIndex);
            PlayerPrefs.Save();
        }

        if (ui != null)
        {
            ui.FadeOut(.45f, () =>
            {
                ui.ShowCompletion(hasNext);
                ui.FadeIn(.45f);
            });
        }
    }

    public void TogglePause()
    {
        SetPaused(!IsPaused);
    }

    public void SetPaused(bool paused)
    {
        IsPaused = paused;

        if (ui != null)
            ui.ShowPause(paused);
    }

    public void ShowLevelSelect()
    {
        IsPaused = false;
        if (ui != null)
        {
            ui.ShowPause(false);
            ui.ShowLevelSelect();
        }
    }

    public void HideLevelSelect()
    {
        if (ui != null)
            ui.HideLevelSelect();
    }

    public void ResetProgress()
    {
        PlayerPrefs.DeleteKey(HighestUnlockedKey);
        PlayerPrefs.DeleteKey(LastLevelKey);
        PlayerPrefs.Save();
    }

    private void HandleSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        ResolveCurrentScene();
    }

    private void ResolveCurrentScene()
    {
        if (catalog == null)
            return;

        int index = catalog.IndexOfScene(SceneManager.GetActiveScene().name);
        if (index >= 0)
            CurrentLevelIndex = index;

        IsPaused = false;

        if (ui != null)
        {
            LevelDefinition level = CurrentLevel;
            ui.SetLevelName(level != null ? level.displayName : SceneManager.GetActiveScene().name);
            ui.HideAllOverlays();
            ui.FadeIn(.35f);
            ui.RefreshLevelButtons();
        }
    }

    private void EnsureUi()
    {
        if (ui != null)
            return;

        ui = GetComponent<LevelUIController>();
        if (ui == null)
            ui = gameObject.AddComponent<LevelUIController>();

        ui.Initialize(this);
    }

    private LevelCatalog CreateFallbackCatalog()
    {
        LevelDefinition first = ScriptableObject.CreateInstance<LevelDefinition>();
        first.name = "Level 01";
        first.levelId = "level-01";
        first.displayName = "Level 01";
        first.sceneName = "SampleScene";

        LevelDefinition second = ScriptableObject.CreateInstance<LevelDefinition>();
        second.name = "Level 02";
        second.levelId = "level-02";
        second.displayName = "Level 02";
        second.sceneName = "Level02";

        first.nextLevel = second;

        LevelCatalog runtimeCatalog = ScriptableObject.CreateInstance<LevelCatalog>();
        runtimeCatalog.name = "Runtime Level Catalog";
        runtimeCatalog.levels = new List<LevelDefinition> { first, second };
        return runtimeCatalog;
    }
}
