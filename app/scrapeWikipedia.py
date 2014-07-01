# -*- coding: utf-8 -*-
"""
scrapeWikipedia.py
This file defines the wikiScraper class
The wikiScraper scrapes specified wikipedia page(s) for specified feature(s)
It calculates a wikiscore according to learnt parameters and stores all the results in a CSV file or database.

Created on Wed Jun 11 17:24:41 2014
@author: ahna
"""
##########################################################################################################
# import tools & config file name
import pymysql
from app.database import *
import app.qualPred

configFileName = 'app/settings/development.cfg'
#configFileName = '/home/ubuntu/wikiscore/app/settings/development.cfg'
#configFileName = '/Users/ahna/Documents/Work/insightdatascience/project/wikiscore/webapp/app/settings/development.cfg'

    
##########################################################################################################                 
class wikiScraper():

    def __init__(self):
        import pandas as pd
        self.wp = [] # place for current wikipedia page
        self.iUseDB = ['meanWordLength','meanSentLength', 'nChars','nImages', 'nLinks','nSections', 'nSents',\
     'nRefs', 'nWordsSummary','pageId','revisionId','title','url','reading_ease','grade_level',\
     'ColemanLiauIndex','GunningFogIndex','ARI','SMOGIndex','flags','flagged','score']
        self.DF = pd.DataFrame(columns=self.iUseDB)
      
    ##########################################################################################################     
    # set up database
    def setUpDB(self, configFileName):
        self.configFileName = configFileName
        debug, self.host, self.port, self.user, self.passwd, self.dbname, localpath = grabDatabaseSettingsFromCfgFile(self.configFileName)
        self.qpfile = localpath + 'app/qualityPredictorFile.p'
          
    ##########################################################################################################     
    # get links to all  articles from a given URL
    def grabWikiLinksFromUrl(self,url):
        import urllib2
        from bs4 import BeautifulSoup
        response = urllib2.urlopen(url)
        content = response.read()
        soup = BeautifulSoup(content, "xml")
        return soup

    ##########################################################################################################     
    # get pageids for all content articles
    def grabWikiPageIDsFromDB(self):
        conn = conDB(self.host,self.dbname,passwd=self.passwd,port=self.port, user=self.user)
        cur = curDB(conn)
        cur.execute('''SELECT page_id FROM content_pages ORDER BY page_id''')
        self.pageids = cur.fetchall()
        closeDB(conn)
    
    ##########################################################################################################     
    # return a readability structure that has fields corresponding to several readability measures (see readability.FleschKincaidGradeLevel())    
    # WARNING: unwiedly function
    # TO DO: compress this function into a short loop with a few lines
    def getReadability(self):    
#        import nltk
        from nltk_contrib.readability.readabilitytests import ReadabilityTool
        text = self.wp.content.encode('utf8')
        if len(text) == 0:
            return None
        # strip out Notes and other irrelavant fields that will only add noise to the readability measures            
        try:            
            i = text.find('== Band members ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass
        try:            
            i = text.find('== Filmography ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass
        try:            
            i = text.find('== Bibliography ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass
        try:            
            i = text.find('== Selected filmography ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass
        try:            
            i = text.find('== Selected works ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass
        try:            
            i = text.find('== Discography ==')
            text = text[0:i] # don't use notes and references in readability measures
        except ValueError:
            pass
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
        if len(text) > 5: # don't measure readability on very short pages - causes errors and returns meaningless info
            readability = ReadabilityTool(text)    
        else:
            readability = None
        return readability
            
    ##########################################################################################################    
    # convert wikipage title and/or page number to feature dict 
    # WARNING: another unwiedly function
    def getWikiPageMeta(self,title=None,pageid=None):
        import wikipedia
        try:
            self.wp = wikipedia.page(title=title,pageid=pageid,auto_suggest=1)
        except:
            print "Skipped pageid " + str(pageid) + " because wikipedia search yielded no results"   
            return None
        
        results = dict()
        from numpy import mean, median

        # figure out where notes and references section starts
        doNotUse = ['==','Further','reading','Notes','References']
        iNoteIdx = self.wp.content.find("Notes and references")
        nonRef = self.wp.content[0:iNoteIdx-1]
        sentences = nonRef.split('.')
        words = nonRef.split()
        if len(self.wp.content) < 5:
            bNoText = 1
            print "No text on this Wikipedia page!"
        else:
            bNoText = 0        
  
        # measure readibility of text
        if (bNoText == 0) and ('reading_ease' in self.iUseDB or 'grade_level' in self.iUseDB):
            readability = self.getReadability()
            if readability is None:
                bNoText = 1

        # main loop: cycle through feature list a do the appropriate measure for each, saving to results
        for iUse in self.iUseDB:   
                
            if iUse == 'nSents': # sentence statistics
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
                cur.execute('''SELECT COUNT(1) FROM testing2 WHERE title = %s ''', title)
                isIn = min(1,cur.fetchall()[0][0])
            elif datatable == 'training2':
                try:
                    cur.execute('''SELECT COUNT(1) FROM training2 WHERE title = %s ''', title)
                except:
                    return isIn
                isIn = min(1,cur.fetchall()[0][0])
        return isIn
        
    ##########################################################################################################
    # for each wikipedia page, get some meta data and put in the database or csvfile
    def getWikiPagesMeta(self,links = 'NA',DF = 'NA',csvfilename = 'NA',iStart=0,title=None,flags=None,tablename='testing2'):
        import pandas as pd    
        p = None; score = None
        
        # if using a csvfile, load it into a dataframe from file and append to it
        if csvfilename != 'NA': 
            if iStart > 0:
                self.DF = pd.DataFrame().from_csv(csvfilename) 
        
        # open up database
        conn = conDB(self.host,self.dbname,passwd=self.passwd,port=self.port, user=self.user)
        cur = curDB(conn)
           
        print title, links
        if title is not None: # either search by the title
            n = 1; iStart = 0
        elif links != 'NA': # or search by a list of links
            n = len(links)
        else: # or search by the page ids
            n = len(self.pageids)
            
        # load up the learnt parameters   
        import pickle
        #import qualPred
        if False: # optionally relearn the parameters. This generally should not be necessary except due to changes in learning algorithm or feature set
            import learnWikipediaPageQuality
            print "about to relearn"
            #qp = qualPred.qualPred()
            qp = qualPred()
            qp.learn() #qp = learnWikipediaPageQuality.main()
            print qp
            print "learnt"        
        with open(self.qpfile, 'rb') as f:
            qp = pickle.load(f)
        print "Got qp"
        
        # for each link in the list    
        for i in range(iStart,n):
            if title is None:
                if links != 'NA': 
                    l = links[i] # dataframe method
                    print(str(i) +"/" + str(n) + ": " + l.text)
                    title = l.text.replace('"','') # fix for unicode junk
                else:
                    p = self.pageids[i][0] # database method

            bPageInDB = self.pageInDB(cur,p=p,title=title,datatable=tablename)
            print "bPageInDB=" + str(bPageInDB) 
            
            if not bPageInDB: # only continue if page not already in data base
                     
                new_row = None 
                if title is not None or p is not None: # grab 
                    print(str(i) +"/" + str(n) + ": " + str(p) + " in? : " + str(bPageInDB))
                    new_row = self.getWikiPageMeta(title,p)
                 
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
                    
                    score = new_row['score']
    
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
                        new_row = convert_types(list(new_row2))
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
                                score = self.scorePageDB(f,p,qp,conn)
                            except:
                                print "Skipping for testing2:  "
            i += 1              
        closeDB(conn)     # close up database        
        return score
        
    ##########################################################################################################
    # score wikipedia page and write to DB
    def scorePageDB(self,features,pageId,qp,conn):
        print "Scoring page " + str(pageId) 
        score = float(qp.qualityScore(features))
        print "Scoring page " + str(pageId) + " with score = " + str(score) 
        curDB(conn).execute('''UPDATE testing2 SET score=%s WHERE pageId=%s''',(score,int(pageId)))
        conn.commit()
        return score
        
    ##########################################################################################################
    # (re)score entire database based on features already in database (no new scraping here)
    def scoreDB(self,iStart = 0):

        # open database and get features and pageID
        conn = conDB(self.host,self.dbname,passwd=self.passwd,port=self.port, user=self.user)
        import pandas.io.sql as psql
        featuresDF = psql.frame_query("SELECT * FROM testing2", conn)
        pageId = psql.frame_query("SELECT pageId FROM testing2", conn)
        qp = getQualPred(self.qpfile)

        # go through each page
        print("Calculating scores & writing to database...")
        for f in range(iStart,len(pageId)):
            features = featuresDF.ix[f]
            p = int(pageId.ix[f])
            score = self.scorePageDB(features,p,qp,conn)
            print(str(f) + " / " + str(len(featuresDF)) + " : old / new scores " + str(features['score']) + " : " + str(score)  + " : page " + str(p))
                   
        closeDB(conn)

    ##########################################################################################################
    # utility function to remove duplicate rows from training2 table
    def removeDuplicates(self):
        conn = conDB(self.host,self.dbname,passwd=self.passwd,port=self.port, user=self.user)
        cur = curDB(conn)            
        sql = 'ALTER IGNORE TABLE training2 ADD UNIQUE INDEX pageId (pageId)'
        cur.execute(sql)
        closeDB(conn)
 
    ##########################################################################################################
    # utility function to remeasure entire database on featuerd and flagged pages, and recalculate readability
    def remeasureFeatFlagDB(self):

        conn = conDB(self.host,self.dbname,passwd=self.passwd,port=self.port, user=self.user)
        import pandas.io.sql as psql
        pageIds = psql.frame_query("SELECT pageid FROM testing2 WHERE featured = 1 OR flagged = 1", conn)

        # go through each page, rescrape features and write out readability to database
        print("Calculating readability & scores & writing to database...")
        for i in range(len(pageIds.values)):
            p = pageIds.values[i]
            sql = "SELECT * FROM testing2 WHERE pageid = %s" % p[0]
            featuresDF = psql.frame_query(sql, conn)
            print i, p[0], featuresDF['reading_ease'][0]
            new_row = self.getWikiPageMeta(title=featuresDF['title'][0], pageid=p[0])
            print new_row

            try:
                sql = "UPDATE testing2 SET grade_level = %s WHERE pageId = %s" % (str(new_row['grade_level']),str(p[0]))
                curDB(conn).execute(sql)
                sql = "UPDATE testing2 SET reading_ease = %s WHERE pageId = %s" % (str(new_row['reading_ease']),str(p[0]))
                curDB(conn).execute(sql)
                conn.commit()
            except:
                print "Skipping for testing2:  "
                pass            
                        
        closeDB(conn)
        
   ##########################################################################################################
    # utility function: run through all the pages and write to screen whether the page is in the database or not
    def checkPageInDB(self): 
                    
        conn = conDB(self.host,self.dbname,passwd=self.passwd,port=self.port, user=self.user)
        cur = curDB(conn)            
        n = len(self.pageids)
            
        for i in range(n):        # for each page in the page list    
            p = self.pageids[i][0]
            bPageInDB = self.pageInDB(cur,p=p,title=title)
            print(str(i) +"/" + str(n) + ": " + str(p) + " in : " + str(bPageInDB))
            
        closeDB(conn)    


##########################################################################################################
# SQL doesn't like the numpy types, so this utility function converts all items in row to types it likes       
def convert_types(row):
    import numpy as np
    type_dict = {np.float64:float, np.int64:int, np.bool_:bool, bool:bool, int:int, str:str, unicode:unicode,float:float}
    for j in range(len(row)):
        if row[j] == 'NA' or row[j] is None: 
            row[j] = None  
        else:
            try:    
                row[j] = type_dict[type(row[j])](row[j])
            except:
                row[j] = None
    return row

##########################################################################################################
# grab from disk the quality predictor object instance containing the learnt parameters
def getQualPred(qpfile):
    # open quality predictor
    import pickle
#    from app.qualPred import qualPred
    with open(qpfile, 'rb') as f:
        qp = pickle.load(f)
    print "got qp!"
    return qp


##########################################################################################################
def main():
    # scrape a set of wikipedia pages and add them to the database
    ws = wikiScraper()
    ws.setUpDB(configFileName)
    #ws.remeasureFeatFlagDB()
    #ws.grabWikiPageIDsFromDB()
    #ws.checkPageInDB()
    #ws.getWikiPagesMeta(iStart = 88545)
    ws.scoreDB(5051)
    

if __name__ == '__main__': main()
