# -*- coding: utf-8 -*-
"""
Views.py
Created on Fri Jun 13 13:42:00 2014

@author: ahna
"""

from flask import render_template, request, json, Response
import app
from app import app, host, port, user, passwd, db
from app.helpers.database import conDB, closeDB
import urllib
import pickle
import wikipedia
import pandas.io.sql as psql
import pymysql
from app.helpers import database
from app.helpers import scrapeWikipedia as sw
#from app.helpers.qualityPredictor import qualPred
#from app.helpers import qualityPredictor
from os import chdir, getcwd
import numpy as np


###################################################################
# ROUTING/VIEW FUNCTIONS
@app.route('/')
#@app.route('/index')
def index():
    # Renders index.html.
    return render_template('index.html')

###################################################################
@app.route('/data.json', methods=['POST', 'GET'])
def data():
    # load up machine learnt model parameters ###############################
#    print getcwd()
#    chdir('/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/app/helpers/')
    
#    from app.helpers import qualityPredictor
#    qpfile = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/qualityPredictorFile.p'
#    file = open(qpfile, 'rb')
#    qp = pickle.load(file)
#    file.close()
#    chdir('/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/')
#    print getcwd()
    
    # grab the saved random forest pipeline ###################################################
    qp = sw.getQualPred()

    # connect to database ###################################################
    con = conDB(host='localhost', port=3306, user='root', dbname='wikimeta')

    # get wikipedia search results #############
    searchPhrase =  urllib.unquote(request.args['q'])
    searchRes = wikipedia.search(searchPhrase, results=3, suggestion=False)
    if len(searchRes) < 1:
        return("Sorry. We didn't find any results for you. Please try a new search.")
  
    # check to see if search phrase is already in database
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
        print type(searchPhraseDF['url'])
        wikiscore = 100*searchPhraseDF['score'][0]
#        if wikiscore is NULL:
#            wikiscore = ws.scorePageDB(f,p,qp,conn)
        print("Score is " + str(wikiscore))
    else:
        return("Sorry. We didn't find any results for you. Please try a new search.")

    print searchPhraseDF['url']
    print searchResultUse[0]
     
    # prepare results to return:
    resultFeatureVec = {'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}
    featuredPageAvg = {'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}
    flaggedPageAvg = {'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}
    wikipediaAvg = {'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}


#    # make suggestions	
#    iUniq = [0]
#    if wikiscore < 1:  
#        nSuggest = 50
#        distances = qp.computeDistances([searchPhraseDF['nLinks'][0],searchPhraseDF['nWordsSummary'][0]])
#        f1_indices,f2_indices = qp.suggest(distances,thresh=0.9)
#        newscore = qp.randfor.predict_proba([f1_indices[0],f2_indices[0]])[0][1]
#        print searchPhraseDF['nLinks'][0],searchPhraseDF['nWordsSummary'][0],f1_indices[0],f2_indices[0],wikiscore,newscore

#        newPerf = np.zeros((nSuggest,3))
#        n = 0
#        ns = 0
#        while ns < nSuggest:
#            n0 = qp.randfor.predict_proba([f1_indices[n],searchPhraseDF['nWordsSummary'][0]])[0][1]
#            n1 = qp.randfor.predict_proba([searchPhraseDF['nLinks'][0],f2_indices[n]])[0][1]
#            if n0 != wikiscore and n1 != wikiscore:
#                # found suggestion that changed both scores                
#                newPerf[ns,0] = n0
#                newPerf[ns,1] = n1
#                newPerf[ns,2] = qp.randfor.predict_proba([f1_indices[n],f2_indices[n]])[0][1]
#                print n, newPerf[ns]
#                ns += 1
#            n += 1
#        print("n = " + str(n))
     
     
#     
#        newPerf = np.zeros((len(f1_indices),3))
#        coeff = np.zeros((len(f1_indices),1))
#        frac = np.zeros((len(f1_indices),2))
#        for n in range(100):
#            newPerf[n,0] = qp.randfor.predict_proba([f1_indices[n],searchPhraseDF['nWordsSummary'][0]])[0][1]
#            newPerf[n,1] = qp.randfor.predict_proba([searchPhraseDF['nLinks'][0],f2_indices[n]])[0][1]
#            newPerf[n,2] = qp.randfor.predict_proba([f1_indices[n],f2_indices[n]])[0][1]
#            coeff[n] = (newPerf[n,2]-wikiscore)/(newPerf[n,0]+newPerf[n,1])
#            frac[n,0] = newPerf[n,0]*coeff[n]
#            frac[n,1] = newPerf[n,1]*coeff[n]
#            #print n, newPerf[n],coeff[n],frac[n]
#
#        # get unique fractions        
#        ncols = frac.shape[1]
#        dtype = frac.dtype.descr * ncols
#        struct = frac.view(dtype)
#        uniqFrac,iUniq = np.unique(struct,return_index=True) 
#        uniqFrac = uniqFrac.view(frac.dtype).reshape(-1, ncols)
#        iUniq.sort() # iUniq are indices into frac and coeff that provide new shapes, in order of score
#        print frac[iUniq]
        #frac = qp.rfclf.feature_importances_ * (newscore - wikiscore)
    
    # put the feature importances into a dict
    #featImpDict = qp.getFeatImpDict(qp.getFeatures(searchPhraseDF))
    #featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore,'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}
#    featImpDicts = []
#    for j in range(len(iUniq)):
#        if wikiscore >= 1:
#            featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore}
#        elif newPerf[n,2] == 1:
#            i = iUniq[j]
#            featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore, \
#            'Change # links %s -> %s' % (searchPhraseDF['nLinks'][0],int(f1_indices[i])): frac[i,0], \
#            'Change # intro words %s -> %s' % (searchPhraseDF['nWordsSummary'][0],int(f2_indices[i])): frac[i,1]}
#        else:
#            i = iUniq[j]
#            featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore, \
#            'Change # links %s -> %s' % (searchPhraseDF['nLinks'][0],f1_indices[0]): frac[i,0], \
#            'Change # intro words %s -> %s' % (searchPhraseDF['nWordsSummary'][0],f2_indices[i]): frac[i,1], \
#            'room for improvement': 1-wikiscore-frac[0]-frac[1]}
#        featImpDicts.append(featImpDict)    
                        
		
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
@app.route('/out', methods=['POST','GET'])
def out():
	xloc = 5
	svgtxt = """
		<svg width="500" height="200">
			<line x1="50" y1="100" x2="450" y2="100" stroke="orange" stroke-width="40" /> <!-- Base bar -->
			<line x1="80" y1="100" x2="200" y2="100" stroke="teal" stroke-width="40" /> <!-- Sub bar -->
			<line x1="138" y1="100" x2="142" y2="100" stroke="red" stroke-width="40" /> <!-- Mean "line" -->
			<line x1="140" x2="150" y1="120" y2="130" stroke="red" stroke-width="4" /> <!-- Line connecting mean line to text -->

			<text x="155" y="140" fill="red" text-anchor="start" font-size="16" font-weight="bold">Wiki Mean</text>
		</svg>
	"""
   	wikiscore = 50
	return render_template('vis.html', searchPhrase=request.form['searchPhrase'], wikiscore=wikiscore, svgtxt=svgtxt)

# .format(xloc=xloc,xloc2=xloc)
#<line x1="{xloc:.2f}" y1="30" x2="{xloc2:.2f}" y2="310" stroke="teal" stroke-width="2" />

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
