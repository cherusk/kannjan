#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

THEME = "Responsive-Pelican"

AUTHOR = u'Matthias Tafelmeier'
SITENAME = "cherusk Tech Blog"
SITE_LOGO = "/meta/cherusk.png"
SITEURL = 'http://localhost:8000/'

PATH = 'content'

DEFAULT_LANG = u'en'

# Blogroll
LINKS = (('github', 'http://github.com/cherusk'),)

STATIC_PATHS = ['meta']

PLUGIN_PATHS = ['/home/matthias/Projects/pelican-plugins/']
PLUGINS = ['pelican-toc']
TOC = {
        'TOC_HEADERS'       : '^h[1-7]', # What headers should be included in
       # Expected format is a regular expression
        'TOC_RUN'           : 'true',    # Default value for toc generation,
        # if it does not evaluate
        # to 'true' no toc will be generated
        'TOC_INCLUDE_TITLE': 'false',     # If 'true' include title in toc
    }

MD_EXTENSIONS = ['codehilite(noclasses=True, pygments_style=native)', 'extra']

DISPLAY_PAGES_ON_MENU = True
DISPLAY_CATEGORIES_ON_MENU = True
MENUITEMS = [('Contact', SITEURL + '/pages/contact.html')]

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
