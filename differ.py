"""前回見た空き枠との差分を取る。

「同じ枠か」を決めるのは日付と時限だけ。label は表示用のおまけなので
同一性の判定には使わない（使うと、教習所が表記を変えた日に全件が「新規」になる）。

1回の実行の中でループして監視するので、前回の状態はメモリ上の集合で足りる。
状態ファイルは持たない（リポジトリへの書き戻しと、その競合が不要になる）。
"""


def slot_key(slot: dict) -> str:
    return f"{slot['date']}|{slot['period']}"


def to_keys(slots) -> set:
    return {slot_key(s) for s in slots}


def find_new(previous_keys: set, current_slots: list) -> list:
    """新しく出現した枠だけを返す。消えた枠は返さない。

    消えた枠を通知しないのは、自分が取った枠かもしれないため。
    返すのは辞書のまま（フィルタと通知が date / period / label を使うので）。
    """
    return [s for s in current_slots if slot_key(s) not in previous_keys]


if __name__ == "__main__":
    A = {"date": "10/08(木)", "period": 10, "label": "10時限目"}
    B = {"date": "10/11(土)", "period": 3, "label": "3時限目"}

    cases = [
        ("前回なし → 両方が新規", set(), [A, B], 2),
        ("前回と同じ → 新規なし", to_keys([A, B]), [A, B], 0),
        ("Bだけ増えた → Bのみ", to_keys([A]), [A, B], 1),
        ("Aが消えた → 新規なし", to_keys([A, B]), [B], 0),
        ("labelだけ変わった → 新規なし", to_keys([A]), [{**A, "label": "10限目"}], 0),
    ]
    ok = True
    for name, prev, cur, expected in cases:
        got = find_new(prev, cur)
        mark = "OK " if len(got) == expected else "NG "
        if len(got) != expected:
            ok = False
        print(f"{mark} {name}: {len(got)}件 {[slot_key(s) for s in got]}")
    print()
    print("すべて期待どおり" if ok else "期待と違う結果があります")
