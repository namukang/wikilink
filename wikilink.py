#!/usr/bin/python2.6

from wikitools import wiki
from wikitools import api
from wikitools import page
import re
import cgi
import sys

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
    print "<br /><span class='error'>"
    print "Error: " + msg
    print "</span>"
    print "Please <a href='http://www.dskang.com/wikilink'>try again</a>.</p>"
    sys.exit(0)

def get_html_para(html_des):
    """Extracts the first paragraph of the article in Wikipedia HTML html_des"""
    split_html = html_des.split("\\n")
    pat = r"(?i)<p>.*?<b>.*?</b>.*?</p>"
    found = False
    for html_line in split_html:
        match = re.search(pat, html_line)
        if match:
            html_para = match.group()
            found = True
            break
    if not found:
        msg = "The article for '%s' cannot be parsed due to irregular formatting.<br />" % query
        error_quit(msg)
    return html_para

def invalid_article(html_des):
    """Return True if the article in Wikipedia HTML html_des is not an actual article"""
    return "may refer to" in html_des or "may mean" in html_des

def wiki_to_html(site, wikitext):
    """Translate wikitext to HTML"""
    params = {'action':'parse', 'text': wikitext}
    request = api.APIRequest(site, params)
    html_des = str(request.query())
    return html_des

def get_random_links(wikipage, count):
    import random
    links = []
    all_links = wikipage.getLinks()
    size = len(all_links)
    for i in range(count):
        rand = random.randint(0, size-1)
        links.append(all_links[rand])
        del(all_links[rand])
        size -= 1
    return links

def record(query):
    import datetime
    now = datetime.datetime.now()
    time = now.strftime("%Y-%m-%d %H:%M:%S")

    import os
    ipaddress = cgi.escape(os.environ["REMOTE_ADDR"])
    
    f = open('history.txt', 'a')
    entry = "%s | %-15s | %s\n" % (time, ipaddress, query)
    f.write(entry)
    f.close()
    
def main(query):
    print "Content-type: text/html; charset=utf-8\n\n"
    print """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
  <title>WikiLink | %s</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
""" % query

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
    subject_plain = (' '.join(info[1:-2])).strip("'")

    print "<div id='info'><p><b>" + subject_plain + "</b>: "

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
    print plain_des + "</p></div>"

    # Print an image from the wikipedia article if one exists
    image = get_first_image(html_des)
    if image:
        print image

    # Present random links from article
    links = get_random_links(wikipage, 2)
    print "<h3>Links from '%s':</h3>" % subject_plain
    print "<form action='wikilink.py' method='get' enctype='multipart/form-data'>"
    for link in links:
        print "<input type='submit' name='query' value='%s'>" % link
    print "</form>"

    print "</body></html>"

if __name__ == "__main__":
    if len(sys.argv) == 2:
        query = str(sys.argv[1])
    else:
        # Take user input as query word
        form = cgi.FieldStorage()
        # Look up "None" if there is no input :)
        query = str(form.getfirst("query"))
    record(query)
    main(query)
