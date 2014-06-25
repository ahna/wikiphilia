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
from scrapeWikipedia import wikiScraper
import pickle

def main():

#    conn, cur = scrapeWikipedia.openDB()
    


    flaggedcsvfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/flagged.csv'
    linksfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/flagged.links.p'
    flags = {"Too few wikilinks":1, "In need of updating":2, "May contain original research":3, "Stubs":4, "Need factual verification":5,"Need cleanup after translation":6, "Need copy editing":7, "Introduction cleanup":8,"Missing lead section":9,"To be expanded":10}
#    urls = {"https://en.wikipedia.org/wiki/Category:Articles_with_too_few_wikilinks_from_June_2014": flags["Too few wikilinks"],\
#    "https://en.wikipedia.org/w/index.php?title=Category:Articles_with_too_few_wikilinks_from_June_2014&pagefrom=LGBT+culture+in+Boston#mw-pages":flags["Too few wikilinks"],\
#    "https://en.wikipedia.org/wiki/Category:Wikipedia_articles_needing_cleanup_after_translation":flags["Need cleanup after translation"],\
#    "https://en.wikipedia.org/w/index.php?title=Category:Wikipedia_articles_needing_cleanup_after_translation&pagefrom=Shitik%0AShitik#mw-pages":flags["Need cleanup after translation"],\
#    "https://en.wikipedia.org/wiki/Category:Wikipedia_articles_needing_copy_edit_from_June_2014":flags["Need copy editing"],\
#    "https://en.wikipedia.org/w/index.php?title=Category:Wikipedia_articles_needing_copy_edit_from_June_2014&pagefrom=Republic+Of+Korea+Presidential+Unit+Citation%0ARepublic+of+Korea+Presidential+Unit+Citation#mw-pages":flags["Need copy editing"],\
#    "https://en.wikipedia.org/wiki/Category:Wikipedia_introduction_cleanup_from_June_2014":flags["Introduction cleanup"],\
#    "https://en.wikipedia.org/w/index.php?title=Category:Wikipedia_introduction_cleanup_from_June_2014&pagefrom=Mountain+Industrial+Boulevard#mw-pages":flags["Introduction cleanup"],\
#    "https://en.wikipedia.org/wiki/Category:Pages_missing_lead_section":flags["Missing lead section"],\
#    "https://en.wikipedia.org/wiki/Category:Articles_to_be_expanded_from_June_2014":flags["To be expanded"]} # Use and get more than just first 200 (over 1000 pages!)

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
               #    "https://en.wikipedia.org/wiki/Category:Wikipedia_articles_in_need_of_updating_from_June_2014",\ # 2 pages do not use
#            "https://en.wikipedia.org/wiki/Category:Articles_that_may_contain_original_research_from_June_2014",\ # do not use
#            "https://en.wikipedia.org/wiki/Category:Stubs",\
#            "https://en.wikipedia.org/wiki/Category:Wikipedia_articles_needing_factual_verification_from_June_2014",\ # do not use unless i can get # of footnotes, 2 pages
# create a data frame
    #flaggedDF = pd.DataFrame(columns=['length','nextlinks','nimages','nlinks','pageid','title','ncategories','revlastdate','flags','flagged']) 
    #flaggedDF = pd.DataFrame(columns=['meanWordLength','meanSentLength', 'medianSentLength',  'medianWordLength', \
    # 'nChars','nImages', 'nLinks','nSections', 'nSents','nRefs', 'nWordsSummary','pageId',\
     #'revisionId','title','url','flagged','flags'])
         
    
        
    ################################################################
    # create a Wiki object
    ws = wikiScraper()
    allLinks = []
    i = 0
    for url,flag in urls.iteritems():
        print url, flag
#        soup = scrapeWikipedia.grabWikiLinksFromURL(url)
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
#        flaggedDF = scrapeWikipedia.getWikiPagesMeta(links,flaggedDF,flaggedcsvfilename,flags=flag,iStart=0)
                ws.getWikiPagesMeta(links=links,iStart=iStart,flags=flag,tablename='training2')
                allLinks = allLinks + links
        i += 1
    
    ################################################################
    #flaggedDF['score'] = 0 # indicate that all these articles were not featured
    #flaggedDF['flagged'] = True # indicate that all these articles were flagged

    # save data frame to csv file
    #flaggedDF.to_csv(flaggedcsvfilename)
    #flaggedDF = pd.DataFrame().from_csv(flaggedcsvfilename) # use this line if you ever need to read from file
    
    # save link list
    with open(linksfilename, 'wb') as f:
        pickle.dump(str(allLinks),f)

    ################################################################
    # write to SQL database
    #flaggedDF.to_sql('wikimeta', conn, flavor='mysql', if_exists='append')


if __name__ == '__main__': main()
