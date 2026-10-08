"""1回の起動で、その日の時限の切れ目を順に見に行って監視する。

GitHub Actions の cron は起動時刻を保証しない（実測で平均42分遅れ、大半が実行されず）。
一方、起動してしまえば中の sleep は正確に効く。そこで「何度も起動する」のではなく
「1回起動して長く居座る」形にしてある。

この方式の副産物として、前回の状態をメモリで持てるので状態ファイルが不要になり、
リポジトリへの書き戻しとその競合も消えている。
"""
import os
import time

from differ import find_new, to_keys
from fetch import fetch_reserve_html
from notify import build_broken_message, build_message, send
from parse import parse_slots
from timetable import is_bookable, next_check_at, now_jst

# ジョブの上限は6時間なので、それより手前で自分から終わる
MAX_RUNTIME_SEC = int(os.environ.get("MAX_RUNTIME_SEC", 5.5 * 3600))

# 恒久的な障害（ログインが通らない等）を何時間も繰り返さないための打ち切り
MAX_FAIL_STREAK = 5

# テスト用。FIXTURE があればサイトへ行かずそのファイルを読む。ONCE=1 で1周だけ。
FIXTURE = os.environ.get("FIXTURE")
ONCE = os.environ.get("ONCE") == "1"


def _get_html() -> bytes:
    if FIXTURE:
        with open(FIXTURE, "rb") as f:
            return f.read()
    return fetch_reserve_html()


def _sleep_until_next(started_mono: float) -> bool:
    """次の時限の切れ目まで待つ。もう待たずに終わるべきなら False を返す。"""
    nxt = next_check_at(now_jst())
    if nxt is None:
        print("本日分の時限がすべて終わりました。終了します")
        return False

    wait = (nxt - now_jst()).total_seconds()
    if time.monotonic() - started_mono + wait > MAX_RUNTIME_SEC:
        print(f"次は {nxt:%H:%M} ですが、ジョブの上限時間を超えるため終了します")
        return False

    print(f"次は {nxt:%H:%M}（{wait / 60:.0f}分後）まで待機します", flush=True)
    time.sleep(wait)
    return True


def main() -> int:
    start = now_jst()
    print(f"起動 {start:%m/%d(%a) %H:%M:%S} JST")

    # ONCE は手動の1回チェックなので、稼働時間の判定を飛ばす
    if not ONCE and next_check_at(start) is None:
        print("本日の稼働時間を過ぎています。何もせず終了します")
        return 0

    started_mono = time.monotonic()
    seen = None
    fail_streak = 0

    while True:
        try:
            slots = parse_slots(_get_html())
            fail_streak = 0
        except Exception as e:
            fail_streak += 1
            print(f"[{now_jst():%H:%M:%S}] 取得失敗 {fail_streak}/{MAX_FAIL_STREAK}: {e}", flush=True)
            if fail_streak >= MAX_FAIL_STREAK:
                reason = f"{MAX_FAIL_STREAK}回連続で取得に失敗しました: {e}"
                send(*build_broken_message(reason))
                print("故障通知を送信しました")
                return 1
            if ONCE or not _sleep_until_next(started_mono):
                return 1
            continue

        if seen is None:
            # 起動直後。前のループが止まっていた間（夜間など）に出た枠を取り逃がさないため、
            # いまある空きをそのまま通知対象にする
            new = slots
        else:
            new = find_new(seen, slots)

        bookable = [s for s in new if is_bookable(s)]
        print(
            f"[{now_jst():%H:%M:%S}] 空き{len(slots)}件 "
            f"/ 新規{len(new)}件 / 通知対象{len(bookable)}件"
        )
        for s in slots:
            mark = "●" if is_bookable(s) else "×"
            print(f"    {mark} {s['date']} {s['period']}限")

        if bookable:
            # 失敗すれば例外が飛び、seen を更新しないまま落ちる。
            # つまり次の周回で同じ枠をもう一度通知する（取り逃がす方向には壊れない）
            send(*build_message(bookable))
            print("    → 通知を送信しました")

        seen = to_keys(slots)  # 通知の後に更新する

        if ONCE:
            print("ONCE=1 なので1周で終了します")
            return 0
        if not _sleep_until_next(started_mono):
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
