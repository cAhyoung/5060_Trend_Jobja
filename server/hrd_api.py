from datetime import datetime, timedelta
import requests
import json

def load_hrd():
    try:
        # 현재 날짜 구하기
        current_date = datetime.now()

        # 한 달 전 날짜 계산
        one_month_ago = current_date - timedelta(days=30)

        # 날짜를 문자열로 변환 (YYYYMMDD 형식)
        srchTraStDt = one_month_ago.strftime('%Y%m%d')
        srchTraEndDt = current_date.strftime('%Y%m%d')

        # 내일배움카드 데이터 저장하기
        tot_data = []


        # URL 및 파라미터 설정 - 목록
        key = 'hrd-api-key'
        url = 'https://www.hrd.go.kr/jsp/HRDP/HRDPO00/HRDPOA60/HRDPOA60_1.jsp?'

        for num in range(1, 500):
            params = {
                'authKey': key,
                'returnType': 'JSON',
                'pageNum': num,
                'pageSize': '10',
                'srchTraStDt': srchTraStDt,
                'srchTraEndDt': srchTraEndDt,
                'outType': '1',
                'sort': 'ASC',
                'sortCol': 'TOT_FXNUM',
            }

            # URL - 상세
            url_detail = "https://www.hrd.go.kr/jsp/HRDP/HRDPO00/HRDPOA60/HRDPOA60_2.jsp"

            # API 호출
            response = requests.get(url, params=params)

            # JSON 데이터 파싱
            data = json.loads(response.text)

            # "returnJSON" 문자열을 파싱
            return_json = json.loads(data.get('returnJSON', '{}'))

            # "srchList" 키에 해당하는 값에서 필요한 데이터 추출
            search_list = return_json.get('srchList', [])

            for search in search_list:
                ## 저장할 데이터들 미리 준비
                title = search["title"]  # 강좌 타이틀
                tel_num = search["telNo"]  # 전화번호
                start_date = search["traStartDate"]  # 시작날짜
                end_date = search["traEndDate"]  # 마지막 날짜
                address = search["address"]  # 주소
                user_grade = search["grade"]  # 사용자 평가 등급: 아마도..?
                category = search["trainTarget"]  # 훈련 유형

                # 상세페이지 서치를 위해서 데이터 추출
                train_id = search["trprId"]  # 훈련과정 ID
                train_how_many = search["trprDegr"]  # 훈련 과정 회차
                train_org_id = search["trainstCstId"]  # 훈련기관 ID

                # 파라미터 설정 - 상세
                detail_params = {
                    'authKey': key,
                    'returnType': 'JSON',
                    'outType': 2,
                    'srchTrprId': train_id,
                    'srchTrprDegr': train_how_many,
                    'srchTorgId': train_org_id

                }

                response_detail = requests.get(url_detail, params=detail_params)
                detail = json.loads(response_detail.text)

                # "returnJSON" 문자열을 파싱
                return_json_detail = json.loads(detail.get('returnJSON', '{}'))

                # "srchList" 키에 해당하는 값에서 필요한 데이터 추출
                detail_list = return_json_detail.get('inst_base_info', [])

                # 상세페이지에서 가져올 데이터들 정리
                org_name = detail_list["inoNm"]  # 훈련기관명
                gov_pay = detail_list["perTrco"]  # 정부 지원금
                tot_day = detail_list["trDcnt"]  # 총 훈련일수
                tot_hour = detail_list["trtm"]  # 총 훈련시간
                ncs_name = detail_list["ncsNm"]  # ncs명

                input_data = {
                    "title": title,
                    "tel_num": tel_num,
                    "address": address,
                    "start_date": start_date,
                    "end_date": end_date,
                    "tot_day": tot_day,
                    "tot_hour": tot_hour,
                    "user_grade": user_grade,
                    "org_name": org_name,
                    "category" : category,
                    "gov_pay": gov_pay,
                    "ncs_name" : ncs_name
                }

                tot_data.append(input_data)

    except Exception as e:
        error_message = str(e)
        print(error_message)

    finally: return tot_data
