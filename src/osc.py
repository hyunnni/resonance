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

# ─────────────────────────────────────────────
# 2. TouchDesigner OSC 클라이언트
# ─────────────────────────────────────────────
client = udp_client.SimpleUDPClient(TOUCHDESIGNER_IP, TOUCHDESIGNER_PORT)  # IP, 포트

# ─────────────────────────────────────────────
# 3. JSON 갱신 함수 (1시간 주기)
# ─────────────────────────────────────────────
def update_json():
    print("[osc.py] - 업데이트 시작 : news2emotion.py 실행 중...")
    result = subprocess.run(NEWS2EMOTION_CMD)
    if result.returncode == 0:
        print("[osc.py] - 업데이트 완료 : 뉴스 갱신 완료!")
    else:
        print("[osc.py] - 업데이트 에러 : news2emotion.py 실행 실패 (exit code = %s)", result.returncode)

# ─────────────────────────────────────────────
# 4. OSC 전송 함수 (10초 주기)
# ─────────────────────────────────────────────
def send_random_message():
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            print("[osc.py] - 경고 : json에 데이터가 없습니다 : %s" , JSON_PATH)
            return

        entry = random.choice(data)
        client.send_message("/msg", json.dumps(entry, ensure_ascii=False))
        print("[osc.py] - 전송 완료 -> %s", entry['headline'])

    except Exception as e:
        print("[osc.py] - 에러 : JSON 파싱 오류: %s", e)
        return

# ─────────────────────────────────────────────
# 6. 스케줄 등록 및 루프
# ─────────────────────────────────────────────
if __name__ == "__main__":
    update_json() # 첫 실행에서 JSON 갱신
    print("[osc.py] - 최초 실행 : JSON 갱신 시도")

    # 10초마다 OSC 전송
    schedule.every(10).seconds.do(send_random_message)
    # 1시간마다 JSON 갱신
    schedule.every(1).hours.do(update_json)

    print("[osc.py] - 스크립트 실행 중 : 10초마다 OSC 전송, 1시간마다 JSON 갱신")
    while True:
        schedule.run_pending()
        time.sleep(1)

# update_json()
print("[최초 실행] sample.json 갱신 시도")
schedule.every(10).seconds.do(send_random_message)  # 10초마다 OSC 전송
schedule.every(1).hours.do(update_json)             # 1시간마다 JSON 업데이트

# 6. 루프
print("[실행 중] 뉴스 감정 데이터 전송 + 1시간마다 업데이트")
while True:
    schedule.run_pending()
    time.sleep(1)
