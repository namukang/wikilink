#!/usr/bin/python

from wikitools import wiki
from wikitools import api
from wikitools import page
import re

# Strip HTML from strings in Python
from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

query = "Princeton University"

site = wiki.Wiki()
# Do not sleep if wiki server is lagging
site.setMaxlag(-1)
wikipage = page.Page(site, query)

# Find actual article subject chosen from query
info = str(wikipage.setPageInfo()).split()
subject = ('.*?'.join(info[1:-2])).strip("'")

# Only get the first section of article
wikipage.setSection(number=0)
try:
    wikitext = wikipage.getWikiText()
except page.NoPage:
    print "No Wikipedia article can be found for '%s'" % query
    import sys
    sys.exit(0)

# Find first sentence of description
pat = r"(?i)\s.*?'''%s.*?\.\s" % subject
match = re.search(pat, wikitext)
if match:
    wikides = match.group()
else:
    wikides = wikitext


params = {'action':'parse', 'text': wikides}
request = api.APIRequest(site, params)
result = str(request.query())

# Only keep the pertinent HTML
pat = r"(?i)<p>.*?<b>%s</b>.*?</p>" % subject
match = re.search(pat, result)
if match:
    htmldes = match.group()
else:
    htmldes = result
    
plaindes = strip_tags(htmldes)
print plaindes
