"""空き一覧のHTMLから、空いている枠を取り出す。

bytes を受け取って cp932 でデコードする。文字コードの知識をここに閉じ込めてあるので、
保存したHTMLを食わせればネットワーク無しに試せる。
"""
from bs4 import BeautifulSoup

NBSP = " "


def parse_slots(html_bytes: bytes) -> list:
    soup = BeautifulSoup(html_bytes.decode("cp932"), "html.parser")
    table = soup.select_one("table.taReserve01")
    free_data = []

    # ヘッダ行から列番号 → ラベルを作る。先頭の <th> は日付列なので捨てる。
    # 列は14あるが、ラベルが付くのは10列（1〜10時限目）だけ。残りは空ヘッダで未使用。
    # &nbsp; は get_text(strip=True) では消えないので自分で取り除く。
    labels = [
        th.get_text().replace(NBSP, "").strip()
        for th in table.select_one("tr").select("th")[1:]
    ]

    # 日付と空き枠は同じ <tr> の中にあるので、行単位で回す。
    # 行インデックスで突き合わせると、ヘッダ行の扱いで1行ズレて全部壊れる。
    for tr in table.select("tr"):
        head = tr.select_one("td.Head")
        if head is None:
            continue
        day = head.get_text().strip()  # 例 '10/18(土)'。年は入っていないが曜日が入っている
        for td in tr.select("td.Free"):
            col = int(td["id"][4:6])  # id は 'ID' + 行2桁 + 列2桁
            if col >= len(labels) or labels[col] == "":
                continue  # ラベルの無い列は使われていない
            free_data.append(
                {"date": day, "period": col + 1, "label": labels[col]}
            )
    return free_data


if __name__ == "__main__":
    # 実データではなくフィクスチャを読む。中身が固定なので「6件出るのが正解」と言える。
    # 実データで試したいときは fetch.py を実行する。
    with open("samples/reserve_list_sample.html", "rb") as f:
        data = f.read()
    slots = parse_slots(data)
    for s in slots:
        print(" ", s)
    print(f"{len(slots)}件（フィクスチャの期待値は6件）")
