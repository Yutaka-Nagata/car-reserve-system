import os
import json
from datetime import datetime, timezone
from parse import parse_slots


def slot_key(slot):
    return f"{slot["date"]}|{slot["period"]}"



def load_state(path="state.json"):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"slots": [], "last_success_at": None}
    

def parse_data(data):
    return [slot_key(d) for d in data]
    

# 差分のslotsを返す
def find_new(previous_slots, current_slots):
    return [s for s in current_slots if s not in previous_slots]

    

def get_differ(current_data):
    previous_data = load_state() # state.jsonを読む
    differ = find_new(previous_data["slots"], current_data)
    return differ

def save_state(data):
    with open("state.json", "w", encoding="utf-8") as f: 
        json.dump(
            {
                "slots": data, 
                "last_success_at": datetime.now(timezone.utc).isoformat()
            }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # ローカルのデータを読みこむ
    def load_html(path):
        with open(path, "rb") as f:
            return f.read()
    current_data = parse_data(parse_slots(load_html("samples/reserve_list_sample.html"))) # あきこまを取得
    print(get_differ(current_data))
    save_state(current_data)
    print(current_data[1].split("|"))

