#!/usr/bin/env python3
"""
sync-tasks-to-issues.py

docs/06_knowledge/task-tracker.md のチェックボックスを解析し、GitHub Issueと同期する。

ルール:
- 未完了タスク（- [ ]）で、同名タイトルのOpen Issueが存在しない → 新規作成
- 完了タスク（- [x]）で、同名タイトルのOpen Issueが存在する → Close する
- セクション見出し（## 🔧 実機検証タスク 等）をラベルとして利用

前提: 環境変数 GITHUB_TOKEN が設定済み、gh CLI が使える状態であること
"""

import re
import subprocess
import sys

REPO = "tritomedev/gennai"
TRACKER_PATH = "docs/06_knowledge/task-tracker.md"

# セクション見出し → ラベルのマッピング
SECTION_LABEL_MAP = {
    "実機検証タスク": "build",
    "調査タスク": "research",
}


def run_gh(args):
    result = subprocess.run(
        ["gh"] + args, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        print(f"::warning::gh command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()


def get_open_issue_titles():
    """現在Openな全Issueのタイトル一覧を取得"""
    output = run_gh(
        [
            "issue", "list",
            "--repo", REPO,
            "--state", "open",
            "--limit", "200",
            "--json", "title,number",
        ]
    )
    import json
    if not output:
        return {}
    issues = json.loads(output)
    return {issue["title"]: issue["number"] for issue in issues}


def parse_tracker(path):
    """
    task-tracker.md を解析し、
    [(title, checked: bool, label: str), ...] のリストを返す
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()

    tasks = []
    current_label = None

    for line in content.splitlines():
        # セクション見出し検出
        heading_match = re.match(r"^##\s+.*?([^\s]+タスク)", line)
        if heading_match:
            section_name = heading_match.group(1)
            current_label = SECTION_LABEL_MAP.get(section_name, None)
            continue

        # チェックボックス検出
        checkbox_match = re.match(r"^-\s+\[( |x|X)\]\s+(.+)$", line.strip())
        if checkbox_match:
            checked = checkbox_match.group(1).lower() == "x"
            title_raw = checkbox_match.group(2).strip()
            # Markdown装飾（**太字**、リンク等）を簡易除去してタイトル化
            title = re.sub(r"\*\*(.+?)\*\*", r"\1", title_raw)
            title = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", title)
            title = re.sub(r"`(.+?)`", r"\1", title)
            title = title.strip()
            if title:
                tasks.append((title, checked, current_label))

    return tasks


def create_issue(title, label):
    print(f"  → 作成: {title}")
    args = [
        "issue", "create",
        "--repo", REPO,
        "--title", title,
        "--body", f"task-tracker.md から自動生成されたタスクです。\n\n参照: {TRACKER_PATH}",
    ]
    if label:
        args += ["--label", label]
    run_gh(args)


def close_issue(number, title):
    print(f"  → クローズ: #{number} {title}")
    run_gh(
        [
            "issue", "close", str(number),
            "--repo", REPO,
            "--comment", "task-tracker.md でチェック済みになったため自動クローズしました。",
        ]
    )


def main():
    print("=== task-tracker.md を解析します ===")
    tasks = parse_tracker(TRACKER_PATH)
    print(f"検出したタスク数: {len(tasks)}")

    print("=== 現在のOpen Issue一覧を取得します ===")
    open_issues = get_open_issue_titles()
    print(f"Open Issue数: {len(open_issues)}")

    created = 0
    closed = 0

    for title, checked, label in tasks:
        if not checked:
            # 未完了タスク → Issueがなければ作成
            if title not in open_issues:
                create_issue(title, label)
                created += 1
        else:
            # 完了タスク → Issueがあればクローズ
            if title in open_issues:
                close_issue(open_issues[title], title)
                closed += 1

    print("")
    print(f"=== 完了: {created}件作成 / {closed}件クローズ ===")


if __name__ == "__main__":
    main()
