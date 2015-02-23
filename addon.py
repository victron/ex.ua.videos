# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, xbmcplugin
import urllib, bs4, os, sys
from resources.lib.parser import get_categories, get_movie_list, get_playlist, get_movie_info, get_search_list

plugin = Plugin()
# TODO: change languages
lang = 'ru'
_addon_id = int(sys.argv[1])
addon_path = plugin.addon.getAddonInfo('path').decode('utf-8')
sys.path.append(os.path.join(addon_path, 'resources', 'lib'))
#@plugin.route('/')
@plugin.cached_route('/')
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
    categories_list.insert(0, {'label': 'Search everywhere [.....]',
                           'path' : plugin.url_for('start_search_in', category= 'everywhere', original_id = '0',
                                                   category_name = 'search everywhere')})

#    return plugin.finish(categories_list) #, sort_methods=['label_ignore_the']) #, sort_methods=['label']) #, view_mode=500))
    return categories_list


@plugin.cached_route('/movies_list/<category>/category_name/<category_name>/page/<page>')
#@plugin.route('/movies_list/<category>/category_name/<category_name>/page/<page>')
def show_movies(category, category_name, page):
    page = int(page)
    movies, next_page, original_id = get_movie_list(category, page)
    movies_list = [{'label':movie_title,
                    'thumbnail': thumbnail,
                    'info': get_movie_info(link),
                    'properties': {'fanart_image': thumbnail},
                    'path': plugin.url_for('show_files_list', movie=link,
                                           thumbnail_link = thumbnail, category_name = category_name)}
                   for thumbnail, movie_title, link in movies ]
    list_len = len(movies_list)
    if next_page:
        movies_list.insert(list_len, {'label': 'Next >>',
                                      'path': plugin.url_for('show_movies', category= category, page=str(page + 1),
                                      category_name = category_name)})
    if page > 0:
        movies_list.insert(-1, {'label': '<< Previous',
                                      'path': plugin.url_for('show_movies', category= category, page=str(page - 1),
                                      category_name = category_name)})


    movies_list.insert(0, {'label': 'Search in '+ urllib.unquote_plus(category_name).decode('utf-8') + ' [.....]',
                           'path' : plugin.url_for('start_search_in', category= category, original_id = original_id,
                                                   category_name = category_name)})
    xbmcplugin.setContent(_addon_id, 'movies')
    xbmc.executebuiltin('Container.SetViewMode(504)')
#    return plugin.finish(movies_list, view_mode=504) #, update_listing=True)
    return movies_list


@plugin.cached_route('/movies_list/<category>/category_name/<category_name>/page/<page>/original_id/<original_id>',
              name = 'start_search_in', options = {'start_search' : True, 'page' : '0'})
@plugin.cached_route('/movies_list/<category>/category_name/<category_name>/page/<page>/original_id/<original_id>/search_request/<search_request>')
def show_search_list_in(category, category_name, page, original_id, start_search = False, search_request = ''):
    page = int(page)
    if start_search and len(search_request) == 0:
        search_request = plugin.keyboard()
        if search_request is not None:
            movies, next_page = get_search_list(original_id, search_request, page)
        else:
            # return back window, in history
            return
#            xbmc.executebuiltin('PreviousWindow()')
    else:
        search_request = urllib.unquote_plus(search_request)
        movies, next_page = get_search_list(original_id, search_request, page)
    movies_list = [{'label':movie_title,
                    'thumbnail': thumbnail,
                    'info': get_movie_info(link),
                    'properties': {'fanart_image': thumbnail},
                    'path': plugin.url_for('show_files_list', movie=link,
                                           thumbnail_link = thumbnail, category_name = category_name)}
                   for thumbnail, movie_title, link in movies ]
    list_len = len(movies_list)
    if next_page:
        movies_list.insert(list_len, {'label': 'Next >>',
                                      'path': plugin.url_for('show_search_list_in', category= category, page=str(page + 1),
                                      category_name = category_name, original_id = original_id,
                                      search_request = urllib.quote_plus(search_request))})
    if page > 0:
        movies_list.insert(-1, {'label': '<< Previous',
                                      'path': plugin.url_for('show_search_list_in', category= category, page=str(page - 1),
                                      category_name = category_name, original_id = original_id,
                                      search_request = urllib.quote_plus(search_request))})


    movies_list.insert(0, {'label': 'New search in '+ urllib.unquote_plus(category_name).decode('utf-8') + ' [.....]',
                           'path' : plugin.url_for('start_search_in', category= category, original_id = original_id,
                                                   category_name = category_name)})
    xbmcplugin.setContent(_addon_id, 'movies')
#    return plugin.finish(movies_list, view_mode=504) #, update_listing=True)
    return movies_list


@plugin.route('/files/<movie>/thumbnail/<thumbnail_link>/category_name/<category_name>')
def show_files_list(movie, thumbnail_link, category_name):
    files = get_playlist(movie)
#    thumbnail = files[0]
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
#    xbmcplugin.setContent(_addon_id, 'movies')
#    return files_list
#    return plugin.finish(files_list, sort_methods=['label'], view_mode=504)


if __name__ == '__main__':
    plugin.run()
