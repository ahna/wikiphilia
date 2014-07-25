# -*- coding: utf-8 -*-

"""
scrapeFeaturedWikipedia.py
Grab list of featured articles from Wikipedia, scrape features, and save to a database

Created on Tue Jun 10 10:26:15 2014
@author: ahna
"""

################################################################
# imports
from bs4 import BeautifulSoup
import pickle
from scrapeWikipedia import wikiScraper


def main():

    linksfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/featured.links.p'
    url = "https://en.wikipedia.org/wiki/Wikipedia:Featured_articles"
         
    ################################################################
    # create a Wiki object
    ws = wikiScraper()
    soup = ws.grabWikiLinksFromUrl(url)
    td = soup.findAll('td')[4] # the 5th table on page has all the links to the featured articles
    soup2 = BeautifulSoup(str(td),'xml')
    links = soup2.find_all("a")
    
    # save link list
    with open(linksfilename, 'wb') as f:
        pickle.dump(str(links),f)

    # save wikipedia featured page meta data
    ws.getWikiPagesMeta(links=links,iStart=0,tablename='training2',featured=True)        

if __name__ == '__main__': main()
    