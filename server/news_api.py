import openai
import pprint
from openai import InvalidRequestError
import time
import re
import urllib.request
from newspaper import Article, ArticleException
import tiktoken

def load_news(keyword):
    ### 네이버 뉴스 불러오기 위한 호출 과정
    ### 하루 호출 건수 25,000건이 최대
    client_id = "naver-news-api-key"
    client_secret = "LLDNojEcll"

    ### 검색 키워드는 여기서 설정
    encText = urllib.parse.quote(keyword)

    url = "https://openapi.naver.com/v1/search/news.json?query=" + encText + "&display=5&sort=sim"  # JSON 결과

    request = urllib.request.Request(url)

    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    response = urllib.request.urlopen(request)

    rescode = response.getcode()

    ### 실제로 데이터를 저장할 변수
    news_data = {"news_data": []}

    if (rescode == 200):
        response_body = response.read()
        data = eval(response_body.decode('utf-8'))
        # pprint.pprint(data["items"])

        ### 데이터는 타이틀과 오리지널 링크만 가져오기
        for news in data["items"]:
            try:
                ### 저장 전 데이터 전처리 해주는 부분 -> 특수문자 제거
                news["originallink"] = re.sub(r"\\", "", news["originallink"])
                article = Article(news["originallink"], language='ko')
                article.download()
                article.parse()
                article.text = re.sub(r"\n", "", article.text)
                article.text = re.sub(r"/", "", article.text)
                article.text = re.sub(r"\u200b", "", article.text)

                ### 전처리 후 데이터 변수에 저장
                news_data["news_data"].append({
                    "url": news["originallink"],
                    "title": article.title,
                    "content": article.text
                })
            except ArticleException:
                pass

        return summary_news(news_data["news_data"], keyword)


    else:
        print("Error Code:" + rescode)

def summary_news(data, keyword):
    ### return 할 데이터
    show_news = []

    ### GPT key 설정
    ## key4
    openai.api_key = "gpt-api-key"

    ### 토크나이저 이용해 토큰 수 계산
    tokenizer = tiktoken.get_encoding("cl100k_base")  ### ChatGPT 모델에 대한 토크나이저를 가져오려는 경우 인코딩 방법
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo-1106")

    for i, news in enumerate(data):
        if len(tokenizer.encode(news["content"])) > 16385:
            pass
        else:
            message = [{"role": "system", "content": f"""아래의 content는 당신이 요약해야 할 뉴스기사입니다. \
            뉴스기사의 주요 내용 중 사용자가 입력한 키워드인 {keyword}와 관련한 동향이나 흐름을 알 수 있도록 세줄로 요약해주세요. \
            요약 시 한줄 당 50자 내로 핵심만 뽑아 요약해주세요. 
            세줄로 요약할 때는 output의 형식에 맞춰서 결과를 보여주세요. 

            content: {news["content"]}

            output 
            : 해당 뉴스의 요약입니다. 
            1. 요약내용1
            2. 요약내용2
            3. 요약내용3
            """}]

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-1106",
                messages=message,
                temperature=0,
            )

            append_news = {
                "title": news["title"],
                "summary": response.choices[0].message["content"],
                "url": news["url"]
            }

            show_news.append(append_news)

        if i % 3 == 0:
            time.sleep(60)

    return show_news
