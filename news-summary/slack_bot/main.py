from library import slack
from library.es_query import *
from collections import defaultdict
from datetime import datetime
import json


def post():
    slack.post_message("# chatbot-분석", "\n---{} 뉴스 챗봇 로그 분석 ---".format(datetime.now().strftime("%Y년 %m월 %d일")))

    index = 'elk-logger-' + datetime.now().strftime("%Y.%m.%d")
    records = request_data(index)
    news_type = defaultdict(int)
    
    for record in records["hits"]["hits"]:
        if "log_info" in record["_source"]:
            news =  record["_source"]["log_info"]
            if news != 'update news':
                news_type[news] += 1

    rank_list = []
    for news, cnt in news_type.items():
        rank_list.append([news, cnt])

    # Sort
    rank_list.sort(key=lambda x: x[1], reverse=True)
    
    # Result
    msg = "분야별 기사 순위\n"
    for idx, (keyword, cnt) in enumerate(rank_list):
        msg += "{}위 -> {} : {}회 호출\n".format(idx+1, keyword, cnt)

    # Send Message
    slack.post_message("# chatbot-분석", msg+"---------------------------------------------------\n")
            
if __name__ == "__main__":
    post()