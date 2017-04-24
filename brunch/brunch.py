#-*- coding: utf-8 -*-
import codecs
import time
import re
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

def job_function():
    now = datetime.now()
    nowDatetime = now.strftime('%Y-%m-%d_%H')
    print(nowDatetime)
    #print ( '%s-%s-%s' % ( now.year, now.month, now.day ) )
    #date = '%s-%s-%s_%s:%s' % ( now.year, now.month, now.day, now.hour, now.min )
    #date = str(now)
    date = nowDatetime
    #date_name = '%s-%s-%s_%s:%s' % ( now.year, now.month, now.day, now.hour, now.min )
    date_name = nowDatetime

    file_txt = path + date_name+'_tracking.txt'
    file_html = path + date_name+'_recommended.html'
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36"
    )
    driver = webdriver.PhantomJS(desired_capabilities=dcap,executable_path=r'../../phantomjs-binaries/bin/phantomjs-2.1.1-linux-armhf')
    driver.implicitly_wait(5)
    driver.get(url)
    #driver.find_element_by_id('mArticle')

    w=codecs.open(file_txt, encoding='utf-8', mode='w')
    w2=codecs.open(file_html, encoding='utf-8', mode='w')

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    #print (soup)

    result = soup.findAll("a", {"class":"keyword_item"})
    print (str(len(result))) #24
    #print (result)

    #time.sleep(1)

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

    driver.implicitly_wait(3)
    for i in range(0, len(result)):
        #td_img=talk('span',{'class':'u_cbox_contents'})[i].find("span")
        #img = str(result[i].find('div',{'class':'img_articles'}).find('img'))
        #img_src = result[i].find('div',{'class':'img_articles'}).find('img')['src']
        #f = open("./img/" + str(i) + ".png", "wb")
        #img = re.sub("//", "http://", img)
        #img_req = urllib.request.Request(img)
        #f.write(urllib.request.urlopen(img_req).read())
        #f.close()

        title = result[i].find('strong',{'class':'tit_subject'}).text
        body = result[i].find('p',{'class':'desc_subject'}).text
        author = result[i].find('span',{'class':'info_by'}).text

        #print (img + '<br><h3>' + title + '</h3><br>' + body + '<p>\n')
        w2.write('<p><br><h3>' + title + '</h3><h6>' + author + '</h6>' + body + '</p>\n')
        logger.debug(title + ' ' + author.replace(u'\xa0', ' ') + ' : ' + body.replace(u'\u200b', ' '))

    w2.write('\n</body><html>')

    time.sleep(1)

    #import webbrowser
    #webbrowser.open(file_html) # see results

    w.close()
    w2.close()
    driver.quit()
    logger.info('Completed writing files')

    time.sleep(5)

    # Update on github
    r.git.add('.')
    r.git.commit(m=date_name)
    r.git.push()
    logger.info('Completed to commit and push on GitHub')

sched = BlockingScheduler()

# Schedules job_function to be run on the hour (and more)
sched.add_job(job_function, 'cron', minute='0-7,30-31')
sched.start()
