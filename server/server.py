from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_apscheduler import APScheduler
import openai
import pymongo
from hrd_api import load_hrd
from news_api import load_news

### 서버 설정
application = Flask(__name__)
CORS(application)

### 데이터 주기적으로 업데이트 하기 위한 함수
scheduler = APScheduler()

### DB에서 collection 불러오기
con = pymongo.MongoClient()
db = con.get_database("chat")
coll_chat = db.get_collection("chat")
coll_hrd = db.get_collection("hrd")

### DB에 데이터 주기적으로 저장하기 위한 함수 -> scheduler 이용해서 24시간에 한번씩 중복 제외 업로드
def update_hrd():
    global coll_hrd
    data = load_hrd()
    coll_hrd.insert_many(data, ordered=False)
    print("end")


### Free tier -> 분당 3번 호출이 최대임 그 이상으로 호출하면 에러 떠서 함수 3개 만들어서 돌려 쓰기
def gpt1(prompt):
    ## key1
    openai.api_key = "chat-gpt-api-key"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=prompt,
        temperature=0)

    return response.choices[0].message["content"]

def gpt2(prompt):
    ## key2
    openai.api_key = "chat-gpt-api-key"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=prompt,
        temperature=0)

    return response.choices[0].message["content"]

def gpt3(prompt):
    ## key3
    openai.api_key = "chat-gpt-api-key"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=prompt,
        temperature=0)

    return response.choices[0].message["content"]


### 서버 코드
@application.route('/chat', methods=["POST", "GET"])
def using_userinput():
    try:
        global coll_chat
        global coll_hrd

        ### 사용자 데이터 불러오기
        data = request.json
        user_message = data.get("value")

        ### 서버 연결이 잘 되었는지 확인
        print("user message : ", user_message)

        ### 유저 메세지 DB에 저장
        coll_chat.insert_one({"role": "user",
                         "content": user_message})

        ### 챗봇 구동을 위한 기본적인 프롬프트
        prompt_message = [{
            "role": "assistant",
            "content": "안녕하세요. 당신의 재취업을 도울 챗봇 뉴잡스입니다. 어떤 이유로 절 찾으셨나요?"
        }, {
            "role": "system",
            "content": f"""당신은 중장년층의 재취업을 도울 챗봇인 뉴잡스입니다. \ 당신의 업무는 다음과 같습니다. 
                                - 사용자에게 관심있는 직군이나 분야 혹은 일했던 분야에 대해 입력받습니다. 
                                - 이 과정에서 사용자가 관심있는 직군이나 분야 혹은 일했던 분야를 
                                - 사용자의 입력값을 바탕으로 다음 세가지를 파악해야 합니다. 
                                    1. 뉴스 기반 트렌드를 원하는지
                                    2. 직업 교육 강좌 추천을 원하는지
                                    3. 본인의 능력을 활용할 수 있는 다른 직업을 추천받기를 원하는지 
                                - 이를 파악했다면 예의바르게 답변합니다.   
                                - 사용자와의 대화를 꼭 기억해야 하며, 사용자가 대화를 종료하겠다는 메세지를 줄 때 대화 내용을 모두 삭제합니다. 
                                - 이때 똑같은 말을 여러번 하지 말아야 합니다. 

                                user input = {user_message}"""
        }]

        ### 사용자 입력값에서 키워드 뽑아내기 위한 프롬프트
        prompt_message_keyword = [{
            "role" : "system",
            "content" : f"""당신은 사용자가 입력한 내용에서 사용자가 관심을 가진 직군명이나 직업명, 분야명, 혹은 일했던 직군명이나 직업명, 분야명에 대한 키워드를 뽑아내야 합니다. 아래의 예시를 참고하세요. \ 
                            output을 보여줄 때는 다른 부연설명, 수식어구 필요 없이 키워드만 출력하면 됩니다. 만약 그런 키워드가 없다면 아무것도 출력하지 마세요. \ 
                            꼭 직군명, 직업명, 분야명과 관련된 키워드만 출력하며 이 외의 키워드는 절대 출력하지 마세요. 
                            
                        example :
                            user input = 나는 요새 플로리스트를 해보고 싶어
                            output : 플로리스트
                            user input = 이직 준비를 하고싶어
                            output : ''
                        
                        user input = {user_message}
                        output : """
        }]

        ### 사용자 입력값에서 트렌드를 보고 싶은지 강좌를 보고 싶은지 뽑아내는 프롬프트
        prompt_message_needs = [{
            "role" : "system",
            "content" : f"""당신은 사용자가 입력한 내용에서 사용자가 강좌 추천을 원하는지, 뉴스기사 기반의 트렌드를 알고싶어하는지 파악해 키워드를 추출해야 합니다. 아래의 예시를 참고하세요. \ 
                            output을 보여줄 때는 다른 부연설명, 수식어구 필요 없이 키워드만 출력하면 됩니다. 만약 그런 키워드가 없다면 아무것도 출력하지 마세요. \ 
                            강좌와 관련된 내용이라면 '강좌'라는 키워드만 출력하며, 뉴스기사 기반의 트렌드를 알고싶어 한다면 '트렌드'라는 키워드만 출력합니다. \
                            절대 관련되지 않은 다른 키워드는 출력하지 않습니다. 
                            
                        example :
                            user input = 뭔가 수업을 들어볼만한 것이 있나
                            output : 강좌
                            user input = 트렌드를 좀 알고싶은데
                            output : 트렌드
                            user input = 아 잘 모르겠어
                            output : ''
                            user input = 요새 동향이 어떤지 궁금해
                            output : 트렌드
                            user input = 안녕
                            output : ''
                            user input = 난 개발자가 되고 싶어
                            output : ''
                            user input = 요새 ~~한게 배워보고 싶은데
                            output : 강좌
                        
                        user input = {user_message}
                        output : """
        }]


        ### 챗봇 구동을 위한 메인 프롬프트에 사용자와의 대화 데이터를 계속 추가해서 gpt에게 넣어줌
        for i in coll_chat.find({}, {'_id' : False}):  # -> _id 제거 안해주면 gpt 에러나서 return값 반환 안함
            prompt_message.append(i)

        ### GPT 설정
        global answer
        answer = gpt1(prompt_message)

        ### 키워드 뽑아내기 위한
        keyword = gpt2(prompt_message_keyword)
        print(keyword)
        ### 강좌 vs 트렌드
        needs = gpt3(prompt_message_needs)
        print(needs)

        ### 니즈를 기반으로 어떤 데이터를 불러와야 하는지 확인
        if needs == "트렌드":
            news_data = load_news(keyword)
            news_prompt = [{
                "role" : "system",
                "content" : f"""당신은 내일배움카드 데이터의 사실만을 바탕으로 객관적인 진실만을 전달하는 챗봇입니다. \
                                당신은 데이터를 함부로 만들어서는 안되며, 주어진 내일배움카드 데이터에서 사용자의 관심사와 가장 밀접하고 관련있는 강좌를 골라내 추천합니다. \
                                당신은 서로 다른 데이터끼리 함부로 조합해서는 안되며, 주어진 내일배움카드 데이터만을 이용해 사용자의 관심사와 가장 밀접하고 관련있는 강좌를 추천해야 합니다.\
                                사용자의 관심사({keyword})참고하여 내일배움카드 강좌를 추천합니다.\
                                이때 course data의 데이터의 'title'과 'ncs_name'을 참고하여, 사용자의 키워드와 가장 밀접한 관련이 있는 3개의 강좌를 추천합니다. \
                                이때 출력값에는 "title", "address", "tel_num", "org_name"의 정보가 필수로 포함됩니다. \
                                사용자의 키워드({keyword})와 가장 관련이 깊은 3개의 추천 강좌를 선택하는 명확한 이유가 있어야 합니다. \
                                또한 이러한 교육 강좌를 추천하는 이유에 대해 간단하게 설명하고 응답할 때 주어진 출력에 따라 답변합니다.\
                                사용자에게 정보 제공 시 아래 output과 유사하게 깔끔하게 텍스트로 보여주세요
                                
                            news data : {news_data}
                            output :
                                <원하는 멘트>
                                1. <기사제목> 
                                요약 : 
                                링크 : 
                                    
                                2. <기사제목>
                                요약 : 
                                링크 :
                                    
                                3. <기사제목>
                                요약 : 
                                링크 : """
            }]
            answer = gpt1(news_prompt)

        elif needs == "강좌":
            hrd_data = []
            for i in coll_hrd.find({}, {'_id' : False}):
                hrd_data.append(i)

            # user_chat = []
            # for j in coll_chat.find({"role" : "user"}, {"_id" : False}):
            #     user_chat.append(j)

            hrd_prompt = [{
                "role": "system",
                "content": f"""당신의 업무는 아래의 내일배움카드 데이터를 활용해 user input과 가장 밀접한 데이터를 3개 추출하는 것입니다. \
            사용자의 관심사와 가장 밀접한 강좌를 추천할 때 'title'과 'ncs_name'을 활용합니다. \
            출력값에는 'title', 'tel_num', 'address', 'org_name'은 필수적으로 포함해야 하며, 사용자의 관심사는 user input에 포함되어 있습니다. \
            사용자에게 정보 제공 시 아래 output과 유사하게 깔끔하게 텍스트로 보여주세요. 

            내일배움카드 데이터 : {hrd_data[20:110]}
            user input : {keyword}
            output:
                세가지 강좌를 추천할게요. 
                1. <강좌 제목>
                    - <주소지>
                    - <전화번호>
                    - <회사명>
                2. <강좌 제목>
                    - <주소지>
                    - <전화번호>
                    - <회사명>
                3. <강좌 제목>
                    - <주소지>
                    - <전화번호>
                    - <회사명>
                """
            }]
            answer = gpt2(hrd_prompt)

        else :
            print("해당 사항이 없습니다.")

        coll_chat.insert_one({"role": "assistant",
                              "content": answer})

    except Exception as e:
        print(f"error message : {e}")


    return jsonify({"gpt": answer})


if __name__ == "__main__":
    ### 스케줄러 설정으로 주기적으로 데이터 추가할 수 있도록 함
    scheduler.add_job(id="load_hrd", func=update_hrd, trigger="interval", minutes=1440)
    scheduler.start()
    application.run(host='0.0.0.0', port=5000, debug=True)
