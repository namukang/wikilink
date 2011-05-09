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

query = "Albert Einstein"

site = wiki.Wiki()
# Do not sleep if wiki server is lagging
site.setMaxlag(-1)
wikipage = page.Page(site, query)

# Find actual article subject chosen from query
# e.g. the query "meow" returns the article for "Cat communication"
info = str(wikipage.setPageInfo()).split()
# Subject may have any number of characters between its words
# e.g. Albert&nbsp;Einstein in wikitext
subject = ('.*?'.join(info[1:-2])).strip("'")
# Subject may only have one space (or none) in between its words
# e.g. AlbertEinstein in plaindes
subjectsingle = ('(\s)?'.join(info[1:-2])).strip("'")
# Subject as it will be read
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

# Try to keep only the first sentence of wikitext
pat = r"(?i)\s.*?'''%s.*?\.\s" % subject
match = re.search(pat, wikitext)
if match:
    wikides = match.group()
else:
    wikides = wikitext

params = {'action':'parse', 'text': wikides}
request = api.APIRequest(site, params)
htmldes = str(request.query())
plaindes = strip_tags(htmldes)

# Only keep the first sentence
pat = r"(?i)%s\s.*?\." % subjectsingle
print pat
match = re.search(pat, plaindes)
if match:
    shortdes = match.group()
else:
    shortdes = plaindes
    
print "<b>" + plainsubject + "</b>: " + shortdes + "<br />"


print """
</body>
</html>
"""
