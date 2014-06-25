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
from database import *
from qualPred import qualPred
#from app.helpers.readability_score.calculators.fleschkincaid import *
#from app.helpers.qualityPredictor import qualPred

#qpfile = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/qualityPredictorFile.p'
qpfile = '/home/ubuntu/wikiphilia/webapp/datasets/qualityPredictorFile.p'
#configFileName = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/app/settings/development.cfg'
configFileName = '/home/ubuntu/wikiphilia/app/settings/development.cfg'
debug, host, port, user, passwd, dbname = grabDatabaseSettingsFromCfgFile(configFileName)


##########################################################################################################
# SQL doesn't like the numpy types, so this function converts all items in row to types it likes       
def convert_types(row):
    import numpy as np
    type_dict = {np.float64:float, np.int64:int, np.bool_:bool, bool:bool, int:int, str:str, unicode:str,float:float}
    for j in range(len(row)):
        if row[j] == 'NA' or row[j] is None: # or (is_numlike(row[j]) and isnan(row[j])):
            row[j] = None  
        else:
            try:    
                row[j] = type_dict[type(row[j])](row[j])
            except:
                row[j] = None
    return row

##########################################################################################################
# grab the quality predictor object
def getQualPred(qpfile=qpfile):
    # open quality predictor
    import pickle
    print "imported modules"
    file = open(qpfile, 'rb')
    print("loaded file")
    qp = pickle.load(file)
    print "got qp!"
    return qp

##########################################################################################################                 
class wikiScraper():

    def __init__(self):
#        from wikitools import wiki
#        self.site = wiki.Wiki("http://en.wikipedia.org/w/api.php")         
        self.wp = [] # place for current wikipedia page
        self.method = 2 # which wiki api wrapper to use
        self.DF = pd.DataFrame(columns=['meanWordLength','meanSentLength', 'medianSentLength',  'medianWordLength', \
     'nChars','nImages', 'nLinks','nSections', 'nSents','nRefs', 'nWordsSummary','pageId','revisionId','title','url','reading_ease','grade_level',\
     'ColemanLiauIndex','GunningFogIndex','ARI','SMOGIndex','flags','flagged','score'])
        self.iUseDB = ['meanWordLength','meanSentLength', 'nChars','nImages', 'nLinks','nSections', 'nSents',\
     'nRefs', 'nWordsSummary','pageId','revisionId','title','url','reading_ease','grade_level',\
     'ColemanLiauIndex','GunningFogIndex','ARI','SMOGIndex',\
     'flags','flagged','score']
       
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
        
        #conn = conDB(dbname = 'enwiki')
        conn = conDB(host,dbname,passwd=passwd,port=port, user=user)
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
        resultDict = {'pageid': -1, 'title': None, 'nimages': -1, 'nlinks':-1, 'nextlinks':-1, 'length': -1, 'ncategories':-1, 'revlastdate':-1}
        #   resultDict = {'pageid': -1, 'title': None, 'nimages': -1, 'nlinks':-1, 'nextlinks':-1, 'length': -1, 'counter': -1, 'new': -1, 'ncategories':-1}
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
    
    def getReadability(self):    
        import nltk
        from nltk_contrib.readability.readabilitytests import ReadabilityTool
        text = self.wp.content.encode('utf8')
        if len(text) == 0:
            return None
        try:
            i = text.find('== Notes and references ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass
        try:
            i = text.find('== See also ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass
        try:
            i = text.find('== References ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass
        try:
            i = text.find('== External links ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass 
        try:
            i = text.find('== Further reading ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass   
        if len(text) > 5:
            readability = ReadabilityTool(text)    
        else:
            readability = None
        return readability
            
    ##########################################################################################################    
    # method 2 uses the wikipedia api (faster)
    # convert wikipage title to dict with meta info
    def getWikiPageMeta2(self,title=None,pageid=None):
        from numpy import mean, median
        import wikipedia
        try:
            self.wp = wikipedia.page(title=title,pageid=pageid,auto_suggest=1)
        except:
            print "Skipped pageid " + str(pageid)    
            return None

        results = dict()
        
        # figure out where notes and references section starts
        doNotUse = ['==','Further','reading','Notes','References']
        iNoteIdx = self.wp.content.find("Notes and references")
        nonRef = self.wp.content[0:iNoteIdx-1]
        #ref = wp.content[iNoteIdx:len(wp.content)]
        sentences = nonRef.split('.')
        words = nonRef.split()
        if len(self.wp.content) < 5:
            bNoText = 1
            print "No text!"
        else:
            bNoText = 0
        
        if (bNoText == 0) and ('reading_ease' in self.iUseDB or 'grade_level' in self.iUseDB):
#            import nltk
#            from nltk_contrib.readability.readabilitytests import ReadabilityTool
            readability = self.getReadability()
            if readability is None:
                bNoText = 1

        for iUse in self.iUseDB:   
            
            # sentence statistics
            if iUse == 'nSents':
                if bNoText:
                    results['nSents'] = 0
                else:
                    results['nSents'] = len(sentences) # num of sentences
            elif iUse == 'meanSentLength':
                if bNoText:
                    results['meanSentLength'] = 0
                else:
                    sentenceLengths = [len(s.split()) for s in sentences]
                    results['meanSentLength'] = mean(sentenceLengths) # average length of sentences
            elif iUse == 'medianSentLength':
                if bNoText:
                    results['medianSentLength'] = 0
                else:
                    sentenceLengths = [len(s.split()) for s in sentences]
                    results['medianSentLength'] = median(sentenceLengths) # median length of sentences
            elif iUse == 'nWords':  # word statistics
               words = [x for x in words if x not in doNotUse] # remove do not use words
               results['nWords'] = len(words)
            elif iUse == 'meanWordLength':
               if bNoText:
                   results['meanWordLength'] = 0
               else:
                   wordLengths = [len(w) for w in words]
                   results['meanWordLength']  = mean(wordLengths)
            elif iUse == 'medianWordLength':
               if bNoText:
                   results['medianWordLength'] = 0
               else:
                   wordLengths = [len(w) for w in words]
                   results['medianWordLength'] = median(wordLengths)       
            elif iUse == 'nChars': # character statistics
                if bNoText:
                    results['nChars'] = 0
                else:
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
                results['nSections'] = self.wp.content.count('\n\n==')+1 # add 1 to account for fist section                 
            elif iUse == 'title':
                results['title'] = self.wp.title
            elif iUse == 'grade_level':
                if bNoText:
                    results['grade_level'] = None
                else:
                    results['grade_level'] = readability.FleschKincaidGradeLevel() #getReportAll(text)
            elif iUse =='reading_ease':
                if bNoText:
                    results['reading_ease'] = None
                else:
                    try:
                        results['reading_ease'] = readability.FleschReadingEase()                
                    except:
                        results['reading_ease'] = None
            elif iUse =='ColemanLiauIndex':
                if bNoText:
                    results['ColemanLiauIndex'] = None                
                else:
                    results['ColemanLiauIndex'] = readability.ColemanLiauIndex()                
            elif iUse =='GunningFogIndex':
                if bNoText:
                    results['GunningFogIndex'] = None               
                else:
                    results['GunningFogIndex'] =  readability.GunningFogIndex()                   
            elif iUse =='ARI':
                if bNoText:
                    results['ARI'] = None
                else:
                    results['ARI'] = readability.ARI()    
            elif iUse =='SMOGIndex':
                if bNoText:
                    results['SMOGIndex'] = None
                else:
                    results['SMOGIndex'] = readability.SMOGIndex()
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
    def pageInDB(self,cur,p=None,title=None,datatable='testing2'):
        isIn = False
        if p is not None:
            if datatable == 'testing2':
                cur.execute('''SELECT COUNT(1) FROM testing2 WHERE pageid = %s ''', str(p))
                isIn = min(1,cur.fetchall()[0][0])
            elif datatable == 'training2':
                cur.execute('''SELECT COUNT(1) FROM training2 WHERE pageid = %s ''', str(p))               
                isIn = min(1,cur.fetchall()[0][0])
        elif title is not None:
            if datatable == 'testing2':
                cur.execute('''SELECT COUNT(1) FROM testing2 WHERE title = %s ''', str(title))
                isIn = min(1,cur.fetchall()[0][0])
            elif datatable == 'training2':
                try:
                    cur.execute('''SELECT COUNT(1) FROM training2 WHERE title = %s ''', str(title))                
                except:
                    return isIn
                isIn = min(1,cur.fetchall()[0][0])
        return isIn
        
    ##########################################################################################################
    # for each link, get some meta data and put in the table
    def getWikiPagesMeta(self,links = 'NA',DF = 'NA',csvfilename = 'NA',iStart=0,title=None,flags=None,tablename='testing2'):
        import pandas as pd    
        p = None
        
        if csvfilename != 'NA': 
            if iStart > 0:
                self.DF = pd.DataFrame().from_csv(csvfilename) # load existing dataframe from file and append to it
        
        if self.method == 1: # method 1 uses the wikitools api (slow)
            self.login()
            
        # open up database
        conn = conDB(host,dbname,passwd=passwd,port=port, user=user)
#        conn = conDB()
        cur = curDB(conn)
           
        print title, links
        if title is not None:
            n = 1
            iStart = 0
        elif links != 'NA':
            n = len(links)
        else:
            n = len(self.pageids)
            
        qp = getQualPred()
        print "Got qp"
        
        # for each link in the list    
        for i in range(iStart,n):
            if title is None:
                if links != 'NA':
                    # dataframe method
                    l = links[i]
                    print(str(i) +"/" + str(n) + ": " + l.text)
                    title = l.text.replace('"','') # fix for unicode junk
                else:
                    # database method
                    p = self.pageids[i][0]

            bPageInDB = self.pageInDB(cur,p=p,title=title,datatable=tablename)
            print "bPageInDB=" + str(bPageInDB) 
            # only continue if using data frame method or if page not alrady in data base
            if not bPageInDB:
                        
                if self.method == 1: # method 1 uses the wikitools api (slow)
                    new_row = self.getWikiPageMeta1(title)
                elif self.method == 2:
                    if p is not None:
                        print(str(i) +"/" + str(n) + ": " + str(p) + " in? : " + str(bPageInDB))
                    new_row = self.getWikiPageMeta2(title,p)
                 
                if new_row is not None: 
                    new_row['score'] = None                
                    new_row['flags'] = flags
                    if p is None:
                        p = new_row['pageId']
    
                    if flags is None:
                        new_row['flagged'] = False
                    else:
                        new_row['flagged'] = True
                        new_row['score'] = 0                 
    
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
                        print new_row
                        # insert row into database
                        if tablename == 'training2':
                            try:
                                cur.execute('''INSERT INTO training2 (meanWordLength,meanSentLength, \
                                nChars,nImages, nLinks,nSections, nSents,nRefs, nWordsSummary,pageId,\
                                revisionId,title,url,reading_ease,grade_level,\
                                ColemanLiauIndex,GunningFogIndex,ARI,SMOGIndex,flags,flagged,score) \
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', new_row)
                                conn.commit()
                            except:
                                print "Skipping for training2:  "
                                pass
                        else:
                            try:
                                cur.execute('''INSERT INTO testing2 (meanWordLength,meanSentLength, \
                                nChars,nImages, nLinks,nSections, nSents,nRefs, nWordsSummary,pageId,\
                                revisionId,title,url,reading_ease,grade_level,\
                                ColemanLiauIndex,GunningFogIndex,ARI,SMOGIndex,flags,flagged,score) \
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', new_row)
                                conn.commit()
                                print "Committed"
                                f = dict(zip(self.iUseDB,new_row)) 
                                f
                                self.scorePageDB(f,p,qp,conn)
                            except:
                                print "Skipping for testing2:  "
    
    
            i += 1  
            
        # close up database
        closeDB(conn)
        
        return True
        
    ##########################################################################################################
    # score page and write to DB
    def scorePageDB(self,features,pageId,qp,conn):
        score = float(qp.qualityScore(features))
        print "Scoring page " + str(pageId) + " with score = " + str(score)
        curDB(conn).execute('''UPDATE testing2 SET score=%s WHERE pageId=%s''',(score,int(pageId)))
        conn.commit()
        return score
        
    ##########################################################################################################
    # score entire database
    def scoreDB(self):

        qp = getQualPred()
        conn = conDB(host,dbname,passwd=passwd,port=port, user=user)
#        conn = conDB()
        import pandas.io.sql as psql
        
#        featuresDF = psql.frame_query("SELECT meanWordLength,nImages,nLinks,nRefs,nSections,nSents, nWordsSummary FROM testing", conn)
        featuresDF = psql.frame_query("SELECT * FROM testing2", conn)
        pageId = psql.frame_query("SELECT pageId FROM testing2", conn)

        # go through each page
        print("Calculating scores & writing to database...")
        for f in range(len(pageId)):
            features = featuresDF.ix[f]
            p = int(pageId.ix[f])
            score = self.scorePageDB(features,p,qp,conn)
            print(str(f) + " / " + str(len(featuresDF)) + " : " + str(score)  + " : " + str(p))

                   
        closeDB(conn)

 #   def removeDuplicates(self):
 #       ALTER IGNORE TABLE training2 ADD UNIQUE INDEX pageId (pageId);
 
   ##########################################################################################################
    # run through all the pages and write whether the page is in the database or not
    def checkPageInDB(self): 
                    
        # open up database
        conn = conDB(host,dbname,passwd=passwd,port=port, user=user)
        #conn = conDB()
        cur = curDB(conn)
            
        n = len(self.pageids)
            
        # for each link in the list    
        for i in range(n):
            p = self.pageids[i][0]
            bPageInDB = self.pageInDB(cur,p=p,title=title)
            print(str(i) +"/" + str(n) + ": " + str(p) + " in? : " + str(bPageInDB))
            
        closeDB(conn)    


##########################################################################################################
def main():
    # scrape a set of wikipedia pages and add them to the database
    ws = wikiScraper()
    ws.grabWikiPageIDsFromDB()
    #ws.checkPageInDB()
    ws.getWikiPagesMeta(iStart = 17619)
#    ws.scoreDB()
    

if __name__ == '__main__': main()
