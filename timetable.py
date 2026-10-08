"""timetable.json を読んで、時限の時刻と「次に見に行く時刻」を計算する。

教習所の時限は平日が10限まで、土日が8限まで。5限・6限の時刻が曜日で違う。
日本はサマータイムが無いので、タイムゾーンは固定オフセット(+9)で正確に扱える。
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))

# 時限の終了から何分後に見に行くか。
# キャンセルは「教習が終わった人が別の枠を取り消す」ことで出るので、終了直後に少し待つ。
CHECK_DELAY_MINUTES = 2

_TT = json.loads(Path(__file__).with_name("timetable.json").read_text(encoding="utf-8"))
MAX_PERIOD = _TT["bookable_max_period"]

_WEEKEND = "土日"


def now_jst() -> datetime:
    return datetime.now(JST)


def _kind_of_weekday(d: datetime) -> str:
    return "weekend" if d.weekday() >= 5 else "weekday"


def _kind_of_label(date_label: str) -> str:
    """'10/18(土)' のような表記から weekday / weekend を判定する。

    予約サイトの日付には曜日が入っているので、年が無くても曜日が分かる。
    （祝日は曜日どおりに扱う。平日扱いになるので、表示する時刻がずれる可能性がある）
    """
    i = date_label.index("(")
    return "weekend" if date_label[i + 1] in _WEEKEND else "weekday"


def is_bookable(slot: dict) -> bool:
    """自分が予約できる枠か。

    平日の9・10限はフルタイムプラン専用で予約できず、土日は8限までしか開講していない。
    よって period <= 8 で曜日に関係なく判定できる（2026-10-04 教習所に電話して確認）。
    """
    return slot["period"] <= MAX_PERIOD


def period_time(date_label: str, period: int):
    """その枠の (開始, 終了) を 'HH:MM' で返す。見つからなければ (None, None)。"""
    for r in _TT["periods"][_kind_of_label(date_label)]:
        if r["period"] == period:
            return r["start"], r["end"]
    return None, None


def check_times(d: datetime) -> list[datetime]:
    """その日に見に行く時刻の一覧。各時限の終了 + CHECK_DELAY_MINUTES。"""
    out = []
    for r in _TT["periods"][_kind_of_weekday(d)]:
        h, m = (int(x) for x in r["end"].split(":"))
        out.append(
            d.replace(hour=h, minute=m, second=0, microsecond=0)
            + timedelta(minutes=CHECK_DELAY_MINUTES)
        )
    return sorted(out)


def next_check_at(now: datetime):
    """now より後で、同じ日のうちに来る次の『見に行く時刻』。もう無ければ None。"""
    for t in check_times(now):
        if t > now:
            return t
    return None


if __name__ == "__main__":
    print(f"予約できる上限の時限: {MAX_PERIOD}限")
    print()
    for label, d in [
        ("平日", datetime(2026, 10, 8, 9, 0, tzinfo=JST)),   # 木
        ("土曜", datetime(2026, 10, 10, 9, 0, tzinfo=JST)),  # 土
    ]:
        ts = check_times(d)
        print(f"{label}（{d:%m/%d(%a)}）の見に行く時刻 {len(ts)}回:")
        print("  " + " ".join(f"{t:%H:%M}" for t in ts))
    print()
    for t in ["08:00", "10:30", "15:30", "19:40", "19:55", "23:00"]:
        h, m = (int(x) for x in t.split(":"))
        now = datetime(2026, 10, 8, h, m, tzinfo=JST)
        nxt = next_check_at(now)
        print(f"  いま {t} → 次は {nxt:%H:%M}" if nxt else f"  いま {t} → 本日分は終了")
