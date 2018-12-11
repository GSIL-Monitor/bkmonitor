#!/usr/bin/env python
# -*- coding:utf-8 -*-
import requests
import datetime
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient
from notify import *

client = MongoClient()
events_db = client.events 
events_info = events_db.events_info

def make_point(last_checktime):
    with open('/home/monitor/last_check.log', 'w') as f:
        f.write(last_checktime)
        

def check(begin, end, page=1):
    r = requests.post('http://192.168.0.100/history_event.php', 
                  data={'begintime':begin, 'endtime':end, 'page':page})    #"2018-11-20 17:59:00"

    soup = BeautifulSoup(r.text)
    warning_table = soup.find(id="liebiao").find_all('tr')
    warning_infos = warning_table[1:-1]
    
    if len(warning_infos) > 0 :
        first_warning = warning_infos[0].find_all('td')

        mm = Mailer()
        mm.sendemail('lugf@mail.sustc.edu.cn', ['lmmsuu@163.com'], first_warning[2].text,
                "{} {}".format(first_warning[3].text, first_warning[4].text))

    for w in warning_infos:
        tds = w.find_all('td')
        event = {'设备类型':tds[1].text, 
                 '事件名称':tds[2].text,
                 '发生时间':tds[3].text,
                 '结束时间':tds[4].text,
                 '持续时间':tds[5].text
                }
        try:
            events_info.insert_one(event)
        except Exception as e:
            print(e)
            return -1
        
    if page == 1:
        make_point(end)
        page_info = warning_table[-1].find('div').text   #'共0条|< << 1 >> >| [1]'   共2780条|< << [1] 2 3 >> >| [278]
        total_page = int(page_info.split('|')[2][2:-1])
        if total_page > 1:
            for page in range(2, total_page+1):
                if check(begin, end, page) == -1:
                    print('Fatal Error, just quit')
                    return -1
                
    return len(warning_infos)

if __name__ == '__main__':
    with open("/home/monitor/last_check.log", 'r') as f:
        last_checktime = f.readline()

    begin_time = last_checktime
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = check(begin_time, end_time)
