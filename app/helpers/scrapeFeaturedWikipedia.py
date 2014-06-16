# -*- coding: utf-8 -*-

"""
Grab list of featured articles from Wikipedia and saves to a CSV file

Created on Tue Jun 10 10:26:15 2014
@author: ahna
"""

################################################################
# imports
from bs4 import BeautifulSoup
import pandas as pd
import pickle
import pymysql
import scrapeWikipedia
#scrapeWikipedia = reload(scrapeWikipedia)


def main():

    conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='wikiscore123', db='wikimeta')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    #cur.execute(<SQL statement>)

    csvfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/data/featured.csv'
    linksfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/data/featured.links.p'
    url = "https://en.wikipedia.org/wiki/Wikipedia:Featured_articles"
    # create a data frame
    featuredDF = pd.DataFrame(columns=['length','nextlinks','nimages','nlinks','pageid','title','ncategories','revlastdate']) 

    ################################################################
    # create a Wiki object
    soup = scrapeWikipedia.grabWikiLinks(url)
    td = soup.findAll('td')[4] # the 5th table on page has all the links to the featured articles
    soup2 = BeautifulSoup(str(td),'xml')
    links = soup2.find_all("a")
    
    # save link list
    pickle.dump(str(links),open(linksfilename, 'wb'))

    # save wikipedia featured page meta data
    featuredDF = scrapeWikipedia.getWikiPagesMeta(links,featuredDF,csvfilename)
    
    ################################################################
    featuredDF['featured'] = True # indicate that all these articles were featured
    featuredDF['flagged'] = False # indicate that all these articles were not flagged
    featuredDF['flags'] = 'NA' # indicate that there is no flag info
    
    # save data frame to csv file

    featuredDF.to_csv(csvfilename)
    #featuredDF = pd.DataFrame().from_csv(csvfilename) # use this line if you ever need to read from file

    ################################################################
    # write to SQL database


if __name__ == '__main__': main()
