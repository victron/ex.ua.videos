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

from xbmcswift2 import Plugin
import urllib, bs4, os, sys, xbmc, xbmcplugin
#from resources.lib.parser import get_categories, get_movie_list, get_playlist, get_movie_info, get_search_list
from resources.lib.parser import *

xbmc.log(msg='[ex.ua.videos]' + '----- start ----', level=xbmc.LOGDEBUG)

plugin = Plugin()
# settings
lang = plugin.get_setting('resources_language', int)
cache_flag = plugin.get_setting('cache_on_flag', bool)
cache_ttl = plugin.get_setting('cache_TTL', int) * 60
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

    categories_list = [{'label':category,
                        'path': plugin.url_for('show_movies', category=link,
                                               # encode category_name into url code
                                               category_name = urllib.quote_plus(category.encode('utf-8')),
                                                page = '0')}
                       # TODO: show first page, via multiple route
                       for category, link in categories ]
#    plugin.add_sort_method('label')
    categories_list.insert(0, {'label': search_everywhere + ' [.....]',
                           'path' : plugin.url_for('start_search_in', category= 'everywhere', original_id = '0',
                                                   category_name = 'search everywhere')})

    return plugin.finish(categories_list)


@plugin.route('/movies_list/<category>/category_name/<category_name>/page/<page>')
def show_movies(category, category_name, page):
    page = int(page)
    movies, next_page, original_id = get_movie_list(category, page)
    movies_list = [{'label':movie_title,
                    'thumbnail': thumbnail,
                    'info': get_movie_info_api(cache_flag, link),
                    'properties': {'fanart_image': thumbnail},
                    'path': plugin.url_for('show_files_list', movie=link,
                                           thumbnail_link = thumbnail, category_name = category_name)}
                   for thumbnail, movie_title, link in movies ]
    xbmc.log(msg='[ex.ua.videos]' + '<movies_list> = ' + str(movies_list), level=xbmc.LOGDEBUG)
    list_len = len(movies_list)
    if next_page:
        movies_list.insert(list_len, {'label': next_page_str + ' >>',
                                      'path': plugin.url_for('show_movies', category= category, page=str(page + 1),
                                      category_name = category_name)})
    if page > 0:
        movies_list.insert(-1, {'label': '<< ' + previous_page,
                                        'path': plugin.url_for('back')})
    movies_list.insert(0, {'label': search_in + ' '+ urllib.unquote_plus(category_name).decode('utf-8') + ' [.....]',
                           'path' : plugin.url_for('start_search_in', category= category, original_id = original_id,
                                                   category_name = category_name)})
    xbmcplugin.setContent(_addon_id, 'movies')
    return plugin.finish(movies_list, view_mode=504)


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
        else:
            return
    else:
        search_request = urllib.unquote_plus(search_request)
        movies, next_page = get_search_list(original_id, search_request, page)
    movies_list = [{'label':movie_title,
                    'thumbnail': thumbnail,
                    'info': get_movie_info_api(cache_flag, link),
                    'properties': {'fanart_image': thumbnail},
                    'path': plugin.url_for('show_files_list', movie=link,
                                           thumbnail_link = thumbnail, category_name = category_name)}
                   for thumbnail, movie_title, link in movies ]
    list_len = len(movies_list)
    if next_page:
        movies_list.insert(list_len, {'label': next_page_str + ' >>',
                                      'path': plugin.url_for('show_search_list_in', category= category, page=str(page + 1),
                                      category_name = category_name, original_id = original_id,
                                      search_request = urllib.quote_plus(search_request))})
    if page > 0:
        movies_list.insert(-1, {'label': '<< ' + previous_page,
                                        'path': plugin.url_for('back')})


    movies_list.insert(0, {'label': new_search_in + ' '+ urllib.unquote_plus(category_name).decode('utf-8') + ' [.....]',
                           'path' : plugin.url_for('start_search_in', category= category, original_id = original_id,
                                                   category_name = category_name)})
    xbmcplugin.setContent(_addon_id, 'movies')
    return plugin.finish(movies_list, view_mode=504) #, update_listing=True)


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

#===========================

@plugin.cached(cache_ttl)
def get_movie_info_cached(link):
    # transit function for plugin.cached decorator
    data = get_movie_info(link)
    return data

if __name__ == '__main__':
    plugin.run()
