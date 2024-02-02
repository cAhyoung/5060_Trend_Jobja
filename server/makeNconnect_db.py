from flask import Flask, jsonify, request
from flask_cors import CORS
import openai
import pymongo
from hrd_api import load_hrd

# ### 몽고디비 연결하기
connect = pymongo.MongoClient()
# print(connect)
#
# ### 몽고디비에 있는 DB 목록 가져오기
# for item in connect.list_databases():
#     print(item)
#
# ### DB 명 저장해서 DB 연결하기
db_name = "chat"
#
db = connect.get_database(db_name)
# print(db)
#
# ### DB 연결해서 collection 무엇이 있는지 확인
# for item in db.list_collection_names():
#     print(item)
#
# ### collection 연결하기
# coll = db.get_collection("chat")
# print(coll)
#
# user_message = ""
#
# ### 여러개 넣는 경우 insert_many, 한개만 넣는 경우 insert_one
# coll.insert_many([{
#             "role": "assistant",
#             "content": "안녕하세요. 당신의 재취업을 도울 챗봇 뉴잡스입니다. 어떤 이유로 절 찾으셨나요?"
#         }, {
#             "role": "system",
#             "content": f"""당신은 중장년층의 재취업을 도울 챗봇인 뉴잡스입니다. \ 당신의 업무는 다음과 같습니다.
#                         - 사용자에게 관심있는 직군이나 분야 혹은 일했던 분야에 대해 입력받습니다.
#                         - 이 과정에서 사용자가 관심있는 직군이나 분야 혹은 일했던 분야를
#                         - 사용자의 입력값을 바탕으로 다음 세가지를 파악해야 합니다.
#                             1. 뉴스 기반 트렌드를 원하는지
#                             2. 직업 교육 강좌 추천을 원하는지
#                             3. 본인의 능력을 활용할 수 있는 다른 직업을 추천받기를 원하는지
#                         - 이를 파악했다면 예의바르게 답변합니다.
#
#                         user input = {user_message}"""
#         }])
#
# ### collection에 잘 들어갔는지 확인
# for item in coll.find():
#     print(item)
#
#
# ### collection에서 _id 빼고 가져오기
# for data in coll.find({}, {'_id' : False}):
#     print(data)

hrd_coll = db.get_collection("hrd")
# hrd_coll.delete_many({})
# data = load_hrd()
# hrd_coll.insert_many(data, ordered=False)
# print("end")

for i in hrd_coll.find({}, {'_id' : False}):
    print(i)
