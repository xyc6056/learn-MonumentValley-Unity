using System;
using UnityEngine;
using DG.Tweening;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class LevelUIController : MonoBehaviour
{
    private static readonly Color PanelBackdrop = new Color(.045f, .025f, .085f, .76f);
    private static readonly Color CardBackground = new Color(.14f, .075f, .24f, .98f);
    private static readonly Color HudBackground = new Color(.06f, .035f, .12f, .78f);
    private static readonly Color AccentPink = new Color(.93f, .43f, .80f, 1f);
    private static readonly Color ButtonNormal = new Color(.58f, .28f, .78f, 1f);
    private static readonly Color ButtonHover = new Color(.89f, .48f, .78f, 1f);
    private static readonly Color ButtonPressed = new Color(.44f, .20f, .62f, 1f);
    private static readonly Color DisabledButton = new Color(.28f, .22f, .34f, .75f);
    private static readonly Color BodyText = new Color(.96f, .92f, 1f, 1f);
    private static readonly Color MutedText = new Color(.82f, .75f, .92f, 1f);
    private GameSessionManager session;
    private Font font;

    private Text levelNameText;
    private GameObject completionPanel;
    private Text completionTitleText;
    private Button nextButton;
    private GameObject levelSelectPanel;
    private RectTransform levelButtonRoot;
    private GameObject pausePanel;
    private Image fadeOverlay;

    public void Initialize(GameSessionManager owner)
    {
        session = owner;
        font = Resources.GetBuiltinResource<Font>("Arial.ttf");

        if (font == null)
            font = Font.CreateDynamicFontFromOSFont("Arial", 20);

        EnsureEventSystem();
        EnsureCanvas();
        BuildHud();
        BuildCompletionPanel();
        BuildPausePanel();
        BuildLevelSelectPanel();
        BuildFadeOverlay();
    }

    public void SetLevelName(string levelName)
    {
        if (levelNameText != null)
            levelNameText.text = levelName;
    }

    public void ShowCompletion(bool hasNext)
    {
        if (completionPanel == null)
            return;

        if (completionTitleText != null)
            completionTitleText.text = hasNext ? "Level Complete" : "Chapter Complete";

        if (nextButton != null)
            nextButton.gameObject.SetActive(hasNext);

        completionPanel.SetActive(true);
    }

    public void ShowPause(bool visible)
    {
        if (pausePanel != null)
            pausePanel.SetActive(visible);
    }

    public void ShowLevelSelect()
    {
        if (levelSelectPanel == null)
            return;

        if (completionPanel != null)
            completionPanel.SetActive(false);

        RefreshLevelButtons();
        levelSelectPanel.SetActive(true);
    }

    public void HideLevelSelect()
    {
        if (levelSelectPanel != null)
            levelSelectPanel.SetActive(false);
    }

    public void HideAllOverlays()
    {
        if (completionPanel != null)
            completionPanel.SetActive(false);

        if (levelSelectPanel != null)
            levelSelectPanel.SetActive(false);

        if (pausePanel != null)
            pausePanel.SetActive(false);
    }

    public void FadeOut(float duration, Action onComplete)
    {
        if (fadeOverlay == null)
        {
            if (onComplete != null)
                onComplete();
            return;
        }

        fadeOverlay.gameObject.SetActive(true);
        fadeOverlay.transform.SetAsLastSibling();
        fadeOverlay.raycastTarget = true;
        fadeOverlay.DOKill();
        Color color = fadeOverlay.color;
        color.a = 0f;
        fadeOverlay.color = color;
        fadeOverlay.DOFade(1f, duration).SetEase(Ease.InOutSine).OnComplete(() =>
        {
            if (onComplete != null)
                onComplete();
        });
    }

    public void FadeIn(float duration)
    {
        if (fadeOverlay == null)
            return;

        fadeOverlay.gameObject.SetActive(true);
        fadeOverlay.transform.SetAsLastSibling();
        fadeOverlay.raycastTarget = false;
        fadeOverlay.DOKill();
        Color color = fadeOverlay.color;
        color.a = 1f;
        fadeOverlay.color = color;
        fadeOverlay.DOFade(0f, duration).SetEase(Ease.InOutSine).OnComplete(() => fadeOverlay.gameObject.SetActive(false));
    }

    private void BuildFadeOverlay()
    {
        GameObject overlay = CreatePanel("Fade", transform, new Color(.03f, .015f, .06f, 0f));
        fadeOverlay = overlay.GetComponent<Image>();
        fadeOverlay.raycastTarget = false;
        overlay.SetActive(false);
    }

    public void RefreshLevelButtons()
    {
        if (levelButtonRoot == null || session == null || session.catalog == null)
            return;

        for (int i = levelButtonRoot.childCount - 1; i >= 0; i--)
            Destroy(levelButtonRoot.GetChild(i).gameObject);

        int count = session.catalog.levels.Count;
        int columns = count <= 3 ? 1 : 2;
        float width = 280f;
        float height = 68f;
        float gapX = 28f;
        float gapY = 18f;

        for (int i = 0; i < count; i++)
        {
            int levelIndex = i;
            LevelDefinition level = session.catalog.GetLevel(i);
            bool unlocked = session.IsUnlocked(i);
            string label = level != null ? level.displayName : "Level " + (i + 1);

            if (!unlocked)
                label += "  [Locked]";

            int column = i % columns;
            int row = i / columns;
            float totalWidth = columns * width + (columns - 1) * gapX;
            float startX = -totalWidth * .5f + width * .5f;

            Button button = CreateButton(
                "Level " + (i + 1),
                levelButtonRoot,
                label,
                new Vector2(startX + column * (width + gapX), 20f - row * (height + gapY)),
                new Vector2(width, height),
                unlocked ? (UnityEngine.Events.UnityAction)(() => session.LoadLevel(levelIndex)) : null);

            button.interactable = unlocked;
        }
    }

    private void EnsureEventSystem()
    {
        if (EventSystem.current != null)
            return;

        GameObject eventSystemObject = new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
        eventSystemObject.transform.SetParent(transform, false);
    }

    private void EnsureCanvas()
    {
        Canvas canvas = GetComponent<Canvas>();
        if (canvas == null)
            canvas = gameObject.AddComponent<Canvas>();

        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;

        CanvasScaler scaler = GetComponent<CanvasScaler>();
        if (scaler == null)
            scaler = gameObject.AddComponent<CanvasScaler>();

        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920f, 1080f);
        scaler.matchWidthOrHeight = .5f;

        if (GetComponent<GraphicRaycaster>() == null)
            gameObject.AddComponent<GraphicRaycaster>();
    }

    private void BuildHud()
    {
        RectTransform hud = CreateRect("HUD", transform, new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(16f, -6f), new Vector2(420f, 74f));
        hud.pivot = new Vector2(0f, 1f);

        Image hudBackground = hud.gameObject.AddComponent<Image>();
        hudBackground.color = HudBackground;
        hudBackground.raycastTarget = false;

        RectTransform accent = CreateRect("Accent", hud, new Vector2(0f, 0f), new Vector2(1f, 0f), Vector2.zero, new Vector2(0f, 3f));
        Image accentImage = accent.gameObject.AddComponent<Image>();
        accentImage.color = AccentPink;
        accentImage.raycastTarget = false;

        levelNameText = CreateText(
            "Level Name",
            hud,
            "Level 01",
            28,
            TextAnchor.MiddleLeft,
            new Vector2(20f, 0f),
            new Vector2(280f, 52f),
            new Vector2(0f, .5f));

        CreateButton("Pause", hud, "Pause", new Vector2(352f, 0f), new Vector2(96f, 42f), () => session.TogglePause());
    }

    private void BuildCompletionPanel()
    {
        completionPanel = CreatePanel("Completion", transform, PanelBackdrop);
        completionPanel.SetActive(false);

        RectTransform card = CreatePanelCard("Completion Card", completionPanel.transform, new Vector2(600f, 320f));
        completionTitleText = CreateText(
            "Title",
            card,
            "Level Complete",
            42,
            TextAnchor.MiddleCenter,
            new Vector2(0f, 80f),
            new Vector2(460f, 70f),
            new Vector2(.5f, .5f));

        nextButton = CreateButton("Next", card, "Next", new Vector2(-190f, -55f), new Vector2(170f, 60f), () => session.LoadNextLevel());
        CreateButton("Retry", card, "Retry", new Vector2(0f, -55f), new Vector2(170f, 60f), () => session.RestartCurrentLevel());
        CreateButton("Levels", card, "Levels", new Vector2(190f, -55f), new Vector2(170f, 60f), () => session.ShowLevelSelect());
    }

    private void BuildPausePanel()
    {
        pausePanel = CreatePanel("Pause", transform, PanelBackdrop);
        pausePanel.SetActive(false);

        RectTransform card = CreatePanelCard("Pause Card", pausePanel.transform, new Vector2(480f, 340f));
        CreateText("Title", card, "Paused", 40, TextAnchor.MiddleCenter, new Vector2(0f, 105f), new Vector2(400f, 60f), new Vector2(.5f, .5f));
        CreateButton("Resume", card, "Resume", new Vector2(-105f, 30f), new Vector2(190f, 56f), () => session.TogglePause());
        CreateButton("Restart", card, "Restart", new Vector2(105f, 30f), new Vector2(190f, 56f), () => session.RestartCurrentLevel());
        CreateButton("Levels", card, "Levels", new Vector2(-105f, -48f), new Vector2(190f, 56f), () => session.ShowLevelSelect());
        CreateButton("Quit", card, "Quit", new Vector2(105f, -48f), new Vector2(190f, 56f), () => session.QuitGame());
    }

    private void BuildLevelSelectPanel()
    {
        levelSelectPanel = CreatePanel("Level Select", transform, PanelBackdrop);
        levelSelectPanel.SetActive(false);

        RectTransform card = CreatePanelCard("Level Select Card", levelSelectPanel.transform, new Vector2(660f, 480f));
        CreateText("Title", card, "Select Level", 40, TextAnchor.MiddleCenter, new Vector2(0f, 180f), new Vector2(560f, 60f), new Vector2(.5f, .5f));
        CreateButton("Close", card, "Back", new Vector2(0f, -190f), new Vector2(200f, 58f), () => session.HideLevelSelect());

        GameObject rootObject = new GameObject("Buttons", typeof(RectTransform));
        levelButtonRoot = rootObject.GetComponent<RectTransform>();
        levelButtonRoot.SetParent(card, false);
        levelButtonRoot.anchorMin = new Vector2(.5f, .5f);
        levelButtonRoot.anchorMax = new Vector2(.5f, .5f);
        levelButtonRoot.pivot = new Vector2(.5f, .5f);
        levelButtonRoot.anchoredPosition = new Vector2(0f, -10f);
        levelButtonRoot.sizeDelta = new Vector2(620f, 300f);
    }

    private RectTransform CreatePanelCard(string name, Transform parent, Vector2 size)
    {
        RectTransform card = CreateRect(name, parent, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, size);
        Image image = card.gameObject.AddComponent<Image>();
        image.color = CardBackground;

        RectTransform accent = CreateRect("Accent", card, new Vector2(0f, 1f), new Vector2(1f, 1f), Vector2.zero, new Vector2(0f, 5f));
        accent.pivot = new Vector2(.5f, 1f);
        Image accentImage = accent.gameObject.AddComponent<Image>();
        accentImage.color = AccentPink;
        accentImage.raycastTarget = false;

        return card;
    }

    private GameObject CreatePanel(string name, Transform parent, Color color)
    {
        RectTransform rect = CreateRect(name, parent, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
        Image image = rect.gameObject.AddComponent<Image>();
        image.color = color;
        return rect.gameObject;
    }

    private Text CreateText(
        string name,
        Transform parent,
        string value,
        int size,
        TextAnchor anchor,
        Vector2 position,
        Vector2 dimensions,
        Vector2 objectAnchor)
    {
        RectTransform rect = CreateRect(name, parent, objectAnchor, objectAnchor, position, dimensions);
        Text text = rect.gameObject.AddComponent<Text>();
        text.font = font;
        text.text = value;
        text.fontSize = size;
        text.alignment = anchor;
        text.color = BodyText;
        text.horizontalOverflow = HorizontalWrapMode.Wrap;
        text.verticalOverflow = VerticalWrapMode.Overflow;
        return text;
    }

    private Button CreateButton(
        string name,
        Transform parent,
        string label,
        Vector2 position,
        Vector2 dimensions,
        UnityEngine.Events.UnityAction onClick)
    {
        RectTransform rect = CreateRect(name, parent, new Vector2(.5f, .5f), new Vector2(.5f, .5f), position, dimensions);
        Image image = rect.gameObject.AddComponent<Image>();
        image.color = Color.white;

        Button button = rect.gameObject.AddComponent<Button>();
        button.targetGraphic = image;
        button.navigation = new Navigation { mode = Navigation.Mode.None };

        ColorBlock colors = button.colors;
        colors.normalColor = ButtonNormal;
        colors.highlightedColor = ButtonHover;
        colors.pressedColor = ButtonPressed;
        colors.disabledColor = DisabledButton;
        button.colors = colors;

        Text text = CreateText("Label", rect, label, 22, TextAnchor.MiddleCenter, Vector2.zero, dimensions, new Vector2(.5f, .5f));
        text.raycastTarget = false;

        if (onClick != null)
            button.onClick.AddListener(onClick);

        return button;
    }

    private RectTransform CreateRect(
        string name,
        Transform parent,
        Vector2 anchorMin,
        Vector2 anchorMax,
        Vector2 anchoredPosition,
        Vector2 sizeDelta)
    {
        GameObject child = new GameObject(name, typeof(RectTransform));
        RectTransform rect = child.GetComponent<RectTransform>();
        rect.SetParent(parent, false);
        rect.anchorMin = anchorMin;
        rect.anchorMax = anchorMax;
        rect.pivot = anchorMin == anchorMax ? anchorMin : new Vector2(.5f, .5f);
        rect.anchoredPosition = anchoredPosition;
        rect.sizeDelta = sizeDelta;
        return rect;
    }
}
