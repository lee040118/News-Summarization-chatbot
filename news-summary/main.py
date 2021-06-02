from selenium import webdriver
from bs4 import BeautifulSoup
import argparse
import datetime
import time, os
import pandas as pd
import multiprocessing
import warnings
import re
import json

warnings.filterwarnings(action='ignore')

BASE_DIR = '/tmp/chatbot'
DATA_DIR = 'crawl_data'

web = os.path.join(BASE_DIR, 'chromedriver')
_url = "https://news.naver.com/"

news_type_list = ['today_main_news', 'section_politics', 'section_economy', 'section_society','section_life','section_world','section_it']

def replace_all(text, dic):
    for j in dic.values():
        text = re.sub(j, '', text)
    return text

def preprocessing_div_contents(x):
    find_re = {
    "find_icon" : r"ⓒ[.]+",
    "find_reporter" : r"[가-힣]{2,4} ([가-힣])*기자",
    "find_email" : r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
    "find_things" : r'\[.+?\]',
    "find_useless_bracket" : r"\( *\)",
     "find_spaces" : r"  +"}

    main_contents = ' '.join(str(x).split('\n')[8:-2])
    inner_tags = list(map(lambda x: x[1:], re.findall(r"<[a-zA-z0-9]+", str(main_contents))))

    for tag in inner_tags:
        if tag == 'span': continue
        try:
            eval(f"x.{tag}.decompose()")
        except:
            pass

    final_contents = str(x).split('\n')[-3]
    result = replace_all(final_contents, find_re)

    tmp = ""
    flag = False
    for i in result:
        if i == '<':
            flag = True
            continue
        elif not flag:
            tmp += i
        elif i == '>':
            flag = False
    result = tmp
    result = '다.'.join(result.split('다.')[:-1]) + '다.'

    return result.strip()

def crawling(news_type):
    def get_news_info_df(news_type):
        title = driver.find_element_by_xpath('//*[@id="articleTitle"]').text
        date = driver.find_element_by_xpath('//*[@id="main_content"]/div[1]/div[3]/div/span[1]').text
        p = re.compile(r'[0-9]+.[0-9]+.[0-9]+')
        if p.match(date) is None:
            date = driver.find_element_by_xpath('//*[@id="main_content"]/div[1]/div[3]/div/span[2]').text

        contents = driver.find_element_by_xpath('//*[@id="articleBodyContents"]').text

        req = driver.page_source
        soup = BeautifulSoup(req, 'html.parser')
        pre_contents = soup.select("#articleBodyContents")[0]
        pre_contents = preprocessing_div_contents(pre_contents)
        image_url = get_poster_url()
        news_url = driver.current_url
        df = pd.DataFrame([news_type, title, date, contents, pre_contents, image_url, news_url]).T
        df.columns = ['news_type', 'title', 'date', 'all_contents', 'contents', 'image_url', 'news_url']
        return df

    def get_poster_url():
        # get the image source
        try:
                img = driver.find_element_by_class_name('end_photo_org').find_elements_by_tag_name('img')[0]
                src = img.get_attribute('src')
        except:
                src = "https://newsimg.sedaily.com/2019/01/23/1VE5F3W5WP_18.png"
        return src

    data_list = []
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('window-size=1920x1080')
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome('/tmp/chatbot/chromedriver', options=options)
    driver.get(_url)

    if news_type == 'today_main_news':
        try:
            driver.find_element_by_xpath('//*[@id="today_main_news"]/div[2]/div/div[1]/a[1]').click()
            driver.implicitly_wait(2)
            data_list.append(get_news_info_df(news_type))
            driver.back()
        except:
            driver.get(_url)
        for i in range(1, 5):
            driver.find_element_by_xpath('//*[@id="' + news_type + '"]/div[2]/ul/li[' + str(i) + ']/div[1]/a').click()
            driver.implicitly_wait(2)
            data_list.append(get_news_info_df(news_type))
            driver.back()
    else:
        try:
            driver.find_element_by_xpath('//*[@id="' + news_type + '"]/div[2]/dl/dt/a').click()
            driver.implicitly_wait(2)
            data_list.append(get_news_info_df(news_type))
            driver.back()
        except:
            driver.get(_url)

        for i in range(1, 5):
            driver.find_element_by_xpath('//*[@id="' + news_type + '"]/div[2]/div/ul/li[' + str(i) + ']/a').click()
            driver.implicitly_wait(2)
            data_list.append(get_news_info_df(news_type))
            driver.back()

    driver.quit()
    all_data = pd.concat(data_list)
    return all_data

def main(args):
        num_cpu = multiprocessing.cpu_count() - 1
        start_time = datetime.datetime.now()

        print("Start Time :", start_time)

        pool = multiprocessing.Pool(num_cpu)
        result = pool.imap(crawling, news_type_list)

        pool.close()
        pool.join()

        end_time = datetime.datetime.now()

        all_data = list(result)
        all_data = pd.concat(all_data).reset_index(drop=True)

        all_data.to_csv(os.path.join(BASE_DIR, DATA_DIR, start_time.strftime("%Y%m%d-%H") + '.csv', ), encoding='utf-8' ,index=False)
        print("End Date :", end_time)
        print(start_time.strftime("%Y%m%d-%H") + ', ' + str(all_data.shape) + ', 크롤링을 완료했습니다.')

if __name__ == "__main__":
        PARSER = argparse.ArgumentParser()
        ARGS = PARSER.parse_args()
        main(ARGS)


