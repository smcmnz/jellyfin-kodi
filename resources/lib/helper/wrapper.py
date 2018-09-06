# -*- coding: utf-8 -*-

#################################################################################################

import logging

import xbmcgui

from . import _, LibraryException
from utils import should_stop

#################################################################################################

LOG = logging.getLogger("EMBY."+__name__)

#################################################################################################

def progress(message=None):

    ''' Will start and close the progress dialog.
    '''
    def decorator(func):
        def wrapper(self, item=None, *args, **kwargs):

            dialog = xbmcgui.DialogProgressBG()

            if item and type(item) == dict:

                dialog.create(_('addon_name'), "%s %s" % (_('gathering'), item['Name']))
                LOG.info("Processing %s: %s", item['Name'], item['Id'])
            else:
                dialog.create(_('addon_name'), message)
                LOG.info("Processing %s", message)

            if item:
                args = (item,) + args

            kwargs['dialog'] = dialog
            result = func(self, *args, **kwargs)
            dialog.close()

            return result

        return wrapper
    return decorator


def catch(errors=(Exception,)):

    ''' Wrapper to catch exceptions and return using catch
    '''
    def decorator(func):
        def wrapper(*args, **kwargs):

            try:
                return func(*args, **kwargs)
            except errors as error:
                LOG.exception(error)

                raise Exception("Caught exception")

        return wrapper
    return decorator

def stop(default=None):

    ''' Wrapper to catch exceptions and return using catch
    '''
    def decorator(func):
        def wrapper(*args, **kwargs):

            try:
                if should_stop():
                    raise Exception

            except Exception as error:

                if default is not None:
                    return default

                raise LibraryException("StopCalled")

            return func(*args, **kwargs)

        return wrapper
    return decorator

def emby_item():

    ''' Wrapper to retrieve the emby_db item.
    '''
    def decorator(func):
        def wrapper(self, item, *args, **kwargs):
            e_item = self.emby_db.get_item_by_id(item['Id'] if type(item) == dict else item)

            return func(self, item, e_item=e_item, *args, **kwargs)

        return wrapper
    return decorator

def library_check():

    ''' Wrapper to retrieve the library
    '''
    def decorator(func):
        def wrapper(self, item, *args, **kwargs):
            from database import get_sync

            sync = get_sync()

            if kwargs.get('library') is None:

                if 'e_item' in kwargs:
                    try:
                        view_id = kwargs['e_item'][7]
                        view_name = self.emby_db.get_view_name(view_id)
                        view = {'Name': view_name, 'Id': view_id}
                    except Exception:
                        view = None

                if view is None:
                    ancestors = self.server['api'].get_ancestors(item['Id'])

                    if not ancestors:

                        return

                    for ancestor in ancestors:
                        if ancestor['Type'] == 'CollectionFolder':

                            view = self.emby_db.get_view_name(ancestor['Id'])
                            view = {'Id': None, 'Name': None} if view is None else {'Name': ancestor['Name'], 'Id': ancestor['Id']}

                            break

                    if view['Id'] not in sync['Whitelist']:
                        LOG.info("Library %s is not synced. Skip update.", view['Id'])

                        return

                kwargs['library'] = view

            return func(self, item, *args, **kwargs)

        return wrapper
    return decorator
