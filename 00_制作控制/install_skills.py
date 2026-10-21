#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
install_skills.py — 新电脑一键安装通用 skill 层。

把 skill_sources 下的「通用层」skill（如 character-reference-lock）部署到
豆包运行时 skill 根（.user_skills），免去手敲 Copy。

默认只部署通用层，自动跳过项目总控（目录名以 -producer 结尾）；带 --all 才一并安装。

用法（示例）：
  python install_skills.py --source "<克隆目录>\00_制作控制\skill_sources" \
      --skill-root "C:\...\workspace\.user_skills" \
      --project-root "E:\...\新项目名" \
      --dry-run        # 先预览将安装的 skill

  --source         skill_sources 目录（含通用层源）
  --skill-root     豆包运行时 skill 根（...\.user_skills）
  --project-root   可选，用于替换源中 {{PROJECT_ROOT}} 占位符（通用层通常不含）
  --all            可选，连项目总控（*-producer）一起安装
  --dry-run        仅预览，不写入
"""

import argparse
import os
import sys

PLACEHOLDER_PROJECT_ROOT = "{{PROJECT_ROOT}}"
PLACEHOLDER_SKILL_ROOT = "{{SKILL_ROOT}}"


def resolve_path(value: str) -> str:
    value = os.path.expandvars(value)
    value = os.path.expanduser(value)
    return value.replace("/", "\\")


def is_producer_skill(name: str) -> bool:
    return name.endswith("-producer")


def collect_files(skill_dir: str):
    files = []
    for root, _, names in os.walk(skill_dir):
        for n in names:
            files.append(os.path.relpath(os.path.join(root, n), skill_dir))
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="新电脑一键安装通用 skill 层")
    ap.add_argument("--source", required=True, help="skill_sources 目录")
    ap.add_argument("--skill-root", required=True, help="豆包运行时 skill 根（.user_skills）")
    ap.add_argument("--project-root", help="可选，替换 {{PROJECT_ROOT}} 占位符")
    ap.add_argument("--all", action="store_true", help="连项目总控（*-producer）一起安装")
    ap.add_argument("--dry-run", action="store_true", help="仅预览，不写入")
    args = ap.parse_args()

    source = resolve_path(args.source)
    skill_root = resolve_path(args.skill_root)
    project_root = resolve_path(args.project_root) if args.project_root else None

    if not os.path.isdir(source):
        print(f"[ERROR] source 不存在: {source}", file=sys.stderr)
        return 1
    if not os.path.isdir(skill_root):
        print(f"[ERROR] skill-root 不存在: {skill_root}", file=sys.stderr)
        return 1

    # 列出 skill 目录，并按类型分流
    all_dirs = [d for d in os.listdir(source) if os.path.isdir(os.path.join(source, d))]
    if not all_dirs:
        print("[WARN] source 下没有 skill 目录", file=sys.stderr)

    producers = [d for d in all_dirs if is_producer_skill(d)]
    generics = [d for d in all_dirs if not is_producer_skill(d)]
    targets = all_dirs if args.all else generics

    if not targets:
        print("没有可安装的通用层。")
        return 0

    print("本次将安装的 skill：")
    for name in targets:
        print(f"  - {name}")

    if args.dry_run:
        print(f"[DRY-RUN] 目标 skill-root: {skill_root}")
        return 0

    # 部署
    for name in targets:
        src_skill = os.path.join(source, name)
        dst_skill = os.path.join(skill_root, name)
        os.makedirs(dst_skill, exist_ok=True)
        for rel in collect_files(src_skill):
            src_file = os.path.join(src_skill, rel)
            dst_file = os.path.join(dst_skill, rel)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            with open(src_file, "r", encoding="utf-8") as f:
                content = f.read()
            if PLACEHOLDER_PROJECT_ROOT in content:
                if project_root:
                    content = content.replace(PLACEHOLDER_PROJECT_ROOT, project_root)
                else:
                    print(f"[WARN] {name}/{rel} 含 {PLACEHOLDER_PROJECT_ROOT} 但未给 --project-root，按原样保留")
            if PLACEHOLDER_SKILL_ROOT in content:
                content = content.replace(PLACEHOLDER_SKILL_ROOT, skill_root)
            with open(dst_file, "w", encoding="utf-8") as f:
                f.write(content)
        print(f"  installed: {name}")

    skipped = [d for d in producers if not args.all]
    if skipped:
        print(f"（已跳过项目总控：{', '.join(skipped)}；如需一并安装加 --all）")
    print("\n[OK] 通用层安装完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
