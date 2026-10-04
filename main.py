from parse import parse_slots
from fetch import fetch_reserve_html
from differ import get_differ, parse_data, save_state



if __name__ == "__main__":
    data = parse_data(parse_slots(fetch_reserve_html()))
    print(get_differ(data))
    save_state(data)