#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
deploy_skills.py — 把 skill_sources 里的占位符源版本，替换成本机实际路径，
部署到豆包运行时 skill 根（.user_skills），使 skill 生效。

占位符（在源 SKILL.md / references/*.md 中使用，Git 仓库里只存占位符版，不泄漏本机路径）：
  {{PROJECT_ROOT}}  → 项目根目录（含 00_项目总纲.md、03_图像资产\ 等）
  {{SKILL_ROOT}}    → 豆包运行时 skill 根目录（...\workspace\.user_skills）

用法（示例）：
  python deploy_skills.py ^
      --source-dir "E:\...\00_制作控制\skill_sources" ^
      --project-root "E:\...\肉身塔传说" ^
      --skill-root "C:\...\workspace\.user_skills" ^
      --dry-run

  --dry-run  仅打印将要部署的文件，不写入。建议先跑一次确认。
"""

import argparse
import os
import shutil
import sys

PLACEHOLDER_PROJECT_ROOT = "{{PROJECT_ROOT}}"
PLACEHOLDER_SKILL_ROOT = "{{SKILL_ROOT}}"


def resolve_path(value: str) -> str:
    """展开环境变量与用户主目录符，并规范化反斜杠。"""
    value = os.path.expandvars(value)
    value = os.path.expanduser(value)
    return value.replace("/", "\\")


def process_content(text: str, project_root: str, skill_root: str) -> str:
    text = text.replace(PLACEHOLDER_PROJECT_ROOT, project_root)
    text = text.replace(PLACEHOLDER_SKILL_ROOT, skill_root)
    return text


def collect_files(skill_dir: str):
    """返回相对路径列表（含 SKILL.md、references 等所有待替换文件）。"""
    files = []
    for root, _, names in os.walk(skill_dir):
        for name in names:
            rel = os.path.relpath(os.path.join(root, name), skill_dir)
            files.append(rel)
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy placeholder skills to .user_skills with real paths.")
    ap.add_argument("--source-dir", required=True, help="skill_sources 目录（占位符源版本）")
    ap.add_argument("--project-root", required=True, help="项目根目录，替换 {{PROJECT_ROOT}}")
    ap.add_argument("--skill-root", required=True, help="豆包运行时 skill 根目录，替换 {{SKILL_ROOT}}")
    ap.add_argument("--dry-run", action="store_true", help="仅打印，不写入")
    args = ap.parse_args()

    source_dir = resolve_path(args.source_dir)
    project_root = resolve_path(args.project_root)
    skill_root = resolve_path(args.skill_root)

    if not os.path.isdir(source_dir):
        print(f"[ERROR] source-dir not found: {source_dir}", file=sys.stderr)
        return 1
    if not os.path.isdir(project_root):
        print(f"[ERROR] project-root not found: {project_root}", file=sys.stderr)
        return 1
    if not os.path.isdir(skill_root):
        print(f"[ERROR] skill-root not found: {skill_root}", file=sys.stderr)
        return 1

    skill_names = [d for d in os.listdir(source_dir)
                   if os.path.isdir(os.path.join(source_dir, d))]
    if not skill_names:
        print("[WARN] no skill directories found under source-dir", file=sys.stderr)

    planned = []
    for name in skill_names:
        src_skill = os.path.join(source_dir, name)
        rel_files = collect_files(src_skill)
        for rel in rel_files:
            planned.append((name, rel))

    if args.dry_run:
        print("[DRY-RUN] 将部署以下文件：")
        for name, rel in planned:
            print(f"  {name} / {rel}")
        print(f"[DRY-RUN] PROJECT_ROOT -> {project_root}")
        print(f"[DRY-RUN] SKILL_ROOT   -> {skill_root}")
        return 0

    for name in sorted(set(n for n, _ in planned)):
        src_skill = os.path.join(source_dir, name)
        dst_skill = os.path.join(skill_root, name)
        os.makedirs(dst_skill, exist_ok=True)
        for rel in sorted(set(r for n, r in planned if n == name)):
            src_file = os.path.join(src_skill, rel)
            dst_file = os.path.join(dst_skill, rel)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            with open(src_file, "r", encoding="utf-8") as f:
                content = f.read()
            content = process_content(content, project_root, skill_root)
            with open(dst_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  deployed: {name} / {rel}")

    print("\n[OK] 部署完成。运行时副本已写入 .user_skills，含本机真实路径。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
