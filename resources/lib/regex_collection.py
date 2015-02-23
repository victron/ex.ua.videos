# -*- coding: utf-8 -*-
__author__ = 'vic'
import  re
from bs4 import BeautifulSoup
DETAILS_ukr_ru = {
            'year': (u'([Гг]од|[Рр]ік).*', u'(.*?([0-9]{4}))', '([0-9]{4})'),
            'genre': (u'[Жж]анр.*', u'.*?: *?(.*)', '.+'),
            'director': (u'([Рр]ежисс?[её]р|[Рр]ежисер).*', u'.*?: *?(.*)', '.+'),
            'duration': (u'(Продолжительность|Тривалість).*', u'.*?: *?(.*)', '.+'),
            'plot': (u'(Описание|О фильме|Сюжет|О чем|О сериале).*', u'.*?: *?(.*)', '.+'),
            'cast': (u'[ВвУу] ролях.*', u'.*?: *?(.*)', '.+')
                }

def movie_info(html_page):
    kodi_details = {}
    soup = BeautifulSoup(html_page)
    for detail in DETAILS_ukr_ru:
        search_detail = soup.find(text=re.compile(DETAILS_ukr_ru[detail][0], re.UNICODE))
        if search_detail is not None:
            detail_text = re.findall(DETAILS_ukr_ru[detail][1], search_detail, re.UNICODE)
            if detail_text and len(detail_text[0]) > 2:
                text = detail_text[0]
            else:
                next_ = search_detail.find_next(text=True)
                if len(next_) < 2:
                    next_ = search_detail.find_next(text=True).find_next(text=True)
                detail_text = re.findall(DETAILS_ukr_ru[detail][2], next_, re.UNICODE)
                if detail_text:
                    text = detail_text[0]
                    if text[0] == ':':
                        text = text.replace(':', '', 1)
                else:
                    text = None
            if detail == 'cast':
                kodi_details[detail] = (text,)
#            if detail == 'year':
#                kodi_details[detail] = int(text)
            else:
                kodi_details[detail] = text
    return kodi_details

