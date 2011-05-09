#!/usr/bin/python2.6

from wikitools import wiki
from wikitools import api
from wikitools import page
import re
import cgi
import sys
import random

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

def get_first_image(html_des):
    """Returns HTML for the first pertinent image contained in the Wikipedia HTML html_des"""
    pat = r"(thumbinner|biography|vcard).*?(<img.*?/>)"
    match = re.search(pat, html_des)
    if match:
        return match.group(2)
    else:
        return None

def error_quit(msg=""):
    """Quits the application with msg"""
    print "Error: " + msg
    print "Please <a href='http://www.dskang.com/wikilink'>try again</a>.</p>"
    sys.exit(0)

def get_html_para(html_des):
    """Extracts the first paragraph of the article in Wikipedia HTML html_des"""
    split_html = html_des.split("\\n")
    pat = r"(?i)<p>.*?<b>%s.*?</b>.*?</p>" % subject
    found = False
    for html_line in split_html:
        match = re.search(pat, html_line)
        if match:
            html_para = match.group()
            found = True
            break
    if not found:
        msg = "Wikilink bot cannot parse article for '%s'.<br />" % query
        error_quit(msg)
    return html_para

def invalid_article(html_des):
    """Return True if the article in Wikipedia HTML html_des is not an actual article"""
    return "may refer to" in html_des

def wiki_to_html(site, wikitext):
    """Translate wikitext to HTML"""
    params = {'action':'parse', 'text': wikitext}
    request = api.APIRequest(site, params)
    html_des = str(request.query())
    return html_des
    
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

# Take user input as query word
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
# Subject may have any number of characters between its words
# e.g. Albert&nbsp;Einstein in wikitext
subject = ('.*?'.join(info[1:-2])).strip("'")
# Subject as it will be read
plainsubject = (' '.join(info[1:-2])).strip("'")

print "<p><b>" + plainsubject + "</b>: "

# Only get the first section of article
wikipage.setSection(number=0)
try:
    wikitext = wikipage.getWikiText()
except:
    msg = "No Wikipedia article can be found for '%s'<br />" % query
    error_quit(msg)

# Translate wikitext to HTML
html_des = wiki_to_html(site, wikitext)

# Check validity of article
if invalid_article(html_des):
    msg = "The term '%s' is too ambiguous.<br />" % query
    error_quit(msg)

# Get first descriptive paragraph from HTML
html_para = get_html_para(html_des)
# Strip out the HTML    
plain_des = strip_tags(html_para)
print plain_des + "</p>"

# Print an image from the wikipedia article if one exists
image = get_first_image(html_des)
if image:
    print image

print """
</body>
</html>
"""
