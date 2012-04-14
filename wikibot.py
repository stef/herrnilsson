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

#SITE = "http://localhost/mediawiki/api.php"
SITE = "http://www.euwiki.org/w/api.php"
# dont forget to create a file containing USER, PASSWORD variables set
from password import USER,PASSWORD # to access the wiki - user must exist

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

def getMWdata(ref):
    dossier=fetch("http://parltrack.euwiki.org/dossier/%s?format=json" % ref)
    dossier=json.load(dossier)

    vars=[
        '|title=%s' % dossier['procedure']['title'],
        '|titlesafe=%s' % dossier['procedure']['title'].replace(' ',"+"),
        '|reference=%s' % dossier['procedure']['reference'],
        '|src=%s' % dossier['meta']['source'],
    ]
    if 'finalref' in dossier:
        vars.append('|finalref=%s' % dossier['finalref'])
    if 'dossier_of_the_committee' in dossier['procedure']:
        vars.append('|dossier_of_the_committee=%s' % dossier['procedure']['dossier_of_the_committee'])
    if 'legal_basis' in dossier['procedure']:
        vars.append('|legal_basis=%s' % ', '.join([sub for sub in dossier['procedure']['legal_basis']]))

    template="%s: [http://parltrack.euwiki.org/mep/%s#dossiers %s] [http://parltrack.euwiki.org/mep/%s %s]"
    vars.append("|responsibles=%s" % ', '.join(
        [template % (committee['committee'],
                     a['name'].replace(" ",'+'),
                     a['name'],
                     a['group'].replace(" ",'+'),
                     a['group'])
         for committee in dossier['committees']
         if committee['responsible']
         for a in committee['rapporteur']]))
    vars.append("|opinions=%s" % ', '.join(
        [template % (committee['committee'],
                     a['name'].replace(" ",'+'),
                     a['name'],
                     a['group'].replace(" ",'+'),
                     a['group'])
         for committee in dossier['committees']
         if not committee['responsible']
         for a in committee.get('rapporteur',[])]))

    return ('{{ptheader\n%s\n}}' % '\n'.join(vars), dossier)

def savePage(template, dossier):
    page = wikitools.Page(site,title=dossier['procedure']['reference'])
    print page
    res=page.edit(text="%s\nHerr Nilsson is happy" % template,
                  section="0",
                  bot=True,
                  skipmd5=True)
    print res
    #print page.getWikiText(force=True)

site = wikitools.wiki.Wiki(SITE)
site.login(USER, password=PASSWORD)
print site

if len(sys.argv)>1:
    # process 1st param as reference
    savePage(*getMWdata(sys.argv[1]))
else:
    # process stdin
    for line in sys.stdin.readlines():
        print 'updating line', line
        res=epre.match(line)
        if res:
            savePage(*getMWdata(line.strip()))
