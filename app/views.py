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
from app.helpers import scrapeWikipedia
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
    
    qp = scrapeWikipedia.getQualPred()

    # connect to database ###################################################
    con = conDB(host='localhost', port=3306, user='root', dbname='wikimeta')

    # check if this page has score and features in the database #############
    searchPhrase =  urllib.unquote(request.args['q'])
    searchRes = wikipedia.search(searchPhrase, results=10, suggestion=False)
	
    # check to see if search phrase is already in database
    bAlreadyInDB = False 
    for i in range(len(searchRes)):
        sql = '''SELECT * FROM testing WHERE title="%s"'''%searchRes[i]
        searchPhraseDF = psql.frame_query(sql, con)
        if len(searchPhraseDF['id']) > 0:
            bAlreadyInDB = True
            break
    closeDB(con)
    
    if bAlreadyInDB:
        searchPhraseUse = searchRes[i]
        print("Using searchPhrase from database = " + searchPhraseUse)
        print searchPhraseDF
        print type(searchPhraseDF['url'])
        wikiscore = searchPhraseDF['score'][0]
        print("Score is " + str(wikiscore))
    else:
        print("searchPhrase not in DB... retrieving info")
        return('Retrieving info on ' + searchPhrase + '... please be patient....')
	
    if wikiscore < 1:    
        distances = qp.computeDistances([searchPhraseDF['nLinks'][0],searchPhraseDF['nWordsSummary'][0]])
        f1_indices,f2_indices = qp.suggest(distances,thresh=0.9)
        newscore = qp.randfor.predict_proba([f1_indices[0],f1_indices[1]])[0][1]
        print searchPhraseDF['nLinks'][0],searchPhraseDF['nWordsSummary'][0],f1_indices[0],f2_indices[0],wikiscore,newscore
       
        frac = qp.rfclf.feature_importances_ * \
        (newscore - wikiscore)
        print frac
    
    # put the feature importances into a dict
    #featImpDict = qp.getFeatImpDict(qp.getFeatures(searchPhraseDF))
    #featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore,'Mean Word Length':0.03646565,'# Links':0.03369929,'# References':0.09500643,'# Sections':0.05741374,'# Sentences':0.08198197,   '# Images':0.28234044,  '# Words in Intro':0.41309248}
    featImpDicts = []
    for i in range(100):
        if wikiscore >= 1:
            featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore}
        elif 1-wikiscore-frac[0]-frac[1] == 0:
            featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore, \
            '# links %s -> %s' % (searchPhraseDF['nLinks'][0],int(f1_indices[i])): frac[0], \
            '# intro words %s -> %s' % (searchPhraseDF['nWordsSummary'][0],int(f2_indices[i])): frac[1]}
        else:
            featImpDict = {'Wikiscore = %s'%wikiscore :wikiscore, \
            '# links %s -> %s' % (searchPhraseDF['nLinks'][0],f1_indices[0]): frac[0], \
            '# intro words %s -> %s' % (searchPhraseDF['nWordsSummary'][0],f2_indices[i]): frac[1], \
            'room for improvement': 1-wikiscore-frac[0]-frac[1]}
        featImpDicts.append(featImpDict)    
                    
		
    # grab meta data for this wikipedia page ################################# 
    #scores = {'meanWordLength':0.1,'nImages':0.1,'nLinks':0.1,'nRefs':0.1,'nSections':0.1,'nSents':0.1, 'nWordsSummary':0.1,'score':0.3}
#    scores = {'meanWordLength':0.1,'nImages':0.1,'nLinks':0.1,'nRefs':0.1,'nSections':0.1,'nSents':0.1, 'nWordsSummary':0.1,'score':0.3}
#    print scores
#    print type(scores)
#    out = {'results': [{'label': k, 'value': v} for k, v in featImpDict.iteritems()], 'searchPhrase': searchPhrase}
    out = {'results': [([{'label': k, 'value': v} for k, v in f.iteritems()]) for f in featImpDicts], 'searchPhrase': searchPhrase}
    return Response(json.dumps(out), mimetype='application/json') 
    #return('The predicted quality of the Wikipedia page for ' + searchPhrase + ' is ' + str(score))

###################################################################
@app.route('/out', methods=['POST','GET'])
def out():
	return render_template('vis.html', searchPhrase=request.form['searchPhrase'])


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
