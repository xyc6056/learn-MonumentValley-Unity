using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class BuildGame
{
    private const string OutputFolder = "Builds/Windows";
    private const string OutputName = "MonumentValley.exe";

    [MenuItem("Tools/Monument Valley/Build Windows 64")]
    public static void BuildWindows64()
    {
        string projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
        string outputDirectory = Path.Combine(projectRoot, OutputFolder);
        Directory.CreateDirectory(outputDirectory);

        List<string> scenes = new List<string>();
        EditorBuildSettingsScene[] configuredScenes = EditorBuildSettings.scenes;
        for (int i = 0; i < configuredScenes.Length; i++)
        {
            if (configuredScenes[i] != null && configuredScenes[i].enabled)
                scenes.Add(configuredScenes[i].path);
        }

        if (scenes.Count == 0)
            throw new InvalidOperationException("No enabled scenes in Build Settings.");

        BuildPlayerOptions options = new BuildPlayerOptions
        {
            scenes = scenes.ToArray(),
            locationPathName = Path.Combine(outputDirectory, OutputName),
            target = BuildTarget.StandaloneWindows64,
            options = BuildOptions.None
        };

        BuildReport report = BuildPipeline.BuildPlayer(options);
        if (report.summary.result != BuildResult.Succeeded)
        {
            throw new InvalidOperationException(
                "Windows build failed with " + report.summary.totalErrors + " errors.");
        }

        Debug.Log("Windows build completed: " + options.locationPathName);
    }
}
