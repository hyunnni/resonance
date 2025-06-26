import json
import sys
import random
import time
import subprocess
from pythonosc import udp_client
import schedule

# ─────────────────────────────────────────────
# 1. 설정값 (필요시 수정)
# ─────────────────────────────────────────────
MAX_CHARS_PER_LINE = 40   # 줄바꿈 기준 글자 수 (원하면 변경)
TOUCHDESIGNER_IP = "10.210.68.14" #IP
TOUCHDESIGNER_PORT = 8000   #포트번호

# JSON 파일 경로
JSON_PATH = "latest_articles_with_sentiment.json"

# news2emotion 실행 옵션
NEWS2EMOTION_CMD = [
    sys.executable,
    "src/api/news2emotion.py",
    "--timespan", "3.0",
    "--num-records", "10",
    "--export-count", "10",
]

# ───────────────────────────────────────────────
# 긴 문자열을 <split> 토큰으로 분할
# ───────────────────────────────────────────────
def insert_splits(text: str, chunk: int = MAX_CHARS_PER_LINE) -> str:
    """
    chunk 단위(예: 30, 60, 90 …)에서 가장 가까운 공백을 찾아 <split> 토큰 삽입
    문장 중간에 공백이 없으면 그대로 둡니다
    """
    if len(text) <= chunk:
        return text

    chars = list(text)
    idx = chunk
    while idx < len(chars):
        # 왼쪽으로 10글자, 오른쪽으로 10글자 범위 내에서 가장 먼저 발견되는 공백 탐색
        window = range(max(idx - 10, 0), min(idx + 10, len(chars)))
        split_pos = next((i for i in window if chars[i] == " "), None)
        if split_pos:
            chars[split_pos] = "<split>"
            idx = split_pos + chunk
        else:
            idx += chunk  # 공백 못 찾으면 그대로 건너뛰기
    return "".join(chars)

# ─────────────────────────────────────────────
# 2. TouchDesigner OSC 클라이언트
# ─────────────────────────────────────────────
client = udp_client.SimpleUDPClient(TOUCHDESIGNER_IP, TOUCHDESIGNER_PORT)  # IP, 포트

# ─────────────────────────────────────────────
# 3. JSON 갱신 함수 (1시간 주기)
# ─────────────────────────────────────────────
def update_json() -> None:
    print("[osc.py] - 업데이트 시작 : news2emotion.py 실행 중...")
    result = subprocess.run(NEWS2EMOTION_CMD)
    if result.returncode == 0:
        print("[osc.py] - 업데이트 완료 : 뉴스 갱신 완료!")
    else:
        print(f"[osc.py] - 업데이트 오류 : news2emotion.py 실행 실패 (exit code = {result.returncode})")


# ─────────────────────────────────────────────
# 4. OSC 전송 함수 (10초 주기)
# ─────────────────────────────────────────────
def send_random_message() -> None:
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            print(f"[osc.py] - 경고 : JSON 데이터 없음 → {JSON_PATH}")
            return

        entry = random.choice(data)
        headline_for_td = insert_splits(entry["headline"])  # split
        payload = {**entry, "headline": headline_for_td}    #split headline 새 dict에 
        client.send_message("/msg", json.dumps(payload, ensure_ascii=False))
        print(f"[osc.py] - 전송 완료 → {headline_for_td}")

    except Exception as e:
        print(f"[osc.py] - 에러 : JSON 파싱 오류 → {e}")
        return

# ─────────────────────────────────────────────
# 5. 스케줄 등록 및 루프
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # update_json() # 첫 실행에서 JSON 갱신
    print("[osc.py] - 최초 실행 : JSON 갱신 시도")

    # 10초마다 OSC 전송
    schedule.every(10).seconds.do(send_random_message)
    # 1시간마다 JSON 갱신
    # schedule.every(1).hours.do(update_json)

    print("[osc.py] - 스크립트 실행 중 : 10초마다 OSC 전송, 1시간마다 JSON 갱신")
    while True:
        schedule.run_pending()
        time.sleep(1)