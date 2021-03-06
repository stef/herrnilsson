#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    This file is part of parltrack

#    parltrack is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    parltrack is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with parltrack  If not, see <http://www.gnu.org/licenses/>.

# (C) 2012 by Stefan Marsiske, <stefan.marsiske@gmail.com>

# dont forget to create a file containing USER, PASSWORD variables set
from config import SITE,USER,PASSWORD, PREFIX # to access the wiki - user must exist

import urllib2, time, sys, json, wikitools, re

epre=re.compile(r'([0-9]{4}/[0-9]{4}\([A-Z]{3}\))|([A-Z]{3}/[0-9]{4}/[0-9]{4})')

def fetch(url, retries=5, ignore=[], params=None):
    try:
        f=urllib2.urlopen(url, params)
    except (urllib2.HTTPError, urllib2.URLError), e:
        if hasattr(e, 'code') and e.code>=400 and e.code not in [504, 502]+ignore:
            print >>sys.stderr, "[!] %d %s" % (e.code, url)
            raise
        if retries>0:
            timeout=4*(6-retries)
            print >>sys.stderr, "[!] failed: %d %s, sleeping %ss" % (e.code, url, timeout)
            time.sleep(timeout)
            f=fetch(url,retries-1, ignore=ignore)
        else:
            raise
    return f

from jinja2 import Environment, Template, FileSystemLoader
import os
def getdata(ref):
    url="http://parltrack.euwiki.org/dossier/%s?format=json" % ref
    print url
    dossier=json.load(fetch(url))
    return getMWdata(dossier)

def getMWdata(dossier):
    env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
    t = env.get_template('data.txt')
    return (t.render(dossier=dossier), dossier)

def savePage(template, dossier):
    site = wikitools.wiki.Wiki(SITE)
    site.login(USER, password=PASSWORD)
    print site

    title="%s%s" % (PREFIX, dossier['procedure']['title'])
    print 'saving', title
    page = wikitools.Page(site,title=title)
    #print page
    #print template
    res=page.edit(text="%s" % template,
                  section="0",
                  bot=True,
                  skipmd5=True)
    print res
    #print page.getWikiText(force=True)

if len(sys.argv)>1:
    # process 1st param as reference
    res=epre.match(sys.argv[1])
    if res:
        savePage(*getdata(sys.argv[1]))
    else:
        raw=fetch('http://parltrack.euwiki.org/notification/%s?format=json' % sys.argv[1] )
        for doc in json.load(raw)['dossiers']:
            print doc['procedure']['reference']
            savePage(*getMWdata(doc))
else:
    # process stdin
    for line in sys.stdin.readlines():
        print 'updating line', line
        res=epre.match(line)
        if res:
            savePage(*getdata(line.strip()))
