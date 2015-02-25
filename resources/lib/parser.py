# -*- coding: utf-8 -*-
__author__ = 'vic'

import re, requests
from regex_collection import movie_info
from bs4 import BeautifulSoup
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
    return re.compile('<img src=\'(.+?)\?.*?alt=\'(.+?)\'></a><p><a href=\'(.+?)\'>').findall(html), next_page_flag, original_id


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


def get_movie_info(link):
    html = GetHTML('http://www.ex.ua' + link)
    return movie_info(html)

