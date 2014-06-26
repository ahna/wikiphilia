# -*- coding: utf-8 -*-
"""
Views.py
Created on Fri Jun 13 13:42:00 2014

@author: ahna
"""

from flask import render_template, request, json, Response
import app
from app import app, host, port, user, passwd, db
from app.helpers.database import conDB, closeDB, grabDatabaseSettingsFromCfgFile
import urllib
import pickle
import wikipedia
import pandas.io.sql as psql
import pymysql
#from app.helpers import database
#from app.helpers import scrapeWikipedia as sw
from app.helpers import database
from app.helpers import scrapeWikipedia as sw
#from app.helpers.qualPred import qualPred
from os import chdir, getcwd
import numpy as np
#configFileName = '/home/ubuntu/wikiphilia/app/settings/development.cfg'
configFileName = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/app/settings/development.cfg'
debug, host, port, user, passwd, dbname = grabDatabaseSettingsFromCfgFile(configFileName)


###################################################################
# ROUTING/VIEW FUNCTIONS
@app.route('/')
#@app.route('/index')
def index():
    # Renders index.html.
    return render_template('index.html')


###################################################################
# generate some HTML + SVG text for a single labelled bar
def genSvg(searchPhrase, searchPhraseDF):
    
    #con = conDB(host='localhost', port=3306, user='root', dbname='wikimeta')
    con = conDB(host,dbname,passwd=passwd,port=port, user=user)
    cur = con.cursor()

    svgtxt = ""
    iUseFeatures = ['grade_level','reading_ease', 'nLinks', 'nRefs', 'nWordsSummary','nImages']
    for i in range(len(iUseFeatures)):
        if iUseFeatures[i] == 'reading_ease':
            xmin = 0.; xmax = 100.
            featureName = "Reading Ease"
            cur.execute('''SELECT AVG(reading_ease) FROM testing2''')
        elif iUseFeatures[i] == 'grade_level':
            xmin = 0.; xmax = 20.
            featureName = "Grade Level"
            cur.execute('''SELECT AVG(grade_level) FROM testing2''')
        elif iUseFeatures[i] == 'nRefs':
            xmin = 0.; xmax = 500.
            featureName = "# External Links"
            cur.execute('''SELECT AVG(nRefs) FROM testing2''')
        elif iUseFeatures[i] == 'nLinks':
            xmin = 0.; xmax = 500.
            featureName = "# Wikipedia links"
            cur.execute('''SELECT AVG(nLinks) FROM testing2''')
        elif iUseFeatures[i] == 'nImages':
            xmin = 0.; xmax = 100.
            featureName = "# Images"
            cur.execute('''SELECT AVG(nImages) FROM testing2''')
        elif iUseFeatures[i] == 'nWordsSummary':
            xmin = 0.; xmax = 1000.
            featureName = "# Words in Intro"
            cur.execute('''SELECT AVG(nWordsSummary) FROM testing2''')

        featFrac = (searchPhraseDF[iUseFeatures[i]][0] - xmin)/(xmax-xmin)
        wikiMean = float(cur.fetchall()[0][0])
        meanFrac = (wikiMean - xmin)/(xmax-xmin)
        
        if i == 0:
            bLabel = True
        else:
            bLabel = False

        svgtxt += genSvgBox(featureName,featFrac,xmin=xmin,xmax=xmax,meanFrac=meanFrac,bLabel=bLabel)
    
    closeDB(con)
    return svgtxt
    
# create a set fo labelled bars for each feature name
def genSvgBox(featureName,featFrac,xmin=0,xmax=100,x1=0,x2=350,meanFrac=0.5,bLabel=False):
    xLocFeat=x1+featFrac*(x2-x1)
    xLocWikiMean=x1+meanFrac*(x2-x1)
    print featureName,xLocFeat, xLocWikiMean
    
    svgbox = """<svg width="500" height="100">
		<text x="{xloc1:.2f}" y="25" fill="black" text-anchor="start" font-size="16" font-weight="regular">{featureName}</text>
            <line x1="{xloc1:.2f}" y1="50" x2="{xloc2:.2f}" y2="50" stroke="#EEEEEE" stroke-width="40" /> <!-- Base bar -->
            <line x1="{xloc1:.2f}" y1="50" x2="{xLocFeat:.2f}" y2="50" stroke="teal" stroke-width="40" stroke-opacity=0.5 /> <!-- Sub bar -->
		<line x1="{xLocWikiMean:.2f}" y1="50" x2="{xLocWikiMean2:.2f}" y2="50" stroke="red" stroke-width="40" /> <!-- All of Wikipedia mean "line" -->
            <text x="{xloc1:.2f}" y="85" fill="black" text-anchor="start" font-size="16" font-weight="regular">{xmin}</text>          
            <text x="{xloc2:.2f}" y="85" fill="black" text-anchor="start" font-size="16" font-weight="regular">{xmax}</text>          
         """.format(featureName=featureName,xloc1=x1,xloc2=x2,xLocFeat=xLocFeat,xLocWikiMean=xLocWikiMean,\
         xLocWikiMean2=xLocWikiMean+4,xmin=int(xmin),xmax=int(xmax))
 
    if bLabel is True:
      svgbox += """<line x1="{xLocWikiMean:.2f}" x2="{xLocWikiMean2:.2f}" y1="68" y2="80" stroke="red" stroke-width="4" /> <!-- Line connecting mean line to text -->
		<text x="{xLocWikiMean3:.2f}" y="90" fill="red" text-anchor="start" font-size="16" font-weight="regular">Wikipedia Mean</text>
          """.format(xLocWikiMean=xLocWikiMean+2,xLocWikiMean2=xLocWikiMean+14,xLocWikiMean3=xLocWikiMean+20)
  
    svgbox += """</svg>"""
    return svgbox
    
###################################################################
@app.route('/out', methods=['POST','GET'])
def out():
    searchPhrase = request.form['searchPhrase']
    wikiscore, searchPhraseDF = getWikiScore(searchPhrase)
    svgtxt = genSvg(searchPhrase, searchPhraseDF)
    return render_template('vis.html', searchPhrase=searchPhrase, wikiscore=wikiscore, svgtxt=svgtxt, url=searchPhraseDF['url'][0])


###################################################################
def getWikiScore(searchPhrase):
    # load up machine learnt model parameters ###############################
    
    # grab the saved random forest pipeline ###################################################
    qp = sw.getQualPred()

    # connect to database ###################################################
    con = conDB(host,dbname,passwd=passwd,port=port, user=user)

    # get wikipedia search results #############
    print searchPhrase    
    searchRes = wikipedia.search(searchPhrase, results=3, suggestion=False)
    print searchRes
    if len(searchRes) < 1:
        return("Sorry. We didn't find any results for you. Please try a new search.")
  
    # first check to see if search phrase is already in database
    bAlreadyInDB = False 
    for i in range(len(searchRes)):
        print i, searchRes[i]
        sql = '''SELECT * FROM testing2 WHERE title="%s"'''%searchRes[i]
        searchPhraseDF = psql.frame_query(sql, con)
        if len(searchPhraseDF['id']) > 0:
            bAlreadyInDB = True
            searchResultUse = searchRes[i]
            print("Found " + searchResultUse +" testing2 database")
            break
    
    if bAlreadyInDB is False:
        print("searchPhrase not in DB... retrieving info")
        ws = sw.wikiScraper()
        i = 0
        ws.getWikiPagesMeta(title = searchRes[i],tablename='testing2')
        searchResultUse = searchRes[i]                
        sql = '''SELECT * FROM testing2 WHERE title="%s"'''%searchResultUse
        searchPhraseDF = psql.frame_query(sql, con)
        bAlreadyInDB = True
        
    closeDB(con)

    if bAlreadyInDB is True:
        print("Using searchPhrase from database = " + searchResultUse)
        print searchPhraseDF        
        wikiscore = int(round(100.*(searchPhraseDF['score'][0])))
#        if wikiscore is NULL:
#            wikiscore = ws.scorePageDB(f,p,qp,conn)
        print("Score is " + str(wikiscore))
    else:
    	wikiscore = None
        print("Sorry. We didn't find any results for you. Please try a new search.")

    print searchPhraseDF['url']
    print searchResultUse[0]
    return wikiscore, searchPhraseDF
     

###################################################################
# routine puts data to /data.json
@app.route('/data.json', methods=['POST', 'GET'])
def data():
    wikiscore = getWikiScore()
	
    # prepare results to return:
    resultFeatureVec = {'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}
    featuredPageAvg = {'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}
    flaggedPageAvg = {'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}
    wikipediaAvg = {'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}

    # grab meta data for this wikipedia page ################################# 
    #scores = {'meanWordLength':0.1,'nImages':0.1,'nLinks':0.1,'nRefs':0.1,'nSections':0.1,'nSents':0.1, 'nWordsSummary':0.1,'score':0.3}
#    scores = {'meanWordLength':0.1,'nImages':0.1,'nLinks':0.1,'nRefs':0.1,'nSections':0.1,'nSents':0.1, 'nWordsSummary':0.1,'score':0.3}
#    print scores
#    print type(scores)
#    out = {'results': [{'label': k, 'value': v} for k, v in featImpDict.iteritems()], 'searchPhrase': searchPhrase}
#    out = {'results': [([{'label': k, 'value': v} for k, v in f.iteritems()]) for f in featImpDicts], \
#    'searchPhrase': searchPhrase, 'url': searchPhraseDF['url'][0], 'wikiscore': wikiscore}
    out = {'results': ([{'label': k, 'value': v} for k, v in resultFeatureVec.iteritems()]),\
     'featuredPageAvg': ([{'label': k, 'value': v} for k, v in resultFeatureVec.iteritems()]), \
     'flaggedPageAvg': ([{'label': k, 'value': v} for k, v in resultFeatureVec.iteritems()]), \
     'wikipediaAvg': ([{'label': k, 'value': v} for k, v in resultFeatureVec.iteritems()]), \
     'searchPhrase': searchResultUse, 'url': searchPhraseDF['url'][0], 'wikiscore': wikiscore}
    return Response(json.dumps(out), mimetype='application/json') 
    #return('The predicted quality of the Wikipedia page for ' + searchPhrase + ' is ' + str(score))


###################################################################
@app.route('/vis')
def vis():
    # Renders vis.html.
    return render_template('vis.html')

###################################################################
@app.route('/home')
def home():
    # Renders home.html.
    return render_template('home.html')
    
###################################################################
@app.route('/slides')
def about():
    # Renders slides.html.
    return render_template('slides.html')

###################################################################
@app.route('/author')
def contact():
    # Renders author.html.
    return render_template('author.html')

###################################################################
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

###################################################################
@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

###################################################################
@app.route('/<pagename>')
def regularpage(pagename=None):
    # Renders author.html.
    return "You've arrived at " + pagename
    
    
###################################################################
def suggest():
   # make suggestions	
   iUniq = [0]
   if wikiscore < 1:  
       nSuggest = 50
       distances = qp.computeDistances([searchPhraseDF['nLinks'][0],searchPhraseDF['nWordsSummary'][0]])
       f1_indices,f2_indices = qp.suggest(distances,thresh=0.9)
       newscore = qp.randfor.predict_proba([f1_indices[0],f2_indices[0]])[0][1]
       print searchPhraseDF['nLinks'][0],searchPhraseDF['nWordsSummary'][0],f1_indices[0],f2_indices[0],wikiscore,newscore

       newPerf = np.zeros((nSuggest,3))
       n = 0
       ns = 0
       while ns < nSuggest:
           n0 = qp.randfor.predict_proba([f1_indices[n],searchPhraseDF['nWordsSummary'][0]])[0][1]
           n1 = qp.randfor.predict_proba([searchPhraseDF['nLinks'][0],f2_indices[n]])[0][1]
           if n0 != wikiscore and n1 != wikiscore:
               # found suggestion that changed both scores                
               newPerf[ns,0] = n0
               newPerf[ns,1] = n1
               newPerf[ns,2] = qp.randfor.predict_proba([f1_indices[n],f2_indices[n]])[0][1]
               print n, newPerf[ns]
               ns += 1
           n += 1
       print("n = " + str(n))
     
     
    
       newPerf = np.zeros((len(f1_indices),3))
       coeff = np.zeros((len(f1_indices),1))
       frac = np.zeros((len(f1_indices),2))
       for n in range(100):
           newPerf[n,0] = qp.randfor.predict_proba([f1_indices[n],searchPhraseDF['nWordsSummary'][0]])[0][1]
           newPerf[n,1] = qp.randfor.predict_proba([searchPhraseDF['nLinks'][0],f2_indices[n]])[0][1]
           newPerf[n,2] = qp.randfor.predict_proba([f1_indices[n],f2_indices[n]])[0][1]
           coeff[n] = (newPerf[n,2]-wikiscore)/(newPerf[n,0]+newPerf[n,1])
           frac[n,0] = newPerf[n,0]*coeff[n]
           frac[n,1] = newPerf[n,1]*coeff[n]
           #print n, newPerf[n],coeff[n],frac[n]
#
       # get unique fractions        
       ncols = frac.shape[1]
       dtype = frac.dtype.descr * ncols
       struct = frac.view(dtype)
       uniqFrac,iUniq = np.unique(struct,return_index=True) 
       uniqFrac = uniqFrac.view(frac.dtype).reshape(-1, ncols)
       iUniq.sort() # iUniq are indices into frac and coeff that provide new shapes, in order of score
       print frac[iUniq]
        #frac = qp.rfclf.feature_importances_ * (newscore - wikiscore)
    
    # put the feature importances into a dict
    #featImpDict = qp.getFeatImpDict(qp.getFeatures(searchPhraseDF))
    #featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore,'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}
   featImpDicts = []
   for j in range(len(iUniq)):
       if wikiscore >= 1:
           featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore}
       elif newPerf[n,2] == 1:
           i = iUniq[j]
           featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore, \
           'Change # links %s -> %s' % (searchPhraseDF['nLinks'][0],int(f1_indices[i])): frac[i,0], \
           'Change # intro words %s -> %s' % (searchPhraseDF['nWordsSummary'][0],int(f2_indices[i])): frac[i,1]}
       else:
           i = iUniq[j]
           featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore, \
           'Change # links %s -> %s' % (searchPhraseDF['nLinks'][0],f1_indices[0]): frac[i,0], \
           'Change # intro words %s -> %s' % (searchPhraseDF['nWordsSummary'][0],f2_indices[i]): frac[i,1], \
           'room for improvement': 1-wikiscore-frac[0]-frac[1]}
       featImpDicts.append(featImpDict)   
