import os
import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from parse import parse_slots
from config import configs


load_dotenv()
BASE_URL = configs["BASE_URL"]
LOGIN_URL = configs["LOGIN_URL"]
CARTYPE_URL = configs["CARTYPE_URL"]
RESERVE_LIST_URL = configs["RESERVE_LIST_URL"]
UA = configs["UA"]

session = requests.Session()

step = 0

# hiddenを拾うヘルパー
def hiddens(html_bytes):
    soup = BeautifulSoup(html_bytes.decode("cp932"), "html.parser")
    return {i["name"]: i.get("value", "")  for i in soup.select("input[type=hidden]") if i.get("name")}

# とってきたレスポンスを保存するヘルパー
def dump(resp, name):
    global step
    step += 1
    path = f"samples/{step:02d}_{name}.html"
    with open(path, "wb") as f:
        f.write(resp.content)
    print(f"[{step:02d}] {name} status={resp.status_code} len={len(resp.content)} -> {path}")
    return resp

def post(url, fields, referer):
    body = urlencode(fields, encoding="cp932")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": referer,
        "Origin": "https://dk.ncors.com",
        "User-Agent": UA,
    }

    return session.post(url, data=body, headers=headers)


def fetch_html(pre_res, pre_url, url, fields):
    body = hiddens(pre_res.content)
    body.update(fields)
    return dump(post(f"{BASE_URL}{url}",body,f"{BASE_URL}{pre_url}"), url) 


def fetch_reserve_html() -> bytes:
    USER = os.environ["NCORS_USER"]
    PASS = os.environ["NCORS_PASS"]
    # ログインページを取得する
    # ログインページにあるcookieを使い、ログイン先ページにアクセスする
    res = dump(session.get(f"{BASE_URL}{LOGIN_URL}"), LOGIN_URL)
    res = fetch_html(res, LOGIN_URL, CARTYPE_URL, {"USERID": USER, "USERPASSWD": PASS})
    assert USER in res.content.decode("cp932"), "ログイン失敗"
    res = fetch_html(res, CARTYPE_URL, RESERVE_LIST_URL, {"CARTYPE": "002"})
    return res.content


if __name__ == "__main__":
    print(parse_slots(fetch_reserve_html()))