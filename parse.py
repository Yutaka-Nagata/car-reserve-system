from bs4 import BeautifulSoup

def parse_slots(html_bytes):
        soup = BeautifulSoup(html_bytes.decode("cp932"), "html.parser")
        table = soup.select_one("table.taReserve01")
        free_data = []

        labels = [th.get_text().replace("\u00a0", "").strip() for th in table.select_one("tr").select("th")[1:]]

        for tr in table.select("tr"):
            # 日付を取得
            head = tr.select_one("td.Head")
            if head is not None:
                day = head.get_text().strip()
                for td in tr.select("td.Free"):
                    col = int(td["id"][4:6])
                    if col >= len(labels) or labels[col] == "":
                        continue
                    label = labels[col]
                    free_data.append({"date": day, "period": col+1,"label": label})
        return free_data



if __name__ == "__main__":
    with open("samples/03_reserve_list.html", "rb") as f:
        data = f.read()
    print(parse_slots(data))

    
    
