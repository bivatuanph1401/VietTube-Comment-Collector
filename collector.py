import os
import re
import time
import socket
import pandas as pd

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# must match the file name used by your label.py
OUT = os.path.join(BASE_DIR, "comment.csv")

VIDEO_IDS = [
    "1qutSFY-iYg",
    "8zfM8e9EsmQ",
    "1BVjyLsZejg",
    "fnTfJ130mjw",
    "K3F0UJBUik",   # only 10 characters, recopy the full 11-character ID
]

MAX_PER_VIDEO = 2000

socket.setdefaulttimeout(60)


def load_api_key():
    # 1) api_key.txt next to this script
    path = os.path.join(BASE_DIR, "api_key.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    # 2) environment variables
    for name in ("DANHAPAPI", "YOUTUBE_API_KEY"):
        key = os.getenv(name, "").strip()
        if key:
            return key
    return ""


def clean(text):
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = re.sub(r"http\S+|www\.\S+|@\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_comments(yt, video_id, limit):
    rows = []
    token = None

    while len(rows) < limit:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(100, limit - len(rows)),
            "textFormat": "plainText",
        }
        if token:
            params["pageToken"] = token

        for attempt in range(5):
            try:
                response = yt.commentThreads().list(**params).execute(num_retries=2)
                break
            except (OSError, TimeoutError):
                print(f"  network error {attempt + 1}/5")
                if attempt == 4:
                    raise
                time.sleep(3 * (attempt + 1))

        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            text = clean(snippet.get("textDisplay", ""))
            if len(text) > 3:
                rows.append({"text": text})

        token = response.get("nextPageToken")
        if not token:
            break

    return rows


def save_new(rows):
    new = pd.DataFrame(rows, columns=["text"])
    new = new.drop_duplicates(subset=["text"])

    # treat a missing or empty (0 byte) file as a new file
    if os.path.exists(OUT) and os.path.getsize(OUT) > 0:
        old = pd.read_csv(OUT, encoding="utf-8-sig", dtype={"label": "object"})

        if "text" not in old.columns:
            raise ValueError("file has no 'text' column")

        existing_text = set(old["text"].dropna().astype(str))
        new = new[~new["text"].isin(existing_text)]
        df = pd.concat([old, new], ignore_index=True)
    else:
        df = new.copy()
        df["label"] = ""

    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    return len(new), len(df)


def main():
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError(
            "No API key found. Create api_key.txt next to collector.py "
            "and paste your key in it (one line)."
        )

    yt = build("youtube", "v3", developerKey=api_key)
    total_added = 0

    for video_id in VIDEO_IDS:
        if len(video_id) != 11:
            print(f"Skip {video_id}: YouTube IDs have 11 characters")
            continue
        try:
            rows = get_comments(yt, video_id, MAX_PER_VIDEO)
            added, total = save_new(rows)
            total_added += added
            print(f"{video_id}: fetched {len(rows)}, added {added} new, total {total}")

        except HttpError as error:
            details = getattr(error, "error_details", None)
            reason = details[0].get("reason") if details else error.status_code
            print(f"Skip {video_id}: {reason}")   # no key printed
        except Exception as error:
            print(f"Error {video_id}: {type(error).__name__}")

    print(f"\nDone: {total_added} new comments added.")
    print(f"File: {OUT}")


if __name__ == "__main__":
    main()