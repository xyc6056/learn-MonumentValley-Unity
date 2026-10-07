# Monument Valley Style Unity Puzzle Game

一个《纪念碑谷》风格的非欧几何解谜游戏项目，参考并基于 Mix and Jam 的 Monument Valley Level Design 开源项目继续开发和整理尝试。

项目经历了两个阶段：

1. Python + PyOpenGL 阶段，用于验证等距投影、立方体绘制、鼠标旋转和屏幕空间连通思路。
2. Unity 阶段，基于前期思路完成可玩原型、两关流程、关卡 UI、进度保存和 Windows 打包。

## 项目文档

- [项目汇报文档](Docs/MonumentValley_Project_Report.md)

## 当前功能

- 等距正交相机
- 鼠标点击寻路和角色移动
- 中心枢轴与右侧枢轴旋转
- 相机四向旋转
- 物体角度和相机方向条件连通
- 视觉对齐触发的非欧连接
- 按钮机关
- 两关流程和关卡解锁
- 关卡选择、暂停、重开和退出
- PlayerPrefs 进度保存
- Windows 64 位构建

## 技术栈

- Unity 2019.2.3f1
- C#
- DOTween
- ProBuilder
- uGUI
- Unity Build Pipeline

## 关卡

- 第一关：`Assets/Scenes/SampleScene.unity`
- 第二关：`Assets/Scenes/Scene 2.unity`

## 操作

- 鼠标左键：点击可走方块
- 左右方向键：旋转中心枢轴
- `Q / E`：旋转相机
- 鼠标中键或右键拖拽：旋转相机
- `R`：重开当前关卡
- `Esc`：暂停
- 暂停面板中的 `Quit`：退出游戏
- `Alt + F4`：直接退出游戏

## 本地运行

1. 使用 Unity `2019.2.3f1` 打开项目。
2. 打开 `Assets/Scenes/SampleScene.unity`。
3. 进入 Play Mode。
4. 完成第一关后，点击 `Next` 进入第二关。

## 构建 Windows 版本

在 Unity 编辑器中选择：

```text
Tools > Monument Valley > Build Windows 64
```

或者关闭 Unity 后执行：

```cmd
"D:\unity\Hub\Editor\2019.2.3f1\Editor\Unity.exe" -batchmode -quit -projectPath "D:\MonumentValley\MonumentValley-LevelDesign-master" -executeMethod BuildGame.BuildWindows64 -logFile "D:\MonumentValley\MonumentValley-LevelDesign-master\Builds\UnityBuild.log"
```

构建结果默认输出到：

```text
Builds/Windows/MonumentValley.exe
```

运行时需要保留整个 `Builds/Windows` 文件夹。

## 目录结构

```text
Assets/                  Unity 资源、脚本和场景
ProjectSettings/         Unity 项目设置
Packages/                Unity 包配置
Docs/                    项目汇报
Phase1-Python/           Python + PyOpenGL 第一阶段代码
Builds/                  Windows 构建产物，默认不上传 Git
```

## 来源说明

本项目最初参考并基于 Mix and Jam 的 Monument Valley Level Design 开源项目继续开发和整理。当前仓库中的第二阶段 Unity 原型、关卡流程、UI、视觉调整、构建脚本和课程文档为本人项目实践内容。

## 其他

更多详细介绍可见Docs/MonumentValley_Project_Report.md
