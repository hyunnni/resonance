# 🛰️ TouchDesigner OSC 연동 (osc.py 사용법)

## 🔧 실행 방법
### 1. 가상환경 실행

**🪟 Windows (CMD)**
```bash
cd documents\resonance
venv\Scripts\activate
```
**🍎 macOS / 🐧 Linux**
```bash
cd documents/resonance
source venv/bin/activate
```

### 2. 스크립트 실행
```bash
python -m src.api.osc
#또는 모듈 실행 대신 직접 실행
python src/api/osc.py   
```

## ⚙️ 주요 변수 설명 (src/api/osc.py 내부)
```python
# TouchDesigner 수신 설정
TOUCHDESIGNER_IP = "10.210.68.14"   # TouchDesigner가 실행 중인 컴퓨터의 IP 주소
TOUCHDESIGNER_PORT = 8000           # OSC를 수신할 포트 번호

# 감정 분석 JSON 경로
JSON_PATH = "latest_articles_with_sentiment.json"  # 최신 뉴스 감정 분석 결과가 저장된 파일

# news2emotion.py 실행 명령어
NEWS2EMOTION_CMD = [
    sys.executable,                # 현재 파이썬 실행 경로 (예: venv 내 Python)
    "src/api/news2emotion.py",    # 뉴스 분석 스크립트 경로
    "--timespan", "3.0",          # 분석할 뉴스의 시간 범위 (최근 3시간)
    "--num-records", "10",        # 최대 뉴스 수집 개수
    "--export-count", "10",       # 출력 JSON에 포함할 기사 개수
]

```

## 🧾 news2emotion 실행 옵션 (수정가능)
| 옵션               | 설명                                  |
| ---------------- | ----------------------------------- |
| `--timespan`     | 최근 몇 시간 동안의 뉴스 가져올지 (예: 3.0 → 3시간) |
| `--num-records`  | 최대 몇 개의 뉴스 기사를 가져올지 (예: 10개/최대 100개)        |
| `--export-count` | JSON으로 저장할 뉴스 기사 수 (최신 순 기준)        |

## ⏱️ 동작 스케줄 요약 (수정가능)
| 기능        | 주기         | 설명                                            |
| --------- | ---------- | --------------------------------------------- |
| OSC 전송    | 10초마다      | 감정 분석된 뉴스 중 무작위로 하나를 OSC 메시지로 전송 (`/msg` 주소)  |
| JSON 업데이트 | (옵션) 1시간마다 | `news2emotion.py`를 실행해 최신 뉴스로 갱신 (주석 처리되어 있음) |
