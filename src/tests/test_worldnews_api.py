from src.api.worldnews_api import fetch_worldnews

def main():
    articles = fetch_worldnews(number=5)
    print(f"[test_worldnews_api] Returned {len(articles)} articles.")
    for i, article in enumerate(articles):
        print(f"\nArticle {i+1}:")
        for k, v in article.items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    main() 