#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

THEME = "Responsive-Pelican"

AUTHOR = u'Matthias Tafelmeier'
SITENAME = "cherusk Tech Blog"
SITE_LOGO = "/meta/cherusk.png"
SITEURL = ''

PATH = 'content'

DEFAULT_LANG = u'en'

# Blogroll
LINKS = (('github', 'http://github.com/cherusk'),)

STATIC_PATHS = ['meta']

DISPLAY_PAGES_ON_MENU = True
DISPLAY_CATEGORIES_ON_MENU = True
MENUITEMS = [('About', SITEURL + '/pages/about.html')]

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
