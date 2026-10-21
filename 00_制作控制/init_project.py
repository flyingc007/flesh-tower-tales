#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
init_project.py — 新项目脚手架：一条命令搭起 AI 视频项目骨架并自动引入机制。

自动完成：
  1. 创建项目目录骨架（00_制作控制/01_剧本/02_分镜脚本/03_图像资产/04_分镜视频/shared/bak）
  2. 生成 00_项目总纲.md 初稿（红线/角色/场景/形态区分/备用资产 五节）
  3. 生成 03_图像资产/资产清单.md 初稿（人物/神兽备用/场景 三表 + 一致性约定）
  4. 生成并部署项目总控 skill <en>-producer 到豆包运行时 skill 根（含触发词、
     引用通用层 character-reference-lock、占位符 {{PROJECT_ROOT}}/{{SKILL_ROOT}}）
  5. 可选：初始化本地 git 仓库

用法（示例）：
  python init_project.py --name "新项目名" --en new-project \
      --triggers "主角A,配角B,场景C,分镜" \
      --dest "E:\\projects\\新项目名" \
      --skill-root "C:\\...\\workspace\\.user_skills" \
      --git

  --name        项目中文名（必填）
  --en          项目英文短名，决定总控 skill 名 <en>-producer（必填，小写连字符）
  --triggers    触发词，逗号分隔：项目名+全部角色名+全部场景名+关键事件词（必填）
  --dest        项目根目录（默认当前目录/<name>）
  --skill-root  豆包运行时 skill 根目录（...\.user_skills）；不填则只生成源版本不部署
  --git         布尔开关：带则 git init -b main，不带则跳过（它不接受值，不是仓库名）
"""

import argparse
import os
import shutil
import subprocess
import sys

# ---------------- 内嵌模板 ----------------

TEMPLATE_TOTAL_GANG = """# 《{{PROJECT_NAME}}》项目总纲

> 本文件是整个项目的**唯一设定基准**。任何后续创作、修改、生成，都必须以此为准。改动需更新版本号，避免设定漂移。

## 一、项目基本信息
| 项目 | 内容 |
| ---- | ---- |
| 项目名称 | {{PROJECT_NAME}} |
| 故事依据 | {{原著/剧本来源，见 01_剧本}} |
| 核心主旨 | {{一句话剧情主线}} |
| 美术基调 | {{如：国风神话写实，统一光影}} |
| 呈现形式 | 分镜逐镜头 AI 视频生成，后期合成 |

## 二、故事核心红线（严禁违反）
1. 严格忠于原著，不擅自增删剧情、不新增原著没有的人物对白与桥段。
2. {{待填：主角定位}}
3. {{待填：关键道具/事件必须形态}}

## 三、角色资产清单
| 角色 | 形象定位 | 锚定图状态 | 存放位置 |
| ---- | ---- | ---- | ---- |
| {{待填角色A}} | {{形象定位}} | ✅待归位 | 03_图像资产/人物/{{待填角色A}} |

## 四、场景资产清单
| 场景 | 说明 | 状态 | 存放位置 |
| ---- | ---- | ---- | ---- |
| {{待填场景A}} | {{说明}} | ✅待归位 | 03_图像资产/场景 |

## 五、角色出现形态区分（极易出错，务必牢记）
| 出现位置 | 形态 |
| ---- | ---- |
| {{位置1}} | {{形态1，含关键视觉特征}} |

> ⚠️ 两种形态**不可混用**。

## 六、备用/待定资产（暂不进镜头，为后续扩展准备）
| 资产 | 定位 | 依据 | 状态 | 存放位置 |
| ---- | ---- | ---- | ---- | ---- |
| {{备用资产名}} | {{设定定位}} | 传说设定（非本片原著桥段） | 🔒备用，暂不进镜头 | 03_图像资产/{{备用目录}} |

> 规则：备用资产**不进入当前角色/场景清单**，避免设定漂移与"新增桥段"红线冲突；启用时更新状态并登记对应镜头。

---
版本记录：
- v1.0（建立）：确定剧本、分镜框架、资产清单与区分规则
"""

TEMPLATE_ASSET_LIST = """# 《{{PROJECT_NAME}}》· 图像资产清单

> 状态约定：✅已归位 = 锚定图已存放且可用；🔒备用 = 已归位但暂不进镜头。
> **改文件夹必同步改本清单**（总控第 2 步强制检查一致性）。

## 人物资产
| 子文件夹 | 存放内容 | 状态 | 锚点文件 | 用途镜头 |
| ---- | ---- | ---- | ---- | ---- |
| {{待填角色}} | {{形象定位}} | ✅待归位 |  |  |

## 神兽/备用资产（暂不进镜头）
| 子文件夹 | 存放内容 | 状态 | 锚点文件 | 用途镜头 |
| ---- | ---- | ---- | ---- | ---- |
| {{待填备用}} | {{设定定位}} | 🔒备用，待启用 |  | 待定 |

## 场景资产
| 子文件夹 | 存放内容 | 状态 | 锚点文件 | 用途镜头 |
| ---- | ---- | ---- | ---- | ---- |
| {{待填场景}} | {{说明}} | ✅待归位 |  |  |
"""

TEMPLATE_PRODUCER_SKILL = r"""---
name: {{PROJECT_EN}}-producer
description: 《{{PROJECT_NAME}}》项目的制作总控。当任何涉及该项目的内容生成（分镜生成、图像生成、视频生成、资产取用、角色复用）时使用，负责"读项目总纲 → 定位资产 → 应用角色锁定 → 产出"的整条链路。解决"生成时不知依据哪个文档、不知去哪找角色/场景资产、角色形态混用、锚定图被魔改"的问题。触发词：{{TRIGGERS}}，或该项目的任何角色/场景名称。使用本 skill 时必须先读项目总纲（唯一设定基准），再定位资产，再套用角色锁定协议。
---

# {{PROJECT_NAME}} · 制作总控

## 触发条件

任何与《{{PROJECT_NAME}}》相关的内容生成任务均触发：分镜脚本执行、角色/场景图像生成、视频生成、资产取用与复用。

## 触发保障（重要）

本 skill 依靠 description 中的关键词触发。执行时提醒用户：生成请求尽量带上项目/角色/场景关键词。若表述完全不含关键词，主动补问是否属于本项目，确认后按本流程执行，避免退回凭记忆取材。

## 强制前置：读项目总纲（唯一设定基准）

第一步必须完整读取：`{{PROJECT_ROOT}}\00_项目总纲.md`

## 核心流程

### 第 1 步：读总纲
完整读取 `00_项目总纲.md`，冲突以总纲为准。

### 第 2 步：定位资产
按总纲清单，从 `{{PROJECT_ROOT}}\03_图像资产\` 定位锚定图，缺失如实报告。

**清单一致性检查（强制）**：对照 `03_图像资产\资产清单.md` 与实际文件夹，若发现不一致（文件夹有清单未登记 / 清单登记但文件夹缺 / 状态、锚点、v 号不符），**向用户报告差异并提示更新清单**，不得静默跳过。原则：改文件夹必同步改清单。

### 第 3 步：应用角色锁定协议
涉及任何角色复用/图生/图生视频时，**必须读取并应用**通用 skill `character-reference-lock`：`{{SKILL_ROOT}}\character-reference-lock`。先 Read 其 SKILL.md，再按其中契约锁定角色、拼接强约束提示词与负面词。

### 第 4 步：执行角色形态区分（红线，极易出错）
按总纲第五节严格执行，两种形态**不可混用**。生成前先确认镜头处于哪个空间，再选定形态。

## 红线清单（生成时逐项检查）

{{从总纲第二节复制红线，逐条列出}}

## 输出与交付

- 图像/视频按用户指定方式交付。
- 涉及新资产或设定调整，提示更新 `00_项目总纲.md` 版本号。

## 协作提示

- 资产索引在**本地目录**（03_图像资产），资产查找一律以总纲清单 + 本地目录为准。
"""

# ---------------- 工具函数 ----------------

def fill(text, **kwargs):
    for key, val in kwargs.items():
        text = text.replace("{{" + key + "}}", val)
    return text


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def write_text(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  create: {path}")


# ---------------- 主流程 ----------------

def main() -> int:
    ap = argparse.ArgumentParser(description="AI 视频项目脚手架：搭骨架并自动引入机制")
    ap.add_argument("--name", required=True, help="项目中文名（必填）")
    ap.add_argument("--en", required=True, help="项目英文短名，决定 <en>-producer skill 名（必填）")
    ap.add_argument("--triggers", required=True, help="触发词，逗号分隔：项目名+角色名+场景名+关键事件词")
    ap.add_argument("--dest", help="项目根目录（默认 <当前目录>/<name>）")
    ap.add_argument("--skill-root", help="豆包运行时 skill 根（...\\.user_skills）；不填则只生成源不部署")
    ap.add_argument("--git", action="store_true", help="布尔开关：初始化本地 git 仓库")
    args = ap.parse_args()

    project_name = args.name
    project_en = args.en
    triggers = args.triggers

    dest = args.dest if args.dest else os.path.join(os.getcwd(), project_name)
    dest = dest.replace("/", "\\")
    dest_abs = os.path.abspath(dest)

    print(f"== 初始化项目「{project_name}」 @ {dest_abs} ==")

    # 1. 目录骨架
    print("[1/5] 创建目录骨架")
    for sub in ("00_制作控制", "01_剧本", "02_分镜脚本",
                "03_图像资产/人物", "03_图像资产/场景", "03_图像资产/备用资产",
                "04_分镜视频", "shared", "bak"):
        ensure_dir(os.path.join(dest_abs, sub))
    print(f"  created {dest_abs} 下的骨架")

    # 2. 总纲初稿
    print("[2/5] 生成 00_项目总纲.md")
    write_text(os.path.join(dest_abs, "00_项目总纲.md"),
               fill(TEMPLATE_TOTAL_GANG, PROJECT_NAME=project_name))

    # 3. 资产清单初稿
    print("[3/5] 生成 03_图像资产/资产清单.md")
    write_text(os.path.join(dest_abs, "03_图像资产", "资产清单.md"),
               fill(TEMPLATE_ASSET_LIST, PROJECT_NAME=project_name))

    # 4. 总控 skill 源版本（占位符，随项目 git）+ 部署运行副本
    print("[4/5] 生成并部署总控 skill <en>-producer")
    src_dir = os.path.join(dest_abs, "00_制作控制", "skill_sources", f"{project_en}-producer")
    skill_src_path = os.path.join(src_dir, "SKILL.md")
    skill_text = fill(TEMPLATE_PRODUCER_SKILL,
                      PROJECT_NAME=project_name,
                      PROJECT_EN=project_en,
                      TRIGGERS=triggers)
    write_text(skill_src_path, skill_text)

    if args.skill_root:
        skill_root = args.skill_root.replace("/", "\\")
        # 部署：占位符替换为本机路径，写入运行时副本
        deployed = skill_text.replace("{{PROJECT_ROOT}}", dest_abs).replace("{{SKILL_ROOT}}", skill_root)
        write_text(os.path.join(skill_root, f"{project_en}-producer", "SKILL.md"), deployed)
        # 校验通用层是否在
        lock_skill = os.path.join(skill_root, "character-reference-lock", "SKILL.md")
        if not os.path.isfile(lock_skill):
            print("[WARN] 运行时 skill 根缺少通用层 character-reference-lock，请先部署通用层。")
        else:
            print(f"  deployed {project_en}-producer -> {skill_root}")
    else:
        print("  (未指定 --skill-root，仅生成源版本，未部署运行时副本)")

    # 5. git
    if args.git:
        print("[5/5] git init")
        r = subprocess.run(["git", "init", "-b", "main"], cwd=dest_abs, capture_output=True, text=True)
        print("  " + (r.stdout.strip() or "git init ok"))
    else:
        print("[5/5] 跳过 git（未带 --git）")

    # 验收提示
    print("\n== 初始化完成。请按验收清单确认 ==")
    print("  [ ] 在 00_项目总纲.md 填真实设定：红线 / 角色清单 / 场景清单 / 形态区分 / 备用资产")
    print("  [ ] 归位锚定图到 03_图像资产（人物/场景/备用），并同步资产清单")
    print("  [ ] 确认总控 skill 触发词已覆盖项目名+角色名+场景名")
    print("  [ ] 若本机缺通用层，先部署 character-reference-lock")
    print("  [ ] 建剧本/分镜（01_剧本 / 02_分镜脚本）")
    print("  [ ] git add/commit；远程仓库名在 GitHub 建（不在本命令里）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
