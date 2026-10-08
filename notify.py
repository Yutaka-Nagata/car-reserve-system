"""空き枠をメールで通知する。

文面を作る部分（build_*）と送る部分（send）を分けてある。
文面作りは純粋関数なので、メールを1通も送らずに何度でも試せる。
"""
import os

import requests
from dotenv import load_dotenv

from config import configs
from timetable import now_jst, period_time

load_dotenv()

SUBJECT_PREFIX = "[教習空き]"
RESERVE_PAGE = f"{configs['BASE_URL']}{configs['LOGIN_URL']}"

# 1 を入れると送信せず標準出力に出す。文面を固めるときに使う。
DRY_RUN = os.environ.get("DRY_RUN") == "1"


def _format_slot(slot: dict) -> str:
    start, end = period_time(slot["date"], slot["period"])
    when = f" {start}-{end}" if start else ""
    return f"{slot['date']} {slot['period']}限{when}"


def build_message(slots: list):
    """空き枠の通知。空のリストで呼ぶのは呼び出し側のバグなので例外にする。

    「空きはありません」を定期的に送ると、本物の通知が埋もれて仕組みが死ぬ。
    動いていることの確認は、異常時だけ鳴る build_broken_message が担当する。
    """
    if not slots:
        raise ValueError("空のリストで build_message を呼ばないこと")

    slots = sorted(slots, key=lambda s: (s["date"], s["period"]))
    first = slots[0]

    # 件名にいちばん近い枠を入れる。スマホの通知で見えるのは件名だけなので、
    # 開く前に「行けるか」を判断できるようにする。
    suffix = "" if len(slots) == 1 else " ほか"
    subject = (
        f"{SUBJECT_PREFIX} {len(slots)}件 "
        f"直近 {first['date']}{first['period']}限{suffix}"
    )

    lines = [_format_slot(s) for s in slots]
    body = (
        "\n".join(lines)
        + f"\n\n予約 ➤ {RESERVE_PAGE}"
        + f"\n\n検知 {now_jst():%m/%d %H:%M}"
    )
    return subject, body


def build_broken_message(reason: str):
    """監視そのものが壊れたときの通知。

    壊れているのに通知が来ず「空きがないだけ」と思い込むのが最も怖いので、
    異常は必ず鳴らす。
    """
    subject = f"{SUBJECT_PREFIX} ⚠️ 監視が止まっています"
    lines = [reason, "", f"検知 {now_jst():%m/%d %H:%M}"]

    # GitHub Actions が入れてくれる環境変数から、実行ログへのリンクを作る
    server = os.environ.get("GITHUB_SERVER_URL")
    repo = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if server and repo and run_id:
        lines += ["", f"ログ ➤ {server}/{repo}/actions/runs/{run_id}"]
    return subject, "\n".join(lines)


def send(subject: str, body: str):
    """失敗したら例外を投げる。呼び出し側が state を更新しないで済むように。"""
    if DRY_RUN:
        print("--- DRY_RUN（送信しません）---")
        print(f"件名: {subject}")
        print(body)
        print("-----------------------------")
        return

    api_key = os.environ.get("RESEND_API_KEY", "")
    to = os.environ.get("TO_EMAIL", "")
    if not api_key or not to:
        raise RuntimeError(
            "RESEND_API_KEY / TO_EMAIL が空です。"
            "ローカルなら .env、GitHub Actions なら Secrets の登録を確認してください"
        )

    res = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": "onboarding@resend.dev",
            "to": [to],
            "subject": subject,
            "text": body,
        },
        timeout=30,
    )
    res.raise_for_status()


if __name__ == "__main__":
    print("=== 複数件 ===")
    slots = [
        {"date": "10/14(水)", "period": 1, "label": "1時限目"},
        {"date": "10/11(土)", "period": 6, "label": "6時限目"},
        {"date": "10/11(土)", "period": 3, "label": "3時限目"},
    ]
    s, b = build_message(slots)
    print(f"件名: {s}\n{b}")

    print("\n=== 1件 ===")
    s, b = build_message([{"date": "10/18(土)", "period": 5, "label": "5時限目"}])
    print(f"件名: {s}\n{b}")

    print("\n=== 故障通知 ===")
    s, b = build_broken_message("5回連続で取得に失敗しました: ログイン失敗（ログイン画面が返ってきた）")
    print(f"件名: {s}\n{b}")

    print("\n=== 空リスト ===")
    try:
        build_message([])
    except ValueError as e:
        print(f"  ValueError: {e}")
