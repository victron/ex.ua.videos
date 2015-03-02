# -*- coding: utf-8 -*-
__author__ = 'vic'

import re, requests
from bs4 import BeautifulSoup
import xbmc
# get web page source
def GetHTML(url):
    headers = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) '
                            'Gecko/2008092417 Firefox/3.0.3',
               'Content-Type':'application/x-www-form-urlencoded'}
    r = requests.get(url)
    return r.text

def get_categories(lang='uk'):
    """return [(category, link), (.., ..)]"""
    html = GetHTML('http://www.ex.ua/' + lang + '/video')
    #<a href='/82470?r=80934'><b>Закордонне кіно</b></a><p><a href='/82470?r=80934' class=info>
    #<b>Закордонне кіно</b></a><p><a href='/82470?r=80934' class=info>
    return re.compile('<b>(.+?)</b></a><p><a href=\'(.+?)\' class=info>').findall(html) #.decode('utf-8'))


def get_movie_list(category, page):
    """:returns [((thumbnail, movie_title, link), next_page_flag), ((.., .., ..),..)]"""
    page = str(page)
    html = GetHTML('http://www.ex.ua' + category + '&p=' + page)
    # <img src='http://fs64.www.ex.ua/show/151452178/151452178.jpg?200' width='137' height='200' border='0' alt='Танкістка / Дівчина-танк / Tank Girl (1995) HDTVRip Ukr/Eng'></a><p><a href='/86793599?r=82470'><b>Танкістка / Дівчина-танк / Tank Girl (1995) HDTVRip Ukr/Eng</b></a><br><a href='/user/Worms2012'>Worms2012</a>,&nbsp;<small>0:39, 14 февраля 2015</small>
    # TODO: checking for last page
    next_page_flag = True
    soup = BeautifulSoup(html)
    original_id = soup.find(attrs={"name": "original_id"})["value"] # category id
    #return re.compile('<img src=\'(.+?)\?.*?alt=\'(.+?)\'></a><p><a href=\'(.+?)\'>').findall(html), next_page_flag, original_id
    return re.compile('</a><p><a href=\'(.+?)\'>').findall(html), next_page_flag, original_id


def get_search_list(original_id, search_request, page):
    """
    search in movie category
    :param original_id: string
    :param search_request: string
    :param page: integer; number of page
    :return: ((thumbnail, movie_title, link), (..,..,..),next_page_flag)
    """
    page = str(page)
    html = GetHTML('http://www.ex.ua' +'/search?original_id=' + original_id + '&s=' + search_request + '&p=' + page)
    soup = BeautifulSoup(html)
    _result = []
    for link in soup('a'):
        if link.find('img', align="left") is not None:
            _result.append((re.findall('(.+?)\?.*', link.img['src'])[0], link.img['alt'], link['href']))
            #TODO: retur next_page_flag, if len of return 0 return False
    next_page_flag = True
    return _result , next_page_flag


def get_playlist(movie):
    """
    :param movie: link to movie
    :return: [( file_title, link), (.., ..)]
    """
    html = GetHTML('http://www.ex.ua' + movie)
    # <a href='/playlist/85726671.m3u' rel='nofollow'><b>плей-лист</b></a>, <a href='/playlist/85726671.xspf' rel='nofollow'>.xspf</a></small></td>
    xspf_link = re.compile('</b></a>, <a href=\'(.+?)\' rel=\'nofollow\'>\.xspf').findall(html)
    html = GetHTML('http://www.ex.ua' + xspf_link[0])
    return re.compile('\t<title>(.+?)</title>\n\t<location>(.+?)</location>').findall(html)


DETAILS_ukr_ru = {
            'year': (u'([Гг]од|[Рр]ік).*', u'(.*?([0-9]{4}))', '([0-9]{4})'),
            'genre': (u'[Жж]анр.*', u'.*?: *?(.*)', '.+'),
            'director': (u'([Рр]ежисс?[её]р|[Рр]ежисер).*', u'.*?: *?(.*)', '.+'),
            'duration': (u'(Продолжительность|Тривалість).*', u'.*?: *?(.*)', '.+'),
            'plot': (u'(Описание|О фильме|Сюжет|О чем|О сериале).*', u'.*?: *?(.*)', '.+'),
            'cast': (u'[ВвУу] ролях.*', u'.*?: *?(.*)', '.+')
                }


def get_movie_info(link):
    html_page = GetHTML('http://www.ex.ua' + link)
#    xbmc.log(msg='[ex.ua.videos]' + 'GetHTM request =>>> ' + str(link), level=xbmc.LOGDEBUG)
    kodi_details = {}
    soup = BeautifulSoup(html_page)
    kodi_details['title'] = soup.head.find(name='meta', attrs={'name':"title"}).get('content')
    kodi_details['trailer'] = re.findall('(.+?)\?.*',
                                           soup.head.find(name='link', attrs={'rel':"image_src"}).get('href'))[0]
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
#    xbmc.log(msg='[ex.ua.videos]' + '<kodi_details> =' + str(kodi_details), level=xbmc.LOGDEBUG)
    return kodi_details

