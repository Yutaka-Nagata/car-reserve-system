from parse import parse_slots
from fetch import fetch_reserve_html
from differ import get_differ, parse_data, save_state
from notify import send, build_message


if __name__ == "__main__":
    data = parse_data(parse_slots(fetch_reserve_html()))
    get_differ(data)
    subject, body = build_message(get_differ(data))
    send(subject, body)
    save_state(data)