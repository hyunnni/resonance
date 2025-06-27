import os
from datetime import datetime, timedelta, timezone
import pytz
import pycountry
from dotenv import load_dotenv; 
import worldnewsapi
from worldnewsapi.rest import ApiException
from typing import List, Dict
from pprint import pprint

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

from .config import TIMESPAN_HOURS, NUM_RECORDS

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

def fetch_worldnews(
    timespan: float = TIMESPAN_HOURS,
    number: int = NUM_RECORDS,
    language: str = 'en',
    categories: str = 'politics,sports,business,technology,entertainment,health,science,lifestyle,travel,culture,education,environment,other',
    sort: str = 'publish-time',
    sort_direction: str = 'DESC',
    offset: int = 0
) -> List[Dict]:
  
    try:

        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        earliest = now - timedelta(hours=timespan)

        print(f"[fetch_worldnews] earliest_publish_date: {earliest.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[fetch_worldnews] latest_publish_date: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        params = {
            'language':language,
            'categories':categories,
            'sort':sort,
            'sort_direction':sort_direction,
            'offset':offset,
            'number':number,
            'earliest_publish_date':earliest.strftime('%Y-%m-%d %H:%M:%S'),
            'latest_publish_date':now.strftime('%Y-%m-%d %H:%M:%S')
        }

        response = newsapi_instance.search_news(**params)
        print(f"[fetch_worldnews_Response] Recieved {len(response.news)} articles. Total available: {response.available}.")
        
        articles = []
        min_headline_length = 20  # 최소 헤드라인 길이
        for article in response.news:
            if len(article.title) >= min_headline_length:
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

# now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
# one_hour_ago = now - timedelta(hours = 1)

# print(f"earliest_publish_date: {one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')}")
# print(f"latest_publish_date: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# NEWS_PER_REQUEST = 10

# # 2025-06-23 18:00:00
# # latest_publish_date: 2025-06-23 19:00:00

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