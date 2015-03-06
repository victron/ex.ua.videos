# -*- coding: utf-8 -*-
__author__ = 'vic'

import re, requests
from bs4 import BeautifulSoup
import xbmc, xbmcgui
from addon import connect_timeout, read_timeout, max_retries, too_slow_connection, waited_too_long_between_bytes,\
    get_an_HTTPError, not_expected_output
# get web page source
dialog = xbmcgui.Dialog()

def GetHTML(url):
    headers = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) '
                            'Gecko/2008092417 Firefox/3.0.3',
               'Content-Type':'application/x-www-form-urlencoded'}
    session = requests.Session()
    session.mount("http://", requests.adapters.HTTPAdapter(max_retries=max_retries))
#    connect_timeout = 2.0011
#    read_timeout = 1.0
    try:
        response = session.get(url= url, timeout=(connect_timeout, read_timeout))
        #response = requests.get(url, timeout=(connect_timeout, read_timeout))
    except requests.exceptions.ConnectTimeout as e:
        xbmc.log(msg='[ex.ua.videos]' + 'Too slow connection', level=xbmc.LOGWARNING)
        return dialog.notification('connection problem', too_slow_connection, xbmcgui.NOTIFICATION_WARNING, 5000, True)
    except requests.exceptions.ReadTimeout as e:
        xbmc.log(msg='[ex.ua.videos]' + 'Waited too long between bytes.', level=xbmc.LOGERROR)
        return dialog.notification('connection problem', waited_too_long_between_bytes,
                                   xbmcgui.NOTIFICATION_WARNING, 5000, True)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        xbmc.log(msg='[ex.ua.videos]' + 'get an HTTPError: ' + e.message, level=xbmc.LOGERROR)
        return dialog.notification('connection problem', get_an_HTTPError + e.message,
                                   xbmcgui.NOTIFICATION_WARNING, 5000, True)
#    response = requests.get(url)
    return response.text

def get_categories(lang='uk'):
    """return [(category, link), (.., ..)]"""
    html = GetHTML('http://www.ex.ua/' + lang + '/video')
    #<a href='/82470?r=80934'><b>Закордонне кіно</b></a><p><a href='/82470?r=80934' class=info>
    #<b>Закордонне кіно</b></a><p><a href='/82470?r=80934' class=info>
    result_list = re.compile('<b>(.+?)</b></a><p><a href=\'(.+?)\' class=info>').findall(html) #.decode('utf-8'))
    if result_list:
        return result_list
    else:
        xbmc.log(msg='[ex.ua.videos]' + 'not expected output', level=xbmc.LOGWARNING)
        return dialog.notification('Server output', not_expected_output, xbmcgui.NOTIFICATION_WARNING, 5000, True)


def get_movie_list(category, page):
    """:returns ( [link, .., ..], next_page_flag, original_id)"""
    page = str(page)
    html = GetHTML('http://www.ex.ua' + category + '&p=' + page)
    # <img src='http://fs64.www.ex.ua/show/151452178/151452178.jpg?200' width='137' height='200' border='0' alt='Танкістка / Дівчина-танк / Tank Girl (1995) HDTVRip Ukr/Eng'></a><p><a href='/86793599?r=82470'><b>Танкістка / Дівчина-танк / Tank Girl (1995) HDTVRip Ukr/Eng</b></a><br><a href='/user/Worms2012'>Worms2012</a>,&nbsp;<small>0:39, 14 февраля 2015</small>
    soup = BeautifulSoup(html)
    if soup.find(attrs={"name": "original_id"}) is not None:
        original_id = soup.find(attrs={"name": "original_id"})["value"] # category id
    else:
        original_id = 'NONE'
    # ------- alternative -------
#   _result_n = []
#        for img in soup.find_all('img', attrs = {'border' : "0", 'height' :"200"}):
#            _result_n.append(img.parent['href'])
    if soup.find('img', alt=u'вы находитесь на последней странице') is None:
        next_page_flag = True
    else:
        next_page_flag = False
    return re.compile('</a><p><a href=\'(.+?)\'>').findall(html), next_page_flag, original_id


def get_search_list(original_id, search_request, page):
    """
    search in movie category
    :param original_id: string
    :param search_request: string
    :param page: integer; number of page
    :return: ([link, .., ..], next_page_flag)
    """
    page = str(page)
    html = GetHTML('http://www.ex.ua' +'/search?original_id=' + original_id + '&s=' + search_request + '&p=' + page)
    soup = BeautifulSoup(html)
    _result = []
    for img in soup.find_all('img', attrs = {"align":"left"}):
        _result.append(img.parent['href'])
#    for link in soup('a'):
#        if link.find('img', align="left") is not None:
#            _result.append((re.findall('(.+?)\?.*', link.img['src'])[0], link.img['alt'], link['href']))
    if soup.find('img', alt=u'вы находитесь на последней странице') is None:
        next_page_flag = True
    else:
        next_page_flag = False
    return _result , next_page_flag


def get_playlist(movie):
    """
    :param movie: link to movie
    :return: [( file_title, link), (.., ..)]
    """
    html = GetHTML('http://www.ex.ua' + movie)
    # <a href='/playlist/85726671.m3u' rel='nofollow'><b>плей-лист</b></a>, <a href='/playlist/85726671.xspf' rel='nofollow'>.xspf</a></small></td>
    xspf_link = re.compile('</b></a>, <a href=\'(.+?)\' rel=\'nofollow\'>\.xspf').findall(html)
    if not xspf_link:
        xbmc.log(msg='[ex.ua.videos]' + 'there are no <xspf_link>', level=xbmc.LOGDEBUG)
        return None
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
    """
    # not the best solution, but such infoLabels from xbmcgui.setInfo as 'trailer' and 'code' used for transfering
    # fanart link information about played files on page or not
    :param link: to movie page
    :return: {'title' : <..>, 'trailer' : <..>, 'code' : <..>, 'year': <..>, 'genre': <..>, 'director': <..>,
                'duration': <..>, 'plot': <..>, 'cast': <..>}
    """
    html_page = GetHTML('http://www.ex.ua' + link)
    xbmc.log(msg='[ex.ua.videos]' + 'GetHTM request =>>> ' + str(link), level=xbmc.LOGDEBUG)
    kodi_details = {}
    soup = BeautifulSoup(html_page, 'html.parser')
    # there is some strange behaviour if 'html.parser' missing
    kodi_details['title'] = soup.body.find(name='img', attrs={'align':'left'}).get('alt')
#    kodi_details['title'] = soup.head.find(name='meta', attrs={'name':"title"}).get('content', 'NNNN')
    # 'trailer' used to save a link on fanart
    kodi_details['trailer'] = re.findall('(.+?)\?.*',
                                         soup.body.find(name='img', attrs={'align':'left'}).get('src'))[0]
    xspf = soup.body.find(name='a', attrs={'rel' : 'nofollow'}, text='.xspf')
    file_list = soup.body.find(name='a', attrs={'rel' : 'nofollow'}, text=u'файл-лист')
    play_list = soup.body.find(name='a', attrs={'rel' : 'nofollow'}, text=u'плей-лист')
    if xspf is not None or file_list is not None or play_list is not None:
        # playlist xspf not found on page
        #kodi_details['code'] = soup.body.find(name='a', attrs={'rel' : 'nofollow'}, text='.xspf').get('href')
        kodi_details['code'] = 'show_files_list'
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
    else:
        kodi_details['code'] = 'show_movies_2'
    return kodi_details


