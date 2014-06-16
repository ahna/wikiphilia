# -*- coding: utf-8 -*-
"""
scrapeWikipedia
Created on Wed Jun 11 17:24:41 2014

@author: ahna
"""


import urllib2
from bs4 import BeautifulSoup
#import pandas as pd

def getSite():
    site = wiki.Wiki("http://en.wikipedia.org/w/api.php") 
    site.login("ahnagirshick", "HMb58tfj") # login - required for read-restricted wikis
    return site

def grabWikiLinks(url):
    # get links to all  articles
    response = urllib2.urlopen(url)
    content = response.read()
    soup = BeautifulSoup(content, "xml")
    return soup
 
# function to convert wikitools.api.APIResult to a clean dict 
def saveAPIRequestResult(result):
    j = api.APIListResult(result['query']['pages'])[0]
    fields = api.APIListResult(result['query']['pages'][j])
    resultDict = {'pageid': -1, 'title': 'None', 'nimages': -1, 'nlinks':-1, 'nextlinks':-1, 'length': -1, 'ncategories':-1, 'revlastdate':-1}
 #   resultDict = {'pageid': -1, 'title': 'None', 'nimages': -1, 'nlinks':-1, 'nextlinks':-1, 'length': -1, 'counter': -1, 'new': -1, 'ncategories':-1}
    for f in fields:
        if f != 'ns':
            thisField = result['query']['pages'][j][f]
            if f == 'images':
                resultDict['nimages'] = len(thisField) # to do: remove some of the standard images
            elif f == 'pageid':
                resultDict['pageid'] = thisField
            elif f == 'links':
                resultDict['nlinks'] = len(thisField) # num internal links
            elif f == 'categories':
                resultDict['ncategories'] = len(thisField) # num internal links
            elif f == 'extlinks':
                resultDict['nextlinks'] = len(thisField) # num external links
            elif f == 'counters':
                resultDict['counter'] = thisField # If $wgDisableCounters is false, gives number of views. Otherwise, gives empty attribute.
            elif f == 'new':
                resultDict['new'] = thisField # whether the page has only one revisio
            elif f == 'length':
                resultDict['length'] = thisField
            elif f == 'revisions':
                resultDict['revlastdate'] = thisField[0]['timestamp']
            elif f == 'title':
                resultDict['title'] = thisField.encode('utf-8')
    return resultDict

# method 1 uses the wikitools api (slow)
# convert wikipage title to dict with meta info
def getWikiPageMeta1(title,site=getSite()):
    # create the request object & query the API
    params = {'action':'query', 'titles':title, 'prop':'info|images|links|extlinks|categories|revisions', 'rvprop':'timestamp'}   # to do, see if i can get more info in the query  
    request = api.APIRequest(site, params)
    result = saveAPIRequestResult(request.query())
    return result
    
# method 2 uses the wikipedia api (faster)
# convert wikipage title to dict with meta info
def getWikiPageMeta2(title,site=getSite()):
    resultDict = {'pageid': 'NA', 'title': 'NA', 'nimages': 'NA', 'nlinks':'NA', 'nrefs':'NA', 'length': 'NA','url':'NA'}
    for r in resultDict:
        if r == 'nimages':
            resultDict['nimages'] = len(thisField) # to do: remove some of the standard images
        elif r == 'pageid':
            resultDict['pageid'] = thisField
        elif r == 'nlinks':
            resultDict['nlinks'] = len(thisField) # num internal links
        elif r == 'nrefs':
            resultDict['ncategories'] = len(thisField) # num internal links
        elif r == 'extlinks':
            resultDict['nextlinks'] = len(thisField) # num external links
        elif r == 'counters':
            resultDict['counter'] = thisField # If $wgDisableCounters is false, gives number of views. Otherwise, gives empty attribute.
        elif r == 'new':
            resultDict['new'] = thisField # whether the page has only one revisio
        elif r == 'title':
            resultDict['title'] = thisField.encode('utf-8')
    return resultDict    

# for each link, get some meta data and put in the table
def getWikiPagesMeta(links,DF,csvfilename,iStart=0,flags='NA',method=2):
    import pandas as pd    
    if iStart > 0:
        DF = pd.DataFrame().from_csv(csvfilename) # load existing dataframe from file and append to it
    
    if method == 1: # method 1 uses the wikitools api (slow)
        from wikitools import api
        from wikitools import wiki
        site = getSite()
    elif method == 2: # method 2 uses the wikipedia api (faster)
        import wikipedia
        
    for i in range(iStart,len(links)):
        l = links[i]
        print(str(i) +"/" + str(len(links)) + ": " + l.text)

        title = l.text.replace('"','')
        if method == 1: # ethod 1 uses the wikitools api (slow)
            new_row = getWikiPageMeta1(title,site)
        elif method == 2:
            new_row = getWikiPageMeta2(title)
            
        new_row['flags'] = flags
        if flags == 'NA':
            new_row['flagged'] = False
        else:
            new_row['flagged'] = True
        # write and save to file
        DF = DF.append(new_row,ignore_index=True)
        DF.to_csv(csvfilename)
        i += 1
    return DF    
