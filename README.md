# Resonance: 뉴스 감정 분석

<br>

## 구조

```
  src/
  ├── api/
  │   ├── worldnews_api.py       # 뉴스 수집 모듈
  │   ├── news2emotion.py        # 메인 파이프라인 실행
  │   ├── emotion_utils.py       # 감정 분석 핵심 로직
  │   ├── sentiment_nli.py       # MNLI 기반 감정 분석
  │   ├── translation_api.py     # 번역 API 연동
  │   ├── db.py                  # SQLite DB 관련 함수
  │   ├── config.py              # 설정값 모음
  │
  └── tests/                     # 테스트 코드
```

<br>

## ⚙️ 설치 및 실행

### 1. 설치

```bash
git clone https://github.com/hyunnni/resonance.git
cd resonance
pip install -r requirements.txt
```

### 2. 환경 변수 설정 
`.env.example`을 침고하여 API 키 및 ID를 입력해주세요.
```ini
GOOGLE_APPLICATION_CREDENTIALS=PASTE_YOUR_GOOGLE_APPLICATION_CREDENTIALS(.JSON)
PROJECT_ID=PASTE_YOUR_PROJECT_ID
WORLD_NEWS_API_KEY=PASTE_YOUR_API_KEY
```

### 3. 실행 예
```bash
python src/api/news2emotion.py --timespan 1.0 --num-records 20
```
출력 파일 :
- `latest_articles_with_sentiment.json` : 최근 기사 N개 반환

<br>

## 🧪 실행 옵션
| 옵션 이름            | 설명                | 기본값 |
| ---------------- | ----------------- | --- |
| `--timespan`     | 최근 몇 시간 이내 뉴스 수집(hour)  | 1.0 |
| `--num-records`  | 수집할 뉴스 개수         | 100 |
| `--export-count` | 최근 저장할 JSON 기사 개수 | 100 |

예:`python src/api/news2emotion.py --timespan 3.0 --num-records 50`

<br>

## ⏰ 자동 실행 예

예를 들어, 메인 파이썬 코드 내에서 1시간마다 실행:
```python
import subprocess

subprocess.run([
    "python", "src/api/news2emotion.py",
    "--timespan", "1.0",
    "--num-records", "5"
])
```
또는 schedule 라이브러리를 사용해 정기 실행 설정
<br>

## 📄 출력 예 (JSON)
```json
{
  "url": "https://example.com/news/123",
  "headline": "국제 정상 회담에서 협정 체결",
  "source_country": "South Korea",
  "timestamp": "2025-06-25 08:30:00",
  "sentiment": {
    "label": "positive",
    "confidence": 0.782
  }
}
```
<br>
