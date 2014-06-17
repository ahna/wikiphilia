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
    from wikitools import wiki
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
    from wikitools import api
    from wikitools import wiki
    # create the request object & query the API
    params = {'action':'query', 'titles':title, 'prop':'info|images|links|extlinks|categories|revisions', 'rvprop':'timestamp'}   # to do, see if i can get more info in the query  
    request = api.APIRequest(site, params)
    result = saveAPIRequestResult(request.query())
    return result
    
    
# method 2 uses the wikipedia api (faster)
# convert wikipage title to dict with meta info
def getWikiPageMeta2(title):
    from numpy import mean
    from numpy import median
    import wikipedia
    wp = wikipedia.page(title,auto_suggest=1)
    results = {'meanWordLength':'NA','meanSentLen':'NA', 'medianSentLen':'NA',  'medianWordLength':'NA', \
     'nChars':'NA','nImages': 'NA', 'nLinks':'NA','nSections':'NA', 'nSents':'NA','nRefs':'NA', 'nWordsSummary':'NA','pageId': 'NA',\
     'revisionId': 'NA','title': 'NA','url':'NA'}
    
    # figure out where notes and references section starts
    doNotUse = ['==','Further','reading','Notes','References']
    iNoteIdx = wp.content.find("Notes and references")
    nonRef = wp.content[0:iNoteIdx-1]
    ref = wp.content[iNoteIdx:len(wp.content)]
   
    # sentence statistics
    sentences = nonRef.split('.')
    results['nSents'] = len(sentences) # num of sentences
    sentenceLengths = [len(s.split()) for s in sentences]
    results['meanSentLen'] = mean(sentenceLengths) # average length of sentences
    results['medianSentLen'] = median(sentenceLengths) # median length of sentences
   
    # word statistics
    words = nonRef.split()
    words = [x for x in words if x not in doNotUse] # remove do not use words
    results['nWords'] = len(words)
    wordLengths = [len(w) for w in words]
    results['meanWordLength']  = mean(wordLengths)
    results['medianWordLength'] = median(wordLengths)
    
    # character statistics
    results['nChars'] = len(nonRef.replace('\n','').replace('=',''))    
    
    # num of words in intro section
    results['nWordsSummary'] = len(wp.summary.split())
    
    # other info
    results['nImages'] = len(wp.images)
    results['pageId'] = int(wp.pageid)
    
    results['revisionId'] = wp.revision_id 
    results['url'] = wp.url            
    results['nSections'] = wp.content.count('\n\n\n==')+1 # add 1 to account for fist section                 
    results['title'] = wp.title

    try:
        results['nLinks'] =  len(wp.links) # num internal links to other Wikipedia pages
    except:
        results['nLinks'] =  0 # no links
            
    try:
        results['nRefs'] = len(wp.references) # num external reference
    except:
        results['nRefs'] = 0 # no references
        
    return results    

# for each link, get some meta data and put in the table
def getWikiPagesMeta(links,DF,csvfilename,iStart=0,flags='NA',method=2):
    import pandas as pd    
    if iStart > 0:
        DF = pd.DataFrame().from_csv(csvfilename) # load existing dataframe from file and append to it
    
    if method == 1: # method 1 uses the wikitools api (slow)
        site = getSite()
        
    for i in range(iStart,len(links)):
        l = links[i]
        print(str(i) +"/" + str(len(links)) + ": " + l.text)

        title = l.text.replace('"','')
        if method == 1: # method 1 uses the wikitools api (slow)
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
        DF.to_csv(csvfilename, encoding='utf-8')
        i += 1
    return DF    
