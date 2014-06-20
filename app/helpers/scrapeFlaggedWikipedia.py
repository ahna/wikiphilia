# -*- coding: utf-8 -*-
"""
scrapeFlaggedWikipedia.py
Grab list of flagged articles from Wikipedia and saves to a CSV file
Created on Wed Jun 11 17:23:45 2014

@author: ahna
"""

# -*- coding: utf-8 -*-

# imports
from bs4 import BeautifulSoup
import pandas as pd
import scrapeWikipedia
import pickle

def main():

    conn, cur = scrapeWikipedia.openDB()


    flaggedcsvfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/flagged.csv'
    linksfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/flagged.links.p'
    urls = ["https://en.wikipedia.org/wiki/Category:Articles_with_too_few_wikilinks_from_June_2014",\
            "https://en.wikipedia.org/wiki/Category:Wikipedia_articles_in_need_of_updating_from_June_2014",\
            "https://en.wikipedia.org/wiki/Category:Articles_that_may_contain_original_research_from_June_2014",\
            "https://en.wikipedia.org/wiki/Category:Stubs",\
            "https://en.wikipedia.org/wiki/Category:Wikipedia_articles_needing_factual_verification_from_June_2014",\
            "https://en.wikipedia.org/wiki/Category:Wikipedia_articles_needing_cleanup_after_translation",\
            "https://en.wikipedia.org/wiki/Category:Wikipedia_articles_needing_copy_edit_from_June_2014",\
            "https://en.wikipedia.org/wiki/Category:Wikipedia_introduction_cleanup_from_June_2014"]
    # create a data frame
    #flaggedDF = pd.DataFrame(columns=['length','nextlinks','nimages','nlinks','pageid','title','ncategories','revlastdate','flags','flagged']) 
    flaggedDF = pd.DataFrame(columns=['meanWordLength','meanSentLength', 'medianSentLength',  'medianWordLength', \
     'nChars','nImages', 'nLinks','nSections', 'nSents','nRefs', 'nWordsSummary','pageId',\
     'revisionId','title','url','flagged','flags'])
         
    #flags = {"Too few wikilinks":1, "In need of updating":2, "May contain original research":3, "Stubs":4, "Need factual verification":5, "Need cleanup after translation":6, "Need copy editing":7, "Introduction cleanup":8}    
    
        
    ################################################################
    # create a Wiki object
    allLinks = []
    for i in range(len(urls)-1,len(urls)):
        url = urls[i]
        print url
        soup = scrapeWikipedia.grabWikiLinksFromURL(url)
        td = soup.findAll('td')
        idx = [len(td)-3,len(td)-2,len(td)-1] # the last three columns on page
        links = []
        for j in idx:
            soup2 = BeautifulSoup(str(td[j]),'xml')
            links = links + soup2.find_all("a")
        flaggedDF = scrapeWikipedia.getWikiPagesMeta(links,flaggedDF,flaggedcsvfilename,flags=i,iStart=0)
        allLinks = allLinks + links
        i += 1
    
    ################################################################
    flaggedDF['score'] = 0 # indicate that all these articles were not featured
    flaggedDF['flagged'] = True # indicate that all these articles were flagged

    # save data frame to csv file
    flaggedDF.to_csv(flaggedcsvfilename)
    #flaggedDF = pd.DataFrame().from_csv(flaggedcsvfilename) # use this line if you ever need to read from file
    
    # save link list
    pickle.dump(str(allLinks),open(linksfilename, 'wb'))
    #test= pickle.load(open(linksfilename, 'rb'))

    ################################################################
    # write to SQL database
    #flaggedDF.to_sql('wikimeta', conn, flavor='mysql', if_exists='append')


if __name__ == '__main__': main()
