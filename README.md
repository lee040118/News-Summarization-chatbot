# News Summarization chatbot

### 프로젝트 목표

- 요약 시스템을 통해 실시간 기사 요약문을 제공하는 챗봇 서비스

  

### 데이터 파이프라인

![](/news-summary/image/chatbot.png)

#### 1. ETL

1. 카테고리별 네이버 뉴스 기사를 수집합니다
2. 수집된 기사들을 전처리 후 요약 모델을 통해  요약문을 생성합니다
3. 가공된 데이터들을 DW(postgreSQL)에 적재합니다

#### 2.  User Service

1. 카카오톡 챗봇(요기어때)을 통해 유저들에게 서비스를 제공합니다
2. 유저들이 카테고리 별 뉴스를 요청하면 Flask를 통해 serving된 서버에서 뉴스와 요약문을 전송합니다

#### 3. Business Intelligence

1. 서버 로그들을 Logstash를 통해 수집 & 파싱 합니다

2. 로그들을 Elasticsearch에 적재후 Kibana를 통해 대시보드를 생성합니다

3. 분석된 로그들을 슬랙 채널에 메시지를 전송합니다

#### 4. Scheduling

1. Airflow를 활용해여 batch scheduling을 실시합니다



### 1. ETL

#### - Extract & Transform

네이버 뉴스를 카테고리(헤드라인,정치, 경제, 사회, 생활/문화, IT/과학, 세계) 별로 수집하고 전처리를 통해 노이즈 데이터를 제거합니다. 

요약 모델은 두 가지의 모델을 사용해 구성했습다

1. 본문을 입력했을 때 요약문을 생성해주는 요약문으로 transformer의 Encoder와 Decoder구조를 사용하는 BART모델을 한국어 데이터셋으로 pretraining시킨 SKT KoBART를 국립국어원 dataset으로 fine-tunning 시켰습니다
2. 사실 불일치 문제(추상 요약 모델이 생성하는 요약문이 본문 내용과 일치 하지 않는 문제)를 해결하기 위해 KoElectra의 QA모델을 사용해 요약문에서 잘못 생성된 개체명에 대해 QA 모델을 통해 정답 개체명을 뽑아내 교체하는 방식으로  fine-tuning 시켰습니다

##### 요약 모델 개요도 

![](/news-summary/image/summary_model.png)

1. Abs Summary 모델을 통해 input으로 들어오는 기사 본문을 상황에 맞게 단어를 생성 또는 추출해 요연한 요약문을 만든다.
2. Fact Correction 모델은 Abs summary 모델을 통해 만들어진 요약문이 본문 내용과 다른 내용이 생성된 부분을 찾아 post-editing 방식으로 요약문을 수정한다.

#### - Load

news_data라는 네임으로 DB 테이블을 생성하고 수집 날짜를 id 값으로 스키마를 작성하고 저장합니다.

##### 로우 데이터 예시

![](/news-summary/image/postgre.png)



### 2. User Service

카카오톡 챗봇을 통해 유저들에게 기사 요약서비스를 제공합니다.

![](/news-summary/image/example.png) 



### 3. Business Intelligence

#### - Logstash & ElasticSearch

1. 챗봇 서버 flask의 로그를 Logstash의  input으로 받습니다
2. filter을 통해 log들을 파싱해주고 output으로 elastic에 전송해줍니다.

#### - Kibana

1. 키바나에서 엘라스틱 서치에 적재한 데이터를 확인할 수 있습니다.
2. 날짜별로 로그 데이터들을 키바나를 통해 시각화 합니다.

##### Discover

![](/news-summary/image/kibana2.png)

##### Dashboard

![](/news-summary/image/kibana.png)

#### - Notification Bot

1. 엘라스틱 서치에서 오늘 날짜에 해당하는 데이터를 요청하고 데이터를 분석합니다.
2. 카테고리별 기사 순위 분석하여 슬랙 채널에 전송합니다.

<img src="/news-summary/image/slack.png" style="zoom: 67%;" /> 



### 4. Scheduling

기존 스케줄링은 cron을 활용하였으나 아래와 같은 문제점들 때문에 Airflow를 활용해 스케줄링 하였습니다.

##### 기존 Cron 방식의 문제점

- 실패 복구 시점 (예외발생시 쉽게 보고 가능)
- 모니터링 힘들다
- 분산된 환경에서 파이프라인들을 관리하기 힘들다
- 새로운 워크플로우를 배포하기 힘들다

##### Airflow 장점

- 파이썬으로 쉬운 프로그래밍
- 분산된 환경에서 확정성이 있음
- 웹 대시보드
- 커스터마이징

#### - DAG Graph

![](/news-summary/image/dag1.png)

![](C:\Users\HOON\Desktop\chatbot\news-summary\image\dag2.png)

#### - Tree View

![](/news-summary/image/tres.png)

## 프로젝트 결과

[![Video Label](http://img.youtube.com/vi/y3klQg9euP0/0.jpg)](https://www.youtube.com/watch?v=y3klQg9euP0)



### 기대 효과 및 활용 방안 

- 바쁜 현대인들의 일상 속에 해당 프로젝트 결과물을 통해 쉽게 최근 헤드라인  뉴스를 이해 할 수 있다.
- 길이가 길고 여러 문단으로 나눠져 있는 기사를 쉽게 이해 할 수 있다.
