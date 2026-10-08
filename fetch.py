"""予約サイト（ncors）から空き一覧のHTMLを取ってくる。

2001年製の Classic ASP。送受信ともに Shift_JIS(cp932)、セッションは Cookie と
hidden の併用、ページ表示から3分でセッションが切れる。
詳しい仕様は memory の knowledge/tools/教習所予約サイト（ncors）の仕様について.md。
"""
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from config import configs

load_dotenv()

BASE_URL = configs["BASE_URL"]
LOGIN_URL = configs["LOGIN_URL"]
CARTYPE_URL = configs["CARTYPE_URL"]
RESERVE_LIST_URL = configs["RESERVE_LIST_URL"]
UA = configs["UA"]

# 失敗したときに原因を調べられるよう、取得したHTMLを samples/ に落とす。
# ループで何十回も回るので、既定では落とさない（DUMP=1 で有効）。
DUMP = os.environ.get("DUMP") == "1"


def hiddens(html_bytes: bytes) -> dict:
    """<input type=hidden> を全部 dict にする。

    どれが必須か分からないので全部引き継ぐ。選ぶと必ず漏れる。
    """
    soup = BeautifulSoup(html_bytes.decode("cp932"), "html.parser")
    return {
        i["name"]: i.get("value", "")
        for i in soup.select("input[type=hidden]")
        if i.get("name")
    }


def _post(session, url: str, fields: dict, referer: str):
    # requests の data={...} は UTF-8 でエンコードするため、氏名が化けて
    # エラーも出ないままログイン画面へ戻される。cp932 で自分で組む。
    from urllib.parse import urlencode

    body = urlencode(fields, encoding="cp932")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": referer,
        "Origin": "https://dk.ncors.com",
        "User-Agent": UA,
    }
    return session.post(url, data=body, headers=headers)


def _advance(session, pre_res, pre_url: str, url: str, fields: dict):
    """前のレスポンスの hidden を引き継いで次のページへ進む。"""
    body = hiddens(pre_res.content)
    body.update(fields)
    res = _post(session, f"{BASE_URL}{url}", body, f"{BASE_URL}{pre_url}")
    _dump(res, url)
    return res


def _dump(res, name: str):
    if not DUMP:
        return
    path = f"samples/{name}.html"
    with open(path, "wb") as f:
        f.write(res.content)
    print(f"  dump {name} status={res.status_code} len={len(res.content)} -> {path}")


def fetch_reserve_html() -> bytes:
    """ログインして空き一覧の生バイトを返す。失敗は例外で知らせる。

    デコードしないのは、文字コードの知識を parse 側に閉じ込めるため。
    """
    user = os.environ.get("NCORS_USER", "")
    password = os.environ.get("NCORS_PASS", "")
    if not user or not password:
        raise RuntimeError(
            "NCORS_USER / NCORS_PASS が空です。"
            "ローカルなら .env、GitHub Actions なら Secrets の登録を確認してください"
        )

    # セッションは毎回作り直す。3分で切れるので使い回す意味がなく、
    # 長時間ループで古い Cookie を持ち続ける事故も防げる。
    session = requests.Session()

    res = session.get(f"{BASE_URL}{LOGIN_URL}")
    _dump(res, "01_login")

    res = _advance(
        session, res, LOGIN_URL, CARTYPE_URL,
        {"USERID": user, "USERPASSWD": password},
    )

    # ログインに失敗しても HTTP 200 でログイン画面が返ってくる。
    # ログイン画面にはパスワード欄があり、ログイン後には無い、という差で判定する。
    html = res.content.decode("cp932")
    if "USERPASSWD" in html:
        raise RuntimeError("ログイン失敗（ログイン画面が返ってきた）")
    if "CARTYPE" not in html:
        raise RuntimeError("車種選択画面ではない（サイトの構造が変わった可能性）")

    res = _advance(session, res, CARTYPE_URL, RESERVE_LIST_URL, {"CARTYPE": "002"})
    return res.content


if __name__ == "__main__":
    from parse import parse_slots

    data = fetch_reserve_html()
    print(f"取得: {len(data)} バイト")
    for s in parse_slots(data):
        print(" ", s)
