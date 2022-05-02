from library import slack
from library.es_query import *
from collections import defaultdict
from datetime import datetime
import json
import os
import sys
sys.path.append('/workspace/News-Summarization-chatbot/news-summary/flask/database')
from postgreslq import CRUD

def post():
    slack.post_message("# chatbot-분석", """---* 뉴스 챗봇 로그 분석* ---""".format(datetime.now().strftime("%Y년 %m월 %d일")))
    now = datetime.now().strftime('%Y%m%d')
    index = 'elk-logger-' + datetime.now().strftime("%Y.%m.%d")
    records = request_data(index)
    news_type = defaultdict(int)
    most_view = defaultdict(list)
    
    for record in records["hits"]["hits"]:
        if "log_info" in record["_source"]:
            news =  record["_source"]["log_info"]
            if  news[0]=='2':
                try:
                    news_id, web_link, title = news.split('|| ')
                    if news_id not in most_view:
                        most_view[news_id] = [1, web_link, title]
                    else:
                        most_view[news_id][0] += 1
                except:
                    pass
                    
            elif news != 'update news':
                news_type[news] += 1 

    rank_list = []
    most_view_rank = []
    for news, cnt in news_type.items():
        rank_list.append([news, cnt])
    
    for news_id, (cnt, link, title) in most_view.items():
        most_view_rank.append([cnt, link, title, news_id])
    # Sort
    rank_list.sort(key=lambda x: x[1], reverse=True)
    most_view_rank.sort(reverse=True)
    # Result
    msg = """*분야별 기사 순위*\n"""
    for idx, (keyword, cnt) in enumerate(rank_list):
        msg += """*{}위* -> {} : {}회 호출\n""".format(idx+1, keyword, cnt)
        
    msg+="""\n*오늘 가장 많이 본 뉴스*\n"""
    for idx, (cnt, link, title, news_id) in enumerate(most_view_rank):
        if idx > 5: break
        msg += """*{}위* \n \t 제목 : {} \n \t {}회 호출 \n \t Link : {}\n""".format(idx+1, title, cnt, link)
        db.insertDB(schema='public',table='past_news', data=(news_id ,cnt, now))
        
    

    
    # Send Message
    slack.post_message("# chatbot-분석", msg+"""---------------------------------------------------\n""")
            
if __name__ == "__main__":
    db = CRUD()
    post()