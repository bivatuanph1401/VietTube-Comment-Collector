
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE_DIR, "comment.csv")

MAP = {
    "1": "negative",
    "2": "neutral",
    "3": "positive"
}

df = pd.read_csv(FILE, encoding="utf-8-sig", dtype={"label": "object"})

if "label" not in df.columns:
    df["label"] = ""

df["label"] = df["label"].fillna("").astype(str).str.strip()

# Chuyen nhan so cu thanh chu
df["label"] = df["label"].replace({
    "1": "negative",
    "2": "neutral",
    "3": "positive"
})

todo = df.index[df["label"] == ""].tolist()

print(f"Con {len(todo)} binh luan chua gan nhan")
print("1 = Negative | 2 = Neutral | 3 = Positive")
print("s = Delete | u = Undo | q = Quit")


def save():
    df.to_csv(FILE, index=False, encoding="utf-8-sig")


history = []
pos = 0
changes = 0

try:
    while pos < len(todo):
        i = todo[pos]

        print(f"\n[{pos + 1}/{len(todo)}] {df.at[i, 'text']}")
        k = input("> ").strip().lower()

        if k in MAP:
            history.append((i, df.at[i, "label"]))
            df.at[i, "label"] = MAP[k]
            pos += 1
            changes += 1

        elif k == "s":
            history.append((i, df.at[i, "label"]))
            df.at[i, "label"] = "deleted"
            pos += 1
            changes += 1

        elif k == "u":
            if history:
                j, old = history.pop()
                df.at[j, "label"] = old
                pos = todo.index(j)
                print("Da hoan tac")
            else:
                print("Khong co thao tac de hoan tac")

        elif k == "q":
            break

        else:
            print("Nhap 1, 2, 3, s, u hoac q")

        # Tu dong luu moi 10 thao tac thay doi
        if changes > 0 and changes % 10 == 0:
            save()
            print("Da tu dong luu!")

finally:
    save()
    print("\nDa luu dataset.")
    print(df["label"].replace("", "(unlabeled)").value_counts())
