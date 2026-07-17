# Fast Hatch Pet / 快速孵化宠物

Fast Hatch Pet is a lean, gated workflow for creating a new, validated Codex v2 animated pet from a reference image or a clear character concept.

Fast Hatch Pet 是一套精简且带质量门控的工作流，用于根据参考图片或清晰角色设定，快速制作通过验证的 Codex v2 动画宠物。

## Version 2 / 版本 2

Version 2 turns the lean workflow into enforceable release gates. It adds a 15-call default image-generation budget, a machine-readable dependency guard, deterministic repair routing for chroma and whole-row scale issues, mandatory row 9/10 direction checks before atlas assembly, raw semantic QA before the single despill pass, compact validator output, and scoped cleanup.

版本 2 把“精简建议”升级为可执行门控：默认最多 15 次图片生成；使用机器账本阻止错误阶段继续；绿幕、整体缩放和定位问题优先确定性修复；row 9/10 必须分别通过方向语义检查；原始图集通过方向与连续性预检后才允许执行唯一一次去绿；验证结果只向主上下文输出摘要，并在成功后清理任务型中间文件。

## 中文介绍

### 它解决什么问题

完整的宠物生产流程很容易因为方向错误、动作不连贯、长发或尾巴串到相邻帧、透明背景残留等问题反复返工。本技能把高风险检查前置，并尽可能复用确定性脚本，从而减少无效的图片生成次数、上下文占用和中间文件。

适合：已有明确参考图或角色设定、制作一个全新的标准 Codex v2 宠物。

不适合：修复现有图集、迁移旧版 8×9 图集、非标准渲染协议、品牌探索或复杂手工补帧。这些情况请使用完整的 `$hatch-pet` 技能。

### 核心流程

1. 锁定角色身份、轮廓、配色和必须保留的特征。
2. 先生成并验收 canonical base，再只测试 `idle` 与 `running-right`。
3. 早期动作门控通过后，才生成其余标准动作；只有确认对称安全时才镜像。
4. 先验证四个基准视角；row 9 通过右侧面部半平面检查后才允许生成 row 10，两行均通过后才允许拼装原始图集。
5. 原始图集先通过接触表、标注方向、三轮盲测和连续性预检，再执行唯一一次去绿、v2 验证和最终视觉 QA。

特别防坑：`stable-slots` 只能稳定几何位置，不能证明头发、辫子、尾巴等分离部件属于当前帧。所有使用 `stable-slots` 或含长附属物的动作行，都必须运行 `scripts/check_frame_component_ownership.py`，并检查黑底预览。默认把面积不少于 25 像素的第二透明组件视为硬门控，防止“隔壁一帧的头发凭空出现”。

### 前置条件

- 已安装 `$imagegen` 技能。
- 已安装完整的 `$hatch-pet` 技能。本技能会复用 `$CODEX_HOME/skills/hatch-pet/scripts` 中的生产脚本，不重复内置整套流水线。
- 可用的 Python 与 Pillow；在 Codex 工作区中应优先使用系统返回的捆绑 Python 路径。

### 安装

PowerShell：

```powershell
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
git clone https://github.com/linnnn89/hatch-pet-fast.git (Join-Path $codexRoot 'skills/hatch-pet-fast')
```

macOS / Linux：

```bash
CODEX_ROOT="${CODEX_HOME:-$HOME/.codex}"
git clone https://github.com/linnnn89/hatch-pet-fast.git "$CODEX_ROOT/skills/hatch-pet-fast"
```

### 使用

在请求中明确调用技能并附上参考图片，例如：

```text
$hatch-pet-fast 根据这张参考图制作一个名为 KOTORI 的 Codex v2 宠物。
```

## English

### What it solves

Pet production can waste many retries on wrong facing directions, weak animation, cross-frame hair or tail fragments, and chroma residue. This skill moves high-risk checks earlier and reuses deterministic scripts wherever possible, reducing image-generation calls, context use, and intermediate artifacts.

Use it for one new standard Codex v2 pet when a concrete reference or clear concept already exists.

Use the full `$hatch-pet` skill for existing-atlas repair, 8×9 migration, nonstandard renderer contracts, brand discovery, or complex manual frame work.

### Workflow

1. Lock the character identity, silhouette, palette, and essential features.
2. Approve one canonical base, then gate production with only `idle` and `running-right`.
3. Generate the remaining standard motions only after the early gate passes; mirror only when semantic symmetry is proven.
4. Approve four cardinals; require row 9 facial-half-plane semantics before row 10, and require both look rows before raw atlas assembly.
5. Run raw contact, labeled direction, three-verdict blind, and continuity preflight before the single despill pass, v2 validation, and final visual QA.

Important safeguard: `stable-slots` stabilizes geometry but does not prove that a braid, hair lock, tail, or other detached component belongs to the current frame. Every `stable-slots` or long-appendage row must pass `scripts/check_frame_component_ownership.py` and black-background review. By default, a secondary alpha component of at least 25 pixels is a hard failure. This specifically catches one-frame fragments borrowed from a neighboring pose.

### Requirements

- The `$imagegen` skill.
- The full `$hatch-pet` skill. Fast Hatch Pet reuses the production scripts in `$CODEX_HOME/skills/hatch-pet/scripts` instead of bundling a duplicate pipeline.
- Python and Pillow. In a Codex workspace, prefer the bundled Python path returned by the workspace dependency loader.

### Usage

Invoke the skill explicitly and attach a reference image:

```text
$hatch-pet-fast Create a Codex v2 pet named KOTORI from this reference image.
```

## Repository layout / 仓库结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── commands.md
│   └── failure-matrix.md
└── scripts/
    ├── check_frame_component_ownership.py
    └── fast_run_guard.py
```

`SKILL.md` is the authoritative workflow. The reference files contain deterministic command recipes and failure routing. `check_frame_component_ownership.py` catches cross-slot fragments; `fast_run_guard.py` records attempts and blocks out-of-order expensive stages.

`SKILL.md` 是权威工作流；参考文件提供确定性命令与失败分流。`check_frame_component_ownership.py` 检查跨帧碎片，`fast_run_guard.py` 记录生成次数并阻止越过门槛的昂贵步骤。
