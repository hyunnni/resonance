import os
from datetime import datetime, timedelta, timezone
import pytz
import pycountry
from dotenv import load_dotenv; 
import worldnewsapi
from worldnewsapi.rest import ApiException

''' WORLD NEWS API
1 point per request / 0.01 point per returned result
https://worldnewsapi.com/docs/search-news/
https://worldnewsapi.com/console/#
https://github.com/ddsky/world-news-api-clients/blob/main/python/docs/NewsApi.md#search_news
'''

load_dotenv()
newsapi_key = os.getenv("WORLD_NEWS_API_KEY")

newsapi_configuration = worldnewsapi.Configuration(api_key={'apiKey': newsapi_key})
newsapi_instance = worldnewsapi.NewsApi(worldnewsapi.ApiClient(newsapi_configuration))

def convert_utc_to_kst(utc_dt) -> str:
    if isinstance(utc_dt, str):
        utc_dt = datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")
    
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
        
    kst = pytz.timezone('Asia/Seoul')
    kst_dt = utc_dt.astimezone(kst)
    return kst_dt.strftime('%Y-%m-%d %H:%M:%S')

def get_country_name(code: str) -> str:
    if not code:
        return "Unknown"
    try:
        country = pycountry.countries.get(alpha_2=code.upper())
        return country.name if country else code
    except:
        return code
    
NEWS_PER_REQUEST = 10

# now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
# one_hour_ago = now - timedelta(hours = 1)

# print(f"earliest_publish_date: {one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')}")
# print(f"latest_publish_date: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# try:
#     response = newsapi_instance.search_news(
#         language='en',
#         earliest_publish_date = one_hour_ago.strftime('%Y-%m-%d %H:%M:%S'),
#         latest_publish_date = now.strftime('%Y-%m-%d %H:%M:%S'),
#         categories= 'politics,sports,business,technology,entertainment,health,science,lifestyle,travel,culture,education,environment,other',
#         sort="publish-time",
#         sort_direction="desc",
#         offset=0,
#         number=NEWS_PER_REQUEST
#     )
    
#     print(f"Recieved {len(response.news)} articles. Total available: {response.available}.\n")
    
#     for article in response.news:
#         kst_date = convert_utc_to_kst(article.publish_date)
#         country_name = get_country_name(article.source_country)
#         print(f"{article.title}")
#         print(f"Country: {country_name}")
#         print(f"Time(KST): {kst_date}")
#         print(f"URL: {article.url}")
#         print("-" * 60)

# except ApiException as e:
#     print(f"Exception when calling NewsAPI -> search_news: {e}")

def fetch_worldnews(
    timespan: str = "1hours",
    number: int = 10,
    source_countries: list[str] = None,
    language: str = 'en',
    categories: str = 'politics,sports,business,technology,entertainment,health,science,lifestyle,travel,culture,education,environment,other',
    sort: str = 'publish-time',
    sort_direction: str = 'desc',
    offset: int = 0
) -> list[dict]:
    """
    Fetch news articles from WorldNews API and return a list of dicts with url, source_country (name), headline, date (KST).
    timespan: e.g. '1hours', '2days'
    """
    try:
        # Calculate time window
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        if timespan.endswith("hours"):
            hours = int(timespan[:-5])
        elif timespan.endswith("days"):
            hours = int(timespan[:-4]) * 24
        else:
            hours = 1
        earliest = now - timedelta(hours=hours)
        earliest_publish_date = earliest.strftime('%Y-%m-%d %H:%M:%S')
        latest_publish_date = now.strftime('%Y-%m-%d %H:%M:%S')

        params = {
            'language': language,
            'categories': categories,
            'sort': sort,
            'sort_direction': sort_direction,
            'offset': offset,
            'number': number,
            'earliest_publish_date': earliest_publish_date,
            'latest_publish_date': latest_publish_date
        }
        if source_countries:
            params['source_countries'] = ','.join(source_countries)
        response = newsapi_instance.search_news(**params)
        articles = []
        for article in response.news:
            kst_date = convert_utc_to_kst(article.publish_date)
            country_name = get_country_name(article.source_country)
            articles.append({
                'url': article.url,
                'source_country': country_name,
                'headline': article.title,
                'date': kst_date
            })
        return articles
    except ApiException as e:
        print(f"Exception when calling NewsAPI -> search_news: {e}")
        return []