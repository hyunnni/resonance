# MoonJar – Resonance

<br>

## 폴더 구조
```
moonjar-resonance/
├── README.md
├── requirements.txt
└── src/
    ├──api/ # 데이터 수집 및 감정 분석
    │   ├── fetch_gdelt.py
    │   ├──news2emotion.py
    └── └──sentiment_nli.py
    └──tests/ # 테스트 코드
.env.example # 환경변수 템플릿
```

<br>

## 실행 방법
```bash
# 1. 소스 받기
git clone https://github.com/hyunnni/moonjar-resonance.git  
cd moonjar-resonance

# 2. 가상환경 생성 & 활성화
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt 

# # 4. 환경변수 파일(.env) 작성
# cp .env.example .env   # NEWS_API_KEY 입력 (NewsAPI 가입 후 발급)
# nano .env
# # NEWS_API_KEY = 실제 키값 붙여넣기

# 5. 실행
python src/api/news2emotion.py
# 콘솔에 JSON 형태로 출력

# 6. 종료 (가상환경 비활성화)
deactivate
```
<br>

## 주요 기능
- fetch_gdelt.py: GDELT API 통해 뉴스 헤드라인 수집
- news2emotion.py: 뉴스 헤드라인 감정 분석 전체 파이프라인
- sentiment_nli.py: 감정 분류 

<br>