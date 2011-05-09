#!/usr/bin/python2.6

from wikitools import wiki
from wikitools import api
from wikitools import page
import re
import cgi

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

# Take user input as query word
print "Content-type: text/html\n\n"
print """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
  <title>Wikilink</title>
</head>
<body>
"""

form = cgi.FieldStorage()
query = str(form.getfirst("query", "Princeton University"))
print "<h3>Query: '%s'</h3>" % query

site = wiki.Wiki()
# Do not sleep if wiki server is lagging
site.setMaxlag(-1)
wikipage = page.Page(site, query)

# Find actual article subject chosen from query
# e.g. the query "meow" returns the article for "Cat communication"
info = str(wikipage.setPageInfo()).split()
subject = ('.*?'.join(info[1:-2])).strip("'")
plainsubject = (' '.join(info[1:-2])).strip("'")

# Only get the first section of article
wikipage.setSection(number=0)
try:
    wikitext = wikipage.getWikiText()
except page.NoPage:
    print "<p> No Wikipedia article can be found for '%s'<br />" % query
    print "Please <a href='http://www.dskang.com/wikilink'>try again</a>.<br /></p>"
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
print "<b>" + plainsubject + "</b>: " + plaindes + "<br />"


print """
</body>
</html>
"""
