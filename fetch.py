import os
import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from parse import parse_slots

load_dotenv()
USER = os.environ["NCORS_USER"]
PASS = os.environ["NCORS_PASS"]
BASE_URL = os.environ["BASE_URL"]
LOGIN_URL = os.environ["LOGIN_URL"]
CARTYPE_URL = os.environ["CARTYPE_URL"]
RESERVE_LIST_URL = os.environ["RESERVE_LIST_URL"]
UA = os.environ["UA"]

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


if __name__ == "__main__":
    # ログインページを取得する
    # ログインページにあるcookieを使い、ログイン先ペー時にアクセスする
    res = dump(session.get(f"{BASE_URL}{LOGIN_URL}"), LOGIN_URL)
    res = fetch_html(res, LOGIN_URL, CARTYPE_URL, {"USERID": USER, "USERPASSWD": PASS})
    res = fetch_html(res, CARTYPE_URL, RESERVE_LIST_URL, {"CARTYPE": "002"})
    print(parse_slots(res.content))


    # fields = hiddens(res.content)
    # fields.update({"USERID": USER, "USERPASSWD": PASS})
    # res = dump(post(f"{BASE_URL}{CARTYPE_URL}",fields,f"{BASE_URL}{LOGIN_URL}"), "after_login") 
    # fields = hiddens(res.content)
    # fields.update({"CARTYPE": "002"})
    # res = dump(post(f"{BASE_URL}{RESERVE_LIST_URL}",fields,f"{BASE_URL}{CARTYPE_URL}"), "reserve_list") 
    # print(parse_slots(res.content))

    # fetch_html(LOGIN_URL, {"USERID": USER, "USERPASSWD": PASS})
