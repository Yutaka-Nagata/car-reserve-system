from parse import parse_slots
from fetch import fetch_reserve_html
from differ import get_differ, parse_data, save_state
from notify import send, build_message


if __name__ == "__main__":
    filtered_free_data = parse_data([free_data for free_data in parse_slots(fetch_reserve_html()) if free_data["period"] not in [9,10]])
    # 予約可能枠があればメール送信しつづけてほしいかも
    if len(filtered_free_data) != 0:
        subject, body = build_message(filtered_free_data)
        send(subject, body)
    else:
        send("空きはありません", "")
    save_state(filtered_free_data)