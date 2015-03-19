# -*- coding: utf-8 -*-
'''
    Ex.Ua.videos plugin for KODI (XBMC)
    Copyright (C) 2015 Viktor Tsymbalyuk
	viktor.tsymbalyuk@gmail.com
    This file is part of plugin .

    Ex.Ua.videos is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Ex.Ua.videos is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Ex.Ua.videos.  If not, see <http://www.gnu.org/licenses/>.
'''

from xbmcswift2 import Plugin, actions
import urllib, bs4, os, sys, xbmc, xbmcplugin, time
from multiprocessing import Pool
#from resources.lib.parser import get_categories, get_movie_list, get_playlist, get_movie_info, get_search_list
from resources.lib.parser import *

xbmc.log(msg='[ex.ua.videos]' + '----- start ----', level=xbmc.LOGDEBUG)

plugin = Plugin()
# settings
lang = plugin.get_setting('resources_language', int)
cache_flag = plugin.get_setting('cache_on_flag', bool)
cache_ttl = plugin.get_setting('cache_TTL', int) * 60
connect_timeout = float(plugin.get_setting('connect_timeout'))
read_timeout = float(plugin.get_setting('read_timeout'))
max_retries = plugin.get_setting('max_retries', int)
pages_preload = plugin.get_setting('pages_preload', int)

_addon_id = int(sys.argv[1])
addon_path = plugin.addon.getAddonInfo('path').decode('utf-8')
#sys.path.append(os.path.join(addon_path, 'resources', 'lib'))


# localization
import xbmcaddon
addon = xbmcaddon.Addon()
next_page_str = addon.getLocalizedString(30024)
previous_page = addon.getLocalizedString(30025)
search_in = addon.getLocalizedString(30021)
search_everywhere = addon.getLocalizedString(30022)
new_search_in = addon.getLocalizedString(30023)
too_slow_connection = addon.getLocalizedString(32024)
waited_too_long_between_bytes = addon.getLocalizedString(32025)
get_an_HTTPError = addon.getLocalizedString(32026)
not_expected_output = addon.getLocalizedString(32027)

get_movie_info_api = lambda cache_flag, link : get_movie_info_cached(link) if cache_flag else get_movie_info(link)

LANGUAGES= ('uk', 'en', 'ru')
lang = LANGUAGES[lang]

xbmc.executebuiltin('Skin.SetBool(AutoScroll)')
"""
msgctxt "#20189"
msgid "Enable auto scrolling for plot & review"
settings maping in /usr/share/kodi/addons/skin.confluence/720p/SkinSettings.xml
"""

@plugin.route('/')
def show_categories():
    categories = get_categories(lang)
    if categories is None:
        return
    categories_list = [{'label':category,
                        'path': plugin.url_for('show_movies', category=link,
                                               # encode category_name into url code
                                               category_name = urllib.quote_plus(category.encode('utf-8')),
                                                page = '0')}
                       # TODO: show first page, via multiple route
                       for category, link in categories ]
#    plugin.add_sort_method('label')
    categories_list.insert(0, {'label': '[COLOR FF00FFFF]' + search_everywhere + ' [.....]' + '[/COLOR]',
                           'path' : plugin.url_for('start_search_in', category= 'everywhere', original_id = '0',
                                                   category_name = 'search everywhere')})

    return plugin.finish(categories_list)

@plugin.route('/movies_list/<category>/category_name/<category_name>',
              name = 'show_movies_2', options = {'page' : '0'})
@plugin.route('/movies_list/<category>/category_name/<category_name>/page/<page>')
def show_movies(category_name, page, category= None, movie = None):
    page = int(page)
    movies, next_page, original_id = get_movie_list(category, page)
    movies_info = [get_movie_info_api(cache_flag, link) for link in movies]
    movies_list = [{'label': movies_info[i].get('title'),
                    'thumbnail': movies_info[i].get('trailer'),
                    'info': movies_info[i],
                    'properties': {'fanart_image': movies_info[i].get('trailer')},
                    'path': plugin.url_for(movies_info[i].get('code'),
                                           movie=movies[i], # for show_files_list function
                                           category = movies[i], # for show_movies function
                                            # in case movies_info[i].get('code') == 'show_movies_2'
                                           thumbnail_link = movies_info[i].get('trailer'), category_name = category_name)}
                   for i in range(len(movies)) ]
    #xbmc.log(msg='[ex.ua.videos]' + '<movies_list> = ' + str(movies_list), level=xbmc.LOGDEBUG)
    list_len = len(movies_list)
    if next_page:
        movies_list.insert(list_len, {'label': '[COLOR blue]' + next_page_str + ' >>' + '[/COLOR]',
                                      'path': plugin.url_for('show_movies', category= category, page=str(page + 1),
                                      category_name = category_name)})
    if page > 0:
        if next_page:
            prev_page_link_posision = -1
        else:
            prev_page_link_posision = list_len
        movies_list.insert(prev_page_link_posision, {'label': '[COLOR FFF0E68C]' + '<< ' + previous_page + '[/COLOR]',
                                        'path': plugin.url_for('back')})
    movies_list.insert(0, {'label': '[COLOR green]' +
                                    search_in + ' '+ urllib.unquote_plus(category_name).decode('utf-8') + ' [.....]' +
                                    '[/COLOR]',
                           'path' : plugin.url_for('start_search_in', category= category, original_id = original_id,
                                                   category_name = category_name)})
    xbmcplugin.setContent(_addon_id, 'movies')
    if xbmc.Monitor().onSettingsChanged():
        xbmc.log(msg='[ex.ua.videos]' + '------ SettingsChanged --------', level=xbmc.LOGDEBUG)

    xbmc.log(msg='[ex.ua.videos]' + '<show_movies> finished ------------', level=xbmc.LOGDEBUG)
    return plugin.finish(movies_list, view_mode=504) , preload_page(pages_preload, page + 1, category, next_page )


@plugin.route('/back', name = 'back')
# call "back"
def previous_view():
    return xbmc.executebuiltin('Action("back")')

@plugin.route('/movies_list/<category>/category_name/<category_name>/page/<page>/original_id/<original_id>',
              name = 'start_search_in', options = {'start_search' : True, 'page' : '0'})
@plugin.route('/movies_list/<category>/category_name/<category_name>/page/<page>/original_id/<original_id>/search_request/<search_request>')
def show_search_list_in(category, category_name, page, original_id, start_search = False, search_request = ''):
    page = int(page)
    if start_search and len(search_request) == 0:
        search_request = plugin.keyboard()
        if search_request is not None:
            movies, next_page = get_search_list(original_id, search_request, page)
            movies_info = [get_movie_info_api(cache_flag, link) for link in movies]
        else:
            return
    else:
        search_request = urllib.unquote_plus(search_request)
        movies, next_page = get_search_list(original_id, search_request, page)
        movies_info = [get_movie_info_api(cache_flag, link) for link in movies]
    movies_list = [{'label':movies_info[i].get('title'),
                    'thumbnail': movies_info[i].get('trailer'),
                    'info': movies_info[i],
                    'properties': {'fanart_image': movies_info[i].get('trailer')},
                    'path': plugin.url_for(movies_info[i].get('code'),
                                           movie=movies[i],
                                           category = movies[i],
                                           thumbnail_link = movies_info[i].get('trailer'),
                                           category_name = category_name)}
                    for i in range(len(movies)) ]
    list_len = len(movies_list)
    if next_page:
        movies_list.insert(list_len, {'label': '[COLOR FF00BFFF]' + next_page_str + ' >>' + '[/COLOR]',
                                      'path': plugin.url_for('show_search_list_in', category= category, page=str(page + 1),
                                      category_name = category_name, original_id = original_id,
                                      search_request = urllib.quote_plus(search_request))})
    if page > 0:
        if next_page:
            prev_page_link_posision = -1
        else:
            prev_page_link_posision = list_len
        movies_list.insert(prev_page_link_posision, {'label': '[COLOR FFBDB76B]' + '<< ' + previous_page + '[/COLOR]',
                                        'path': plugin.url_for('back')})


    movies_list.insert(0, {'label': '[COLOR FF7FFFD4]' +
                                    new_search_in + ' '+ urllib.unquote_plus(category_name).decode('utf-8') + ' [.....]'
                                    + '[/COLOR]',
                           'path' : plugin.url_for('start_search_in', category= category, original_id = original_id,
                                                   category_name = category_name)})
    xbmcplugin.setContent(_addon_id, 'movies')
    return plugin.finish(movies_list, view_mode=504), \
           preload_page_search(pages_preload, page + 1, original_id, search_request, next_page )


@plugin.route('/files/<movie>/thumbnail/<thumbnail_link>/category_name/<category_name>')
def show_files_list(movie, thumbnail_link, category_name):
    files = get_playlist(movie)
    files_list = [{'label': file_title,
                   'thumbnail': thumbnail_link,
                   'properties': {'fanart_image': thumbnail_link},
                   'path': link,
                   'is_playable': True} for  file_title, link in files]
    currentPlaylist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    currentPlaylist.clear()
    plugin.add_to_playlist(files_list)
    if currentPlaylist.size() == 1:
        player = xbmc.Player(xbmc.PLAYER_CORE_AUTO)
        player.play(currentPlaylist)
    else:
        xbmc.executebuiltin("ActivateWindow(VideoPlaylist)")

#=============== cache functions ============

@plugin.cached(cache_ttl)
def get_movie_info_cached(link):
    # transit function for plugin.cached decorator
    data = get_movie_info(link)
    return data


def preload_page(page_number, start_page_number, category, next_page ):
    if next_page:
        for page in range(page_number):
            movies, next_page, original_id = get_movie_list(category, start_page_number + page)
            [get_movie_info_cached(link) for link in movies]
            if not next_page:
                break

def preload_page_search(page_number, start_page_number, original_id, search_request, next_page ):
    if next_page:
        for page in range(page_number):
            movies, next_page = get_search_list(original_id, search_request, start_page_number +page)
            [get_movie_info_cached(link) for link in movies]
            if not next_page:
                break

# TODO:
"""
class LazyMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        xbmc.log(msg='[ex.ua.videos]' + '------ init LazyMonitor --------', level=xbmc.LOGDEBUG)

    def onSettingsChanged(self):
        #update the settings
        xbmc.log(msg='[ex.ua.videos]' + '------ SettingsChanged --------', level=xbmc.LOGDEBUG)
        #actions.update_view('/')
        """

if __name__ == '__main__':
    plugin.run()
