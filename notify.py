import requests
import os
from dotenv import load_dotenv
load_dotenv()

def parse_key(key):
    date, period = key.split("|")
    return date, int(period)

def parse_text(slots):
    text = ""
    for slot in slots:
        text = text + slot + "\n"
    return text

def build_message(slots):
    # タイトル
    if len(slots) != 0:
        parsed_slots = [f"{parse_key(slot)[0]} {parse_key(slot)[1]}限" for slot in slots]
        subject =  f"[教習空き] {len(slots)}件 / 最短 {parsed_slots[0]}"
        body = f"【教習所空きコマ通知システム】\n\n・現在の空きコマ\n{parse_text(parsed_slots)}\n予約 ➤ https://dk.ncors.com/min/ncors/login.asp\n"
    else:
        subject = ""
        body = ""
    return subject, body


def send(subject, body):
    if len(subject) > 0:
        res = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {os.environ["RESEND_API_KEY"]}"},
            json={
                "from": "onboarding@resend.dev",
                "to": [os.environ["TO_EMAIL"]],
                "subject": subject,
                "text": body,
            },

        )
        res.raise_for_status()


if __name__ == "__main__":
    dummy_data = ['09/22(火)|3', '09/22(火)|4', '09/24(木)|6']
    subject, body = build_message(dummy_data)
    print(body)
    # send(subject, body)

