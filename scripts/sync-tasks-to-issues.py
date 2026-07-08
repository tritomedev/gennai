#!/usr/bin/env python3
"""
sync-tasks-to-issues.py

docs/06_knowledge/task-tracker.md のチェックボックス（TASK-XXX付き）を解析し、
GitHub Issueと同期する。

マッチングは「タイトル文字列」ではなく「TASK-ID」で行う。
Issue本文に埋め込む "Task-ID: TASK-XXX" のマーカーで対応関係を管理するため、
タスクの文言を後から編集してもIssueとの対応が壊れない。

ルール:
- 未完了タスク（- [ ] `TASK-XXX` ...）で、対応するOpen Issueが存在しない → 新規作成
- 完了タスク（- [x] `TASK-XXX` ...）で、対応するOpen Issueが存在する → Close する
- セクション見出しをラベルとして利用

前提: gh CLI が使える状態であること（GH_TOKEN環境変数 or gh auth login 済み）
"""

import json
import re
import subprocess

REPO = "tritomedev/gennai"
TRACKER_PATH = "docs/06_knowledge/task-tracker.md"

SECTION_LABEL_MAP = {
    "実機検証タスク": "build",
    "調査タスク": "research",
}

TASK_ID_MARKER = "Task-ID:"


def run_gh(args):
    result = subprocess.run(["gh"] + args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"::warning::gh command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()


def get_open_issues_by_task_id():
    """
    Open Issueの本文から Task-ID: TASK-XXX を抽出し、
    { "TASK-XXX": {"number": N, "title": "..."} } の辞書を返す
    """
    output = run_gh(
        [
            "issue", "list",
            "--repo", REPO,
            "--state", "open",
            "--limit", "300",
            "--json", "number,title,body",
        ]
    )
    if not output:
        return {}

    issues = json.loads(output)
    mapping = {}
    for issue in issues:
        body = issue.get("body") or ""
        match = re.search(rf"{re.escape(TASK_ID_MARKER)}\s*(TASK-\d+)", body)
        if match:
            task_id = match.group(1)
            mapping[task_id] = {"number": issue["number"], "title": issue["title"]}
    return mapping


def parse_tracker(path):
    """
    task-tracker.md を解析し、
    [(task_id, title, checked, label), ...] のリストを返す
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()

    tasks = []
    current_label = None

    for line in content.splitlines():
        heading_match = re.match(r"^##\s+.*?([^\s]+タスク)", line)
        if heading_match:
            section_name = heading_match.group(1)
            current_label = SECTION_LABEL_MAP.get(section_name, None)
            continue

        # 例: - [ ] `TASK-001` genai-webをローカルで動かしてみる
        checkbox_match = re.match(
            r"^-\s+\[( |x|X)\]\s+`(TASK-\d+)`\s+(.+)$", line.strip()
        )
        if checkbox_match:
            checked = checkbox_match.group(1).lower() == "x"
            task_id = checkbox_match.group(2)
            title_raw = checkbox_match.group(3).strip()

            # Markdown装飾を軽く除去
            title = re.sub(r"\*\*(.+?)\*\*", r"\1", title_raw)
            title = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", title)
            title = re.sub(r"`(.+?)`", r"\1", title)
            title = title.strip()

            tasks.append((task_id, title, checked, current_label))

    return tasks


def create_issue(task_id, title, label):
    print(f"  → 作成: {task_id} {title}")
    body = (
        f"task-tracker.md から自動生成されたタスクです。\n\n"
        f"{TASK_ID_MARKER} {task_id}\n"
        f"参照: {TRACKER_PATH}"
    )
    args = [
        "issue", "create",
        "--repo", REPO,
        "--title", f"[{task_id}] {title}",
        "--body", body,
    ]
    if label:
        args += ["--label", label]
    run_gh(args)


def update_issue_title_if_changed(number, current_title, new_title, task_id):
    expected_title = f"[{task_id}] {new_title}"
    if current_title != expected_title:
        print(f"  → タイトル更新: #{number} 「{current_title}」→「{expected_title}」")
        run_gh(
            ["issue", "edit", str(number), "--repo", REPO, "--title", expected_title]
        )


def close_issue(number, task_id, title):
    print(f"  → クローズ: #{number} [{task_id}] {title}")
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

    print("=== 現在のOpen Issue一覧を取得します（Task-ID紐付け） ===")
    open_issues = get_open_issues_by_task_id()
    print(f"Task-ID付きOpen Issue数: {len(open_issues)}")

    created = closed = updated = 0

    for task_id, title, checked, label in tasks:
        existing = open_issues.get(task_id)

        if not checked:
            if existing is None:
                create_issue(task_id, title, label)
                created += 1
            else:
                update_issue_title_if_changed(
                    existing["number"], existing["title"], title, task_id
                )
                updated += 1
        else:
            if existing is not None:
                close_issue(existing["number"], task_id, title)
                closed += 1

    print("")
    print(f"=== 完了: {created}件作成 / {updated}件確認・更新 / {closed}件クローズ ===")


if __name__ == "__main__":
    main()
