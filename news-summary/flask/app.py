from flask import Flask, request, jsonify
import sys, os, re
import datetime
import pandas as pd
from database.postgreslq import CRUD, Databases
from elk_lib.my_log import back_logger_info

os.system("fuser -k 6006/tcp")

app = Flask(__name__)


news_type_list = ['today_main_news', 'section_politics', 'section_economy', 'section_society', 'section_life',
                  'section_world', 'section_it','last_most_view']
all_data_dict = {}
quick_replies = [
    {
        "messageText": "헤드라인 기사",
        "action": "message",
        "label": "헤드라인 기사"
    },
    {
        "messageText": "정치 뉴스",
        "action": "message",
        "label": "정치 뉴스"
    },
    {
        "messageText": "경제 뉴스",
        "action": "message",
        "label": "경제 뉴스"
    },
    {
        "messageText": "사회 뉴스",
        "action": "message",
        "label": "사회 뉴스"
    },
    {
        "messageText": "생활/문화 뉴스",
        "action": "message",
        "label": "생활/문화 뉴스"
    },
    {
        "messageText": "세계 뉴스",
        "action": "message",
        "label": "세계 뉴스"
    },
    {
        "messageText": "IT/과학 뉴스",
        "action": "message",
        "label": "IT/과학 뉴스"
    },
    {
        "messageText": "어제 가장 많이 본 뉴스",
        "action": "message",
        "label": "어제 가장 많이 본 뉴스"
    }
    
]

@app.route('/test')
def test():
    back_logger_info('hello world api!')
    return 'hello'

@app.route('/keyboard')
def Keyboard():
    dataSend = {
    }
    return jsonify(dataSend)

@app.route('/update')
def update():
    back_logger_info('update news')
    db = CRUD()
    FILE_TIME = datetime.datetime.now().strftime('%Y%m%d-%H')
    last_day =  (datetime.datetime.now() + datetime.timedelta(hours=9)- datetime.timedelta(days=1)).strftime('%Y%m%d')
    query = """
        select nd.* from public.news_data as nd
        join public.past_news as pn on nd.id  = pn.id
        where pn.timekey = '{last_day}';
        """.format(last_day= last_day)
    
    data = pd.DataFrame(db.readDB(schema='public',table='news_data',colum='*',condition=FILE_TIME), columns=["news_type", "title", "date", "all_contents","contents","image_url","news_url","summary","qa_span","timekey","id"])
    last_data = pd.DataFrame(db.joinDB(query), columns=["news_type", "title", "date", "all_contents","contents","image_url","news_url","summary","qa_span","timekey","id"])
    last_data["news_type"] = 'last_most_view'
    data = pd.concat([data,last_data], ignore_index=True)
    
    for news_type in news_type_list:
        data_list = []
        for i in range(len(data[data['news_type'] == news_type])):
            if i > 4: 
                break
            data_dict = {}

            reset_df = data[data['news_type'] == news_type].reset_index(drop=True)

            id = reset_df.loc[i].id
            title = reset_df.loc[i].title
            time = reset_df.loc[i].date
            
            # if reset_df.loc[i].qa_span != None:
            #     description = reset_df.loc[i].qa_span
            # else :
            if reset_df.loc[i].contents == '다.':
                description = ''
            else:
                description = reset_df.loc[i].summary
                description = " ".join(re.split(r"\s+", str(description)))

            imageUrl = reset_df.loc[i].image_url
            webLinkUrl = reset_df.loc[i].news_url
            data_dict['title'] = title
            data_dict['description'] = description
            data_dict['thumbnail'] = {"imageUrl": imageUrl}
            data_dict['buttons'] = [{"action": "block", "label": "기사 요약하기",
                                     "messageText": '[기사제목] \n\n' + title + '\n\n[작성 시간]\n' + time + '\n\n[기사 요약]\n\n' + description,
                                     "blockId" : "625a8ab6b11ff05fbedde0ff",
                                     "extra" : {"id" : id, "news_type" : news_type, "title" : title, "webLinkUrl": webLinkUrl}
                                    },
                                    {"action": "webLink", "label": "뉴스기사 보러가기", "webLinkUrl": webLinkUrl}]

            data_list.append(data_dict)

        all_data_dict[news_type] = data_list
    return "update success"

@app.route('/count', methods=['POST'])
def Count():
    content = request.get_json()
    clientExtra = content['action']['clientExtra']
    if clientExtra['news_type'] != 'last_most_view':
        back_logger_info(clientExtra['id']+'|| '+ clientExtra['webLinkUrl']+' || '+ clientExtra['title'])
    dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": all_data_dict[clientExtra['news_type']]
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }
    return jsonify(dataSend)

@app.route('/message', methods=['POST'])
def Message():
    content = request.get_json()
    content = content['userRequest']
    content = content['utterance']
    if content == u"헤드라인 기사":
        back_logger_info(content)
        dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": all_data_dict['today_main_news']
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }
    elif content == u"정치 뉴스":
        back_logger_info(content)
        dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": all_data_dict['section_politics']
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }
    elif content == u"경제 뉴스":
        back_logger_info(content)
        dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": all_data_dict['section_economy']
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }
    elif content == u"사회 뉴스":
        back_logger_info(content)
        dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": all_data_dict['section_society']
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }
    elif content == u"생활/문화 뉴스":
        back_logger_info(content)
        dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": all_data_dict['section_life']
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }
    elif content == u"세계 뉴스":
        back_logger_info(content)
        dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": all_data_dict['section_world']
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }
    elif content == u"IT/과학 뉴스":
        back_logger_info(content)
        dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": all_data_dict['section_it']
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }
    elif content == u"어제 가장 많이 본 뉴스":
        back_logger_info(content)
        dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": all_data_dict['last_most_view']
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }
    else:
        back_logger_info(content,2)
        dataSend = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "버튼으로 클릭해주세요"
                        }
                    }
                ],
                "quickReplies": quick_replies
            }
        }

    return jsonify(dataSend)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6006)

