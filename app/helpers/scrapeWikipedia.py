# -*- coding: utf-8 -*-
"""
scrapeWikipedia
Created on Wed Jun 11 17:24:41 2014

@author: ahna
"""

import urllib2
from bs4 import BeautifulSoup
import pymysql
import pandas as pd
from app.helpers.database import conDB, curDB, closeDB

##########################################################################################################
# SQL doesn't like the numpy types, so this function converts all items in row to types it likes       
def convert_types(row):
    import numpy as np
    type_dict = {np.float64:float, np.int64:int, np.bool_:bool, bool:bool, int:int, str:str, unicode:str,float:float}
    for j in range(len(row)):
        if row[j] == 'NA' or row[j] == None: # or (is_numlike(row[j]) and isnan(row[j])):
            row[j] = None  
        else:
            row[j] = type_dict[type(row[j])](row[j])
    return row

##########################################################################################################
# grab the quality predictor object
def getQualPred():
    # open quality predictor
    import pickle
    from app.helpers.qualityPredictor import qualPred
    #qpfile = './app/helpers/qualityPredictorFile.p'
    qpfile = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/qualityPredictorFile.p'
    file = open(qpfile, 'rb')
    qp = pickle.load(file)
    return qp

##########################################################################################################                 
class wikiScraper():

    def __init__(self):
#        from wikitools import wiki
#        self.site = wiki.Wiki("http://en.wikipedia.org/w/api.php")         
        self.wp = []
        self.method = 2 # which wiki api wrapper to use
        self.DF = pd.DataFrame(columns=['meanWordLength','meanSentLength', 'medianSentLength',  'medianWordLength', \
     'nChars','nImages', 'nLinks','nSections', 'nSents','nRefs', 'nWordsSummary','pageId',\
     'revisionId','title','url','score','flagged','flags'])
        self.iUseDB = ['meanWordLength','meanSentLength', 'nChars','nImages', 'nLinks','nSections', 'nSents',\
    'nRefs', 'nWordsSummary','pageId','revisionId','title','url','flagged','flags','score']
       
    def login(self):
        self.site.login("ahnagirshick", "HMb58tfj") # login - required for read-restricted wikis
  
    ##########################################################################################################     
    def grabWikiLinksFromUrl(self,url):
        # get links to all  articles
        response = urllib2.urlopen(url)
        content = response.read()
        soup = BeautifulSoup(content, "xml")
        return soup

    ##########################################################################################################     
    # get pageids for all content articles
    def grabWikiPageIDsFromDB(self):    
        conn = conDB(dbname = 'enwiki')
        cur = curDB(conn)
        cur.execute('''SELECT page_id FROM content_pages ORDER BY page_id''')
        self.pageids = cur.fetchall()
        closeDB(conn)

    ##########################################################################################################
    # function to convert wikitools.api.APIResult to a clean dict 
    def saveAPIRequestResult(result):
        from wikitools import api
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

    ##########################################################################################################
    # method 1 uses the wikitools api (slow)
    # convert wikipage title to dict with meta info
    def getWikiPageMeta1(self,title):
        from wikitools import api
        self.login()
        # create the request object & query the API
        params = {'action':'query', 'titles':title, 'prop':'info|images|links|extlinks|categories|revisions', 'rvprop':'timestamp'}   # to do, see if i can get more info in the query  
        request = api.APIRequest(self.site, params)
        result = self.saveAPIRequestResult(request.query())
        return result
        
    ##########################################################################################################    
    # method 2 uses the wikipedia api (faster)
    # convert wikipage title to dict with meta info
    def getWikiPageMeta2(self,title=None,pageid=None):
        from numpy import mean
        from numpy import median
        import wikipedia
        try:
            self.wp = wikipedia.page(title=title,pageid=pageid,auto_suggest=1,preload=True)
        except:
            print "Skipped pageid " + str(pageid)    
        results = dict()
        
        # figure out where notes and references section starts
        doNotUse = ['==','Further','reading','Notes','References']
        iNoteIdx = self.wp.content.find("Notes and references")
        nonRef = self.wp.content[0:iNoteIdx-1]
        #ref = wp.content[iNoteIdx:len(wp.content)]
        sentences = nonRef.split('.')
        words = nonRef.split()
       
        for iUse in self.iUseDB:   
            
            # sentence statistics
            if iUse == 'nSents':
                results['nSents'] = len(sentences) # num of sentences
            elif iUse == 'meanSentLength':
                sentenceLengths = [len(s.split()) for s in sentences]
                results['meanSentLength'] = mean(sentenceLengths) # average length of sentences
            elif iUse == 'medianSentLength':
                sentenceLengths = [len(s.split()) for s in sentences]
                results['medianSentLength'] = median(sentenceLengths) # median length of sentences
            elif iUse == 'nWords':  # word statistics
               words = [x for x in words if x not in doNotUse] # remove do not use words
               results['nWords'] = len(words)
            elif iUse == 'meanWordLength':
               wordLengths = [len(w) for w in words]
               results['meanWordLength']  = mean(wordLengths)
            elif iUse == 'meanWordLength':
               wordLengths = [len(w) for w in words]
               results['medianWordLength'] = median(wordLengths)       
            elif iUse == 'nChars': # character statistics
                results['nChars'] = len(nonRef.replace('\n','').replace('=',''))    
            elif iUse == 'nWordsSummary':    
                results['nWordsSummary'] = len(self.wp.summary.split()) # num of words in intro section
            elif iUse == 'nImages':
                results['nImages'] = len(self.wp.images)
            elif iUse == 'pageId':
                results['pageId'] = int(self.wp.pageid)
            elif iUse == 'revisionId':
                results['revisionId'] = self.wp.revision_id 
            elif iUse == 'url':
                results['url'] = self.wp.url            
            elif iUse == 'nSections':
                results['nSections'] = self.wp.content.count('\n\n\n==')+1 # add 1 to account for fist section                 
            elif iUse == 'title':
                results['title'] = self.wp.title
            elif iUse == 'nLinks':
                try:
                    results['nLinks'] =  len(self.wp.links) # num internal links to other Wikipedia pages
                except:
                    results['nLinks'] =  0 # no links
            elif iUse == 'nRefs':
                try:
                    results['nRefs'] = len(self.wp.references) # num external reference
                except:
                    results['nRefs'] = 0 # no references
            
        return results    
    
    ##########################################################################################################
    # check if wikipedia page is already in the DB
    def pageInDB(self,p,cur):
        isIn = False
        cur.execute('''SELECT COUNT(1) FROM testing WHERE pageid = %s ''', str(p))
        isIn = min(1,cur.fetchall()[0][0])
        return isIn
        
    ##########################################################################################################
    # for each link, get some meta data and put in the table
    def getWikiPagesMeta(self,links = 'NA',DF = 'NA',csvfilename = 'NA',iStart=0,flags=None,tablename='testing'):
        import pandas as pd    
        qp = getQualPred()
        title = None
        p = None
        
        if csvfilename != 'NA': 
            if iStart > 0:
                self.DF = pd.DataFrame().from_csv(csvfilename) # load existing dataframe from file and append to it
        
        if self.method == 1: # method 1 uses the wikitools api (slow)
            self.login()
            
        # open up database
        conn = conDB()
        cur = curDB(conn)
            
        if links != 'NA':
            n = len(links)
        else:
            n = len(self.pageids)
            
        
        # for each link in the list    
        for i in range(iStart,n):
            
            bPageInDB = self.pageInDB(p,cur)
            
            if links != 'NA':
                # dataframe method
                l = links[i]
                print(str(i) +"/" + str(n) + ": " + l.text)
                title = l.text.replace('"','')
            else:
                # database method
                p = self.pageids[i][0]
                
            # only continue if using data frame method or if page not alrady in data base
            if links != 'NA' or not bPageInDB:
                        
                if self.method == 1: # method 1 uses the wikitools api (slow)
                    new_row = self.getWikiPageMeta1(title)
                elif self.method == 2:
                    print(str(i) +"/" + str(n) + ": " + str(p) + " in? : " + str(bPageInDB))
                    new_row = self.getWikiPageMeta2(title,p)
                    
                new_row['score'] = None                
                new_row['flags'] = flags
                if flags == None:
                    new_row['flagged'] = False
                else:
                    new_row['flagged'] = True
                    new_row['score'] = 0                 
                    
                print new_row    
                if csvfilename != 'NA':     
                    # write to csv file
                    self.DF = self.DF.append(new_row,ignore_index=True)
                    self.DF.to_csv(csvfilename, encoding='utf-8')
                else:
                    # write to DB     
                    # row = list( featuredDF.ix[i,iUse])
                    new_row2 = list()
                    for u in self.iUseDB:
                        new_row2.append(new_row[u])
                    new_row = convert_types(list( new_row2))
                    
                    # insert row into database
                    if tablename == 'training':
                        cur.execute('''INSERT INTO training (meanWordLength,meanSentLength, \
                        nChars,nImages, nLinks,nSections, nSents,nRefs, nWordsSummary,pageId,\
                        revisionId,title,url,score,flagged,flags) \
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', new_row)
                    else:
                        try:
                            cur.execute('''INSERT INTO testing (meanWordLength,meanSentLength, \
                            nChars,nImages, nLinks,nSections, nSents,nRefs, nWordsSummary,pageId,\
                            revisionId,title,url,score,flagged,flags) \
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', new_row)
                            score = self.scorePageDB(features,p,qp,conn)
                        except:
                            print "Skipping:  "
                            print new_row   

            i += 1  
            
        # close up database
        closeDB(conn)
        
        return self.DF
        
    ##########################################################################################################
    # score page and write to DB
    def scorePageDB(self,features,pageId,qp,conn):
        score = float(qp.qualityScore(features))
        curDB(conn).execute('''UPDATE testing SET score=%s WHERE pageId=%s''',(score,int(pageId)))
        conn.commit()
        return score
        
    ##########################################################################################################
    # score entire database
    def scoreDB(self):

        qp = getQualPred()
        conn = conDB()
        import pandas.io.sql as psql
        
#        featuresDF = psql.frame_query("SELECT meanWordLength,nImages,nLinks,nRefs,nSections,nSents, nWordsSummary FROM testing", conn)
        featuresDF = psql.frame_query("SELECT nLinks, nWordsSummary FROM testing", conn)
        pageId = psql.frame_query("SELECT pageId FROM testing", conn)

        # go through each page
        print("Calculating scores & writing to database...")
        for f in range(len(pageId)):
            features = featuresDF.ix[f]
            p = int(pageId.ix[f])
            score = self.scorePageDB(features,p,qp,conn)
            print(str(f) + " / " + str(len(featuresDF)) + " : " + str(score)  + " : " + str(p))

                   
        closeDB(conn)

    ##########################################################################################################
    # run through all the pages and write whether the page is in the database or not
    def checkPageInDB(self): 
                    
        # open up database
        conn = conDB()
        cur = curDB(conn)
            
        n = len(self.pageids)
            
        # for each link in the list    
        for i in range(n):
            p = self.pageids[i][0]
            bPageInDB = self.pageInDB(p,cur)
            print(str(i) +"/" + str(n) + ": " + str(p) + " in? : " + str(bPageInDB))
            
        closeDB(conn)    


##########################################################################################################
def main():
    # scrape a set of wikipedia pages and add them to the database
    ws = wikiScraper()
    #ws.grabWikiPageIDsFromDB()
    #ws.checkPageInDB()
    #ws.getWikiPagesMeta()
    ws.scoreDB()
    

if __name__ == '__main__': main()
