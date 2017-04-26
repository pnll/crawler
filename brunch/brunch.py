#-*- coding: utf-8 -*-
import codecs
import time
import re
import json
from datetime import datetime
from git import Repo
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import logging
import logging.handlers

#Cron type scheduler
from apscheduler.schedulers.blocking import BlockingScheduler

url = 'https://brunch.co.kr/'
urlKeyword = 'https://api.brunch.co.kr/v1/top/keyword'

path = './record/'
#os.chdir(path)
r = Repo('../')

# logger 인스턴스를 생성 및 로그 레벨 설정
logger = logging.getLogger("crumbs")
logger.setLevel(logging.DEBUG)

# formmater 생성
formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')

# fileHandler와 StreamHandler를 생성
fileHandler = logging.FileHandler('./log/scheduler.log')
streamHandler = logging.StreamHandler()

# handler에 fommater 세팅
fileHandler.setFormatter(formatter)
streamHandler.setFormatter(formatter)

# Handler를 logging에 추가
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)


def init_phantomjs_driver(*args, **kwargs):

    headers = { 'User-Agent': 'brunch/1.5.5 Dalvik/2.1.0 (Linux; U; Android 7.0; SM-G935S Build/NRD90M)',
        'BRUNCH-CLIENT-VERSION': '1.5.5',
        'BRUNCH-CLIENT-OS': 'and',
        'Host': 'api.brunch.co.kr',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }

    for key, value in headers.items():
        webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.{}'.format(key)] = value

    webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'

    driver =  webdriver.PhantomJS(*args, **kwargs)

    return driver


def job_function():
    now = datetime.now()
    nowDatetime = now.strftime('%Y-%m-%d_%H')
    print(nowDatetime)
    #print ( '%s-%s-%s' % ( now.year, now.month, now.day ) )
    #date = str(now)
    date = nowDatetime
    #date_name = '%s-%s-%s_%s:%s' % ( now.year, now.month, now.day, now.hour, now.minute )
    date_name = nowDatetime

    file_txt = path + date_name+'_keyword.txt'
    file_html = path + date_name+'_recommended.html'
    file_json = path + date_name+'.json'
    w=codecs.open(file_txt, encoding='utf-8', mode='a')

    if now.minute%2:
        w2=codecs.open(file_html, encoding='utf-8', mode='w')
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36"
        )
        driver = webdriver.PhantomJS(desired_capabilities=dcap,executable_path=r'../../phantomjs-binaries/bin/phantomjs-2.1.1-linux-armhf')
        driver.get(url)
        driver.implicitly_wait(5)
        
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        #print (soup)

        result = soup.findAll("a", {"class":"keyword_item"})
        print (str(len(result))) #24
        #print (result)

        for i in range(0, len(result)):
            keyword = result[i].find('span',{'class':'keyword_item_txt'}).text
            link = result[i]['href']

            #print (date + ' > ' + keyword + ' : ' + link)
            w.write(date+',\t' + keyword + ',\t' + link + ',\t\n')
            logger.info(keyword + ' : ' + link)
            #driver.find_element_by_class_name('keyword_item_txt')[i].click() #post_title has_image

        result = soup.find("div", {"class":"recommend_articles"}).findAll("a", {"class":"link_slide"})
        print (str(len(result))) #30
        #print (result)
        w2.write('''<html>
            <head>
                <meta charset="UTF-8">
            </head>
            <title>RECOMMENDED ARTICLES</title>
            <body><p>'''+str(now)+'</p>\n')

        for i in range(0, len(result)):
            org = result[i].find('div',{'class':'img_articles'})
            if org is None:
                img = ''
            else:
                img = str(org.find('img'))
                #img_src = result[i].find('div',{'class':'img_articles'}).find('img')['src']
                img = re.sub('src="//', 'src="http://', img)

            title = result[i].find('strong',{'class':'tit_subject'}).text
            body = result[i].find('p',{'class':'desc_subject'}).text
            author = result[i].find('span',{'class':'info_by'}).text

            #print (img + '<br><h3>' + title + '</h3><br>' + body + '<p>\n')
            w2.write('<p>' + img + '<br><h3>' + title + '</h3><h6>' + author + '</h6>' + body + '</p>\n')
            logger.debug(title + ' ' + author.replace(u'\xa0', ' ') + ' : ' + body.replace(u'\u200b', ' '))

        w2.write('\n</body><html>')
        w2.close()

    else:
        w3=codecs.open(file_json, encoding='utf-8', mode='w')
        driver = init_phantomjs_driver(executable_path=r'../../phantomjs-binaries/bin/phantomjs-2.1.1-linux-armhf')
        driver.get(urlKeyword)
        driver.implicitly_wait(5)
        
        pre = driver.find_element_by_tag_name("pre").text
        data = json.loads(pre)
        #print (data)
        w3.write(pre)

        for l in data['data']['list']:
            if l['type'] == "KEYWORD_ARTICLE_AUTO":
                title = l['contents']['keywordTitle']
                groupNo = str(int(l['contents']['groupNo']))
                w.write(date+',\t' + groupNo + ',\t' + title + ',\t\n')
                logger.info(groupNo + ' : ' + title)
            #if 'keywordTitle' in l['contents']:
        logger.debug('Completed writing JSON - keyword file')
        w3.close()


        time.sleep(1)
        driver.quit()
        time.sleep(10)

        w4=codecs.open(path+date_name+'_popular.json', encoding='utf-8', mode='w')
        driver = init_phantomjs_driver(executable_path=r'../../phantomjs-binaries/bin/phantomjs-2.1.1-linux-armhf')
        driver.get('https://api.brunch.co.kr/v1/top/keyword/data/article/popular')
        driver.implicitly_wait(5)
        pre = driver.find_element_by_tag_name("pre").text
        data = json.loads(pre)
        w4.write(pre)
        logger.debug('Completed writing JSON - popular file')
        w4.close()


    time.sleep(1)

    #import webbrowser
    #webbrowser.open(file_html) # see results

    w.close()
    driver.quit()
    logger.debug('Completed writing files')

    time.sleep(1)

    # Update on github
    r.git.add('.')
    r.git.commit(m=date_name)
    r.git.push()
    logger.debug('Completed to commit and push on GitHub')


sched = BlockingScheduler()

# Schedules job_function to be run on the hour (and more)
sched.add_job(job_function, 'cron', minute='0-1,30-31')
sched.start()
