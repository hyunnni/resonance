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

from config import TIMESPAN_HOURS, NUM_RECORDS

MIN_HEADLINE_LENGTH = 25  # 최소 헤드라인 길이 

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

        # now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        earliest = (now - timedelta(hours=timespan)).replace(minute=0, second=0, microsecond=0)

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
        for article in response.news:
            if len(article.title) >= MIN_HEADLINE_LENGTH:
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