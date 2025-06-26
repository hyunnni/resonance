import json

# headline 줄바꿈 삽입 함수
def insert_splits(text: str, chunk: int = 40) -> str:
    if len(text) <= chunk:
        return text

    chars = list(text)
    idx = chunk
    while idx < len(chars):
        window = range(max(idx - 10, 0), min(idx + 10, len(chars)))
        split_pos = next((i for i in window if chars[i] == " "), None)
        if split_pos:
            chars[split_pos] = "<split>"
            idx = split_pos + chunk
        else:
            idx += chunk
    return "".join(chars)

# JSON 파일 경로
JSON_PATH = "latest_articles_with_sentiment.json"

# 테스트 실행
def test_split_insertion():
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            articles = json.load(f)
    except Exception as e:
        print(f"[에러] JSON 파일 읽기 실패: {e}")
        return

    print("\n📄 헤드라인 줄바꿈 테스트 결과:\n" + "-"*50)
    for i, article in enumerate(articles, 1):
        original = article["headline"]
        modified = insert_splits(original)
        print(f"[{i}] 원본:   {original}")
        print(f"    변환:   {modified}\n")

if __name__ == "__main__":
    test_split_insertion()
