# -*- coding: utf-8 -*-

"""
scrapeFeaturedWikipedia.py
Grab list of featured articles from Wikipedia and saves to a CSV file

Created on Tue Jun 10 10:26:15 2014
@author: ahna
"""

################################################################
# imports
from bs4 import BeautifulSoup
import pandas as pd
import pickle
#import pymysql
from scrapeWikipedia import wikiScraper


def main():

#    conn, cur = scrapeWikipedia.openDB()
    
    csvfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/featured.csv'
    linksfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/featured.links.p'
    url = "https://en.wikipedia.org/wiki/Wikipedia:Featured_articles"
    # create a data frame
#    featuredDF = pd.DataFrame(columns=['meanWordLength','meanSentLength', 'medianSentLength',  'medianWordLength', \
#     'nChars','nImages', 'nLinks','nSections', 'nSents','nRefs', 'nWordsSummary','pageId',\
#     'revisionId','title','url','score','flagged','flags'])
     
         
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
    #featuredDF = scrapeWikipedia.getWikiPagesMeta(links,csvfilename,iStart=0,tablename='training')
    ws.getWikiPagesMeta(links=links,iStart=0,tablename='training2')        
        
    ################################################################
    #featuredDF['score'] = True # indicate that all these articles were featured
    #featuredDF['flagged'] = False # indicate that all these articles were not flagged
    #featuredDF['flags'] = 'NA' # indicate that there is no flag info
    
    # save data frame to csv file
    #featuredDF.to_csv(csvfilename)

    ################################################################
    # write to SQL database
#    iUse = ['meanWordLength','meanSentLength', 'nChars','nImages', 'nLinks','nSections', 'nSents',\
#    'nRefs', 'nWordsSummary','pageId','revisionId','title','url','score','flagged','flags']
#    import numpy as np
#    type_dict = {np.float64:float, np.int64:int, np.bool_:bool, str:str, float:float}
#    for i in range(0,len(featuredDF)):
#        print i
#        
#        row = list( featuredDF.ix[i,iUse])
#        # convert types
#        for j in range(len(row)):
#            row[j] = type_dict[type(row[j])](row[j])
#            if row[j] == 'NA' or (is_numlike(row[j]) and isnan(row[j])):
#                row[j] = None        
#         
#        # insert row into database
#        cur.execute('''INSERT INTO training (meanWordLength,meanSentLength, \
#        nChars,nImages, nLinks,nSections, nSents,nRefs, nWordsSummary,pageId,\
#        revisionId,title,url,score,flagged,flags) \
#        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', row)
#        conn.commit()     
#             
#    cur.close()
#    conn.commit()
#    conn.close()


if __name__ == '__main__': main():
    
# UPDATE training2 SET score = 1 WHERE score IS NULL;
