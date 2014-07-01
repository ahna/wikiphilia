# -*- coding: utf-8 -*-
"""
scrapeFlaggedWikipedia.py
Grab list of flagged articles from Wikipedia, scrape features, save to Database
Created on Wed Jun 11 17:23:45 2014

@author: ahna
"""

# -*- coding: utf-8 -*-

# imports
from bs4 import BeautifulSoup
from scrapeWikipedia import wikiScraper
import pickle

###############################################################
def main():

    linksfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/flagged.links.p'
    flags = {"Too few wikilinks":1, "In need of updating":2, "May contain original research":3, "Stubs":4, "Need factual verification":5,"Need cleanup after translation":6, "Need copy editing":7, "Introduction cleanup":8,"Missing lead section":9,"To be expanded":10}
    urls = {"https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=2004+In+Road+Cycling%0A2004+in+men%27s+road+cycling#mw-pages": flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=Andre%0AList+of+awards+received+by+Andr%C3%A9#mw-pages": flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=Chronological+list+of+Australian+classical+composers#mw-pages" : flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=Engschrift#mw-pages" : flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=Helen+Day+Art+Center#mw-pages" : flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=Kenya+County+Representative+elections+in+Kiambu%2C+2013#mw-pages" : flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=List+of+pitch+and+putt+national+associations#mw-pages" : flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=Minuto#mw-pages" : flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=Peace+Parade+Uk%0APeace+Parade+UK#mw-pages" : flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=Schools+Curriculum+%28India%29#mw-pages" : flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=The+Arts+Of+Upstate+New+York%0AArts+in+Upstate+New+York#mw-pages" : flags["Missing lead section"],\
    "https://en.wikipedia.org/w/index.php?title=Category:Pages_missing_lead_section&pagefrom=Whelan%27s+%28Music+Venue%29%0AWhelan%27s+%28music+venue%29#mw-pages" : flags["Missing lead section"]}

    ################################################################
    # create a Wiki object
    ws = wikiScraper()
    allLinks = []
    i = 0
    for url,flag in urls.iteritems():
        print url, flag
        if i >= 5:
            if i == 5:
                iStart = 0
            else:
                iStart = 0
            soup = ws.grabWikiLinksFromUrl(url)
            td = soup.findAll('td')
            idx = [len(td)-3,len(td)-2,len(td)-1] # the last three columns on page
            links = []
            for j in idx:
                soup2 = BeautifulSoup(str(td[j]),'xml')
                links = links + soup2.find_all("a")
                ws.getWikiPagesMeta(links=links,iStart=iStart,flags=flag,tablename='training2')
                allLinks = allLinks + links
        i += 1
        
    # save link list
    with open(linksfilename, 'wb') as f:
        pickle.dump(str(allLinks),f)


if __name__ == '__main__': main()
