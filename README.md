# MoonJar – Resonance

<br>

## 폴더 구조
```
resonance/
├─ src/
│ └─ api/ # 파이썬 데이터 파이프라인
├─ .env.example # API 키 템플릿
└─ requirements.txt
```

<br>

## 실행
```bash
# 1. 소스 받기
git clone https://github.com/hyunnni/moonjar-resonance.git  
cd moonjar-resonance

# 2. 가상환경 생성 & 활성화
python -m venv .venv
source .venv/bin/activate

# 3. 패키지 설치
pip install -r requirements.txt 

# 4. 환경변수 파일(.env) 작성
cp .env.example .env   # NEWS_API_KEY 입력 (NewsAPI 가입 후 발급)
nano .env
# NEWS_API_KEY= 실제 키값 붙여넣기

# 5. 실행
python src/api/news2emotion.py
# 콘솔에 JSON 출력

# 6. 종료 (가상환경 비활성화)
deactivate
```