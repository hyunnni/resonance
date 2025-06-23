import os
from google.cloud import translate_v2 as translate
from dotenv import load_dotenv; 

load_dotenv()

project_id = os.getenv("PROJECT_ID")
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

assert project_id, "PROJECT ID가 설정되지 않았습니다."

# v2 클라이언트 사용 
translate_client = translate.Client()


def translate_text(text, target_language="ko"):
    """
    Translate input text to the target language using Google Translation API.
    Args:
        text (str): The text to translate.
        target_language (str): The language code to translate to (default: 'ko' for Korean).
    Returns:
        str: Translated text.
    """
    if not text:
        return ""
    try:
        result = translate_client.translate(text, target_language=target_language)
        return result["translatedText"]
    except Exception as e:
        print(f"Translation error: {e}")
        return text 
    
# test 
# if __name__ == "__main__":
#     print(translate_text("Hello world!", "ko"))