# -*- coding: utf-8 -*-
"""
Views.py
Created on Fri Jun 13 13:42:00 2014

@author: ahna
"""

from flask import render_template, request
from app import app, host, port, user, passwd, db
from app.helpers.database import con_db
import urllib
#import MySQLdb
import pickle
from app.helpers import scrapeWikipedia
from app.helpers.qualityPredictor import qualPred


# To create a database connection, add the following
# within your view functions:
# con = con_db(host, port, user, passwd, db)

# connect to database here
#db = MySQLdb.connect(user="root",host="localhost",port=3306,db="world")

# ROUTING/VIEW FUNCTIONS
@app.route('/')
#@app.route('/index')
def index():
    # Renders index.html.
    return render_template('index.html')

@app.route('/out', methods=['POST'])
def out():
#    ["https://en.wikipedia.org/wiki/" + searchPhrase]
    qpfile = './app/helpers/qualityPredictorFile.p'
    qpfile = '/Users/ahna/Documents/Work/insightdatascience/project/insightfl/app/helpers/qualityPredictorFile.p'
    file = open(qpfile, 'rb')
    #print(file.read())
    qp = pickle.load(file)
    
    # grab meta data for this wikipedia page  
    searchPhrase = request.form['searchPhrase']
    print(type(searchPhrase))
    print("searching wikipedia for " + searchPhrase + "...")
    result = scrapeWikipedia.getWikiPageMeta(searchPhrase)
    print result
    if result['nimages'] < 2:
        return('Was not able to access meta data for the Wikipedia page for ' + searchPhrase +'. Please try a new search.')
    
    # predict score
    print("predicting score...")
    score = qp.qualityScore(result)
    print score
    return('The predicted quality of the Wikipedia page for ' + searchPhrase + ' is ' + str(score))

@app.route('/home')
def home():
    # Renders home.html.
    return render_template('home.html')

@app.route('/slides')
def about():
    # Renders slides.html.
    return render_template('slides.html')

@app.route('/author')
def contact():
    # Renders author.html.
    return render_template('author.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/<pagename>')
def regularpage(pagename=None):
    # Renders author.html.
    return "You've arrived at " + pagename
