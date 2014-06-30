# -*- coding: utf-8 -*-
"""
Views.py
Created on Fri Jun 13 13:42:00 2014

@author: ahna
"""
###################################################################
# set up
import urllib
import pickle
import wikipedia
import pandas.io.sql as psql
import pymysql
from flask import render_template, request, json, Response
import app
from app import app, host, port, user, passwd, db
from app.database import *
from app import scrapeWikipedia as sw
from os import chdir, getcwd
import numpy as np

###################################################################
#configFileName = '/home/ubuntu/wikiphilia/app/settings/development.cfg'
#configFileName = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/app/settings/development.cfg'
#debug, host, port, user, passwd, dbname, localpath = grabDatabaseSettingsFromCfgFile(configFileName)
configFileName = 'app/settings/development.cfg'

###################################################################
# MAIN PAGE WITH SEARCH BOX
@app.route('/')
def index():
    wiki_avg_svg = genSvgToFile('wiki.averages.svg')
    return render_template('index.html',text='')     # Renders index.html

   
###################################################################
# SEARCH RESULTS
@app.route('/out', methods=['POST','GET'])
def out():
    searchPhrase = request.form['searchPhrase']
    wikiscore, searchPhraseDF = getWikiScore(searchPhrase)
    print "wikiscore is " + str(wikiscore)
    if wikiscore is None:
        "here"
        return render_template('index.html',text='Please try again')
        
    svgtxt = genSvg(searchPhraseDF)
    return render_template('vis.html', searchPhrase=searchPhraseDF['title'][0], wikiscore=wikiscore, svgtxt=svgtxt, url=searchPhraseDF['url'][0])


###################################################################
# GET WIKISCORE FOR THE SEARCH PHRASE
def getWikiScore(searchPhrase):
    
    # get wikipedia search results ####################################
    print searchPhrase    
    searchRes = wikipedia.search(searchPhrase, results=3, suggestion=False)
    print searchRes
    if len(searchRes) < 1:
        print "Sorry. We didn't find any results for you. Please try a new search."
        return None, searchRes
  
    # connect to database ###################################################
    con = conDB(host,db,passwd=passwd,port=port, user=user)

    # first check to see if first search phrase results are already in database ############
    bInDB = False 
    for i in range(1): #range(len(searchRes)):
#        print i, searchRes[i]
        sql = '''SELECT * FROM testing2 WHERE title="%s"'''%searchRes[i]
        searchPhraseDF = psql.frame_query(sql, con)
        if len(searchPhraseDF['id']) > 0:
            bInDB = True
            searchResultUse = searchRes[i]
            #print("Found " + searchResultUse +" testing2 database")
            break

    # if the search phrase isn't in the data base, search and calculate score and add to db    
    if bInDB is False:
        print("searchPhrase not in DB... retrieving info")
        ws = sw.wikiScraper()
        ws.setUpDB(configFileName)
        searchResultUse = None
        for i in range(len(searchRes)):
            print i            
            score = ws.getWikiPagesMeta(title = searchRes[i],tablename='testing2')
            print score
            if score != None:
                searchResultUse = searchRes[i]
                break
        if searchResultUse != None:
            print searchResultUse
            print type(searchResultUse)
            sql = '''SELECT * FROM testing2 WHERE title="%s"'''%searchResultUse
            searchPhraseDF = psql.frame_query(sql, con)
            print searchPhraseDF
            if len(searchPhraseDF) > 0:
                bInDB = True
        
    closeDB(con)

    if bInDB is True:
        #print("Using searchPhrase from database = " + searchResultUse)
        print searchPhraseDF        
        wikiscore = normalizeWikiScore(searchPhraseDF['score'][0])
        print("Score is " + str(searchPhraseDF['score'][0]) + ", " + str(wikiscore))
    else:
        wikiscore = None
        print("Sorry, we didn't find any suitable results for you at this time. Please try a new search.")

    print searchPhraseDF['url']
    print searchResultUse[0]
    return wikiscore, searchPhraseDF
     
###################################################################
# map Wikiscores to a human-meaningful scale
def normalizeWikiScore(rawScore):
    origRange = (0.,1.)
    newRange = (1.,10.)
    m = (newRange[1]-newRange[0])/(origRange[1]-origRange[0])
    normScore = int(round(m * rawScore + newRange[0]))
    return normScore
    
###################################################################
def genSvgToFile(svgFileName = 'wiki.averages.svg'):
    svg = genSvg()
    file = open(svgFileName,'wb')
    file.write(svg)
    file.close()
    return svg

###################################################################
# generate some HTML + SVG text for a single labelled bar
def genSvg(searchPhraseDF = []):
    
    con = conDB(host,db,passwd=passwd,port=port, user=user)
    cur = con.cursor()

    svgtxt = ""
    iUseFeatures = ['grade_level','nLinks', 'nRefs', 'nWordsSummary','nImages']
    print genSvg
    for i in range(len(iUseFeatures)):
        # label the first bar
        bLabelWikiMean = False
        bLabelFlagged = False
        bLabelFeatured = False
        if i == 0:
            bLabelFeatured = True
            print searchPhraseDF
            if len(searchPhraseDF) == 0:
                bLabelWikiMean = True
                bLabelFlagged = True

        if iUseFeatures[i] == 'reading_ease':
            xmin = 0.; xmax = 100.
            featureName = "Reading Ease"
            if len(searchPhraseDF) > 0: 
                 featureName += " = " + str(int(round(searchPhraseDF[iUseFeatures[i]])))
            cur.execute('''SELECT AVG(reading_ease) FROM testing2''')
            wikiMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(reading_ease) FROM testing2 WHERE featured = 1''')
            featuredMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(reading_ease) FROM testing2 WHERE flagged = 1''')
            flaggedMean = float(cur.fetchall()[0][0])
        elif iUseFeatures[i] == 'grade_level':
            xmin = 5.; xmax = 15.
            featureName = "Readability Grade Level"
            if len(searchPhraseDF) > 0: 
                featureName += " = " + str(int(round(searchPhraseDF[iUseFeatures[i]])))
            cur.execute('''SELECT AVG(grade_level) FROM testing2 WHERE grade_level < 20''')
            wikiMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(grade_level) FROM testing2 WHERE featured = 1 AND grade_level < 20''')
            featuredMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(grade_level) FROM testing2 WHERE flagged = 1 AND grade_level < 20''')
            flaggedMean = float(cur.fetchall()[0][0])
        elif iUseFeatures[i] == 'nRefs':
            xmin = 0.; xmax = 100.
            featureName = "# External Links"
            if len(searchPhraseDF) > 0: 
                featureName += " = " +  str(int(round(searchPhraseDF[iUseFeatures[i]])))
            cur.execute('''SELECT AVG(nRefs) FROM testing2''')
            wikiMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(nRefs) FROM testing2 WHERE featured = 1''')
            featuredMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(nRefs) FROM testing2 WHERE flagged = 1''')
            flaggedMean = float(cur.fetchall()[0][0])
        elif iUseFeatures[i] == 'nLinks':
            xmin = 0.; xmax = 500.
            featureName = "# Wikipedia links"
            if len(searchPhraseDF) > 0: 
                 featureName += " = " +  str(int(round(searchPhraseDF[iUseFeatures[i]])))
            cur.execute('''SELECT AVG(nLinks) FROM testing2''')
            wikiMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(nLinks) FROM testing2 WHERE featured = 1''')
            featuredMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(nLinks) FROM testing2 WHERE flagged = 1''')
            flaggedMean = float(cur.fetchall()[0][0])
        elif iUseFeatures[i] == 'nImages':
            xmin = 0.; xmax = 50.
            featureName = "# Images"
            if len(searchPhraseDF) > 0: 
                 featureName += " = " +  str(int(round(searchPhraseDF[iUseFeatures[i]])))
            cur.execute('''SELECT AVG(nImages) FROM testing2''')
            wikiMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(nImages) FROM testing2 WHERE featured = 1''')
            featuredMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(nImages) FROM testing2 WHERE flagged = 1''')
            flaggedMean = float(cur.fetchall()[0][0])
        elif iUseFeatures[i] == 'nWordsSummary':
            xmin = 30.; xmax = 500.
            featureName = "# Words in Intro"
            if len(searchPhraseDF) > 0: 
                 featureName += " = " +  str(int(round(searchPhraseDF[iUseFeatures[i]])))
            cur.execute('''SELECT AVG(nWordsSummary) FROM testing2''')
            wikiMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(nWordsSummary) FROM testing2 WHERE featured = 1''')
            featuredMean = float(cur.fetchall()[0][0])
            cur.execute('''SELECT AVG(nWordsSummary) FROM testing2 WHERE flagged = 1''')
            flaggedMean = float(cur.fetchall()[0][0])

        if len(searchPhraseDF) > 0: 
            featFrac = (max(min(searchPhraseDF[iUseFeatures[i]][0], xmax), xmin) - xmin)/(xmax-xmin)
            wikiMeanFrac = None
            flaggedMeanFrac = None
        else:
            # analtics image
            featFrac = 0
            wikiMeanFrac = (wikiMean - xmin)/(xmax-xmin)
            flaggedMeanFrac = (flaggedMean - xmin)/(xmax-xmin)

        featuredMeanFrac = (featuredMean - xmin)/(xmax-xmin)
        #print featFrac, wikiMeanFrac, featuredMeanFrac,  flaggedMeanFrac
        
        svgtxt += genSvgBox(featureName,featFrac,xmin=xmin,xmax=xmax,wikiMeanFrac=wikiMeanFrac,\
        featuredMeanFrac=featuredMeanFrac,flaggedMeanFrac=flaggedMeanFrac,bLabelWikiMean=bLabelWikiMean,bLabelFlagged=bLabelFlagged,bLabelFeatured=bLabelFeatured)
    
    closeDB(con)
    return svgtxt
    
# create a set for labelled bars for each feature name
def genSvgBox(featureName,featFrac,xmin=0,xmax=100,x1=0,x2=350,wikiMeanFrac=None,featuredMeanFrac=None,flaggedMeanFrac=None,bLabelWikiMean=False, bLabelFlagged=False, bLabelFeatured=False):
    xFeat=x1+featFrac*(x2-x1)
    if wikiMeanFrac != None:
        xWikiMean=x1+wikiMeanFrac*(x2-x1)
#    print featureName,xFeat, xWikiMean
    if featuredMeanFrac != None:
        xFeaturedMean=x1+featuredMeanFrac*(x2-x1)
    if flaggedMeanFrac != None:
        xFlaggedMean=x1+flaggedMeanFrac*(x2-x1)
#    print xFeat, xWikiMean, xFeaturedMean, xFlaggedMean
   
    height = 100
    hOffset = 0
    xOffset = 292
    if  bLabelWikiMean is True and bLabelFlagged is True and  bLabelFeatured is True:
        hOffset = 32
    height += hOffset
    
    svgbox = """<svg width="500" height="{h}">
		<text x="{xloc1:.2f}" y="{y}" fill="black" text-anchor="start" font-size="16" font-weight="regular">{featureName}</text>
            <line x1="{xloc1:.2f}" y1="{y1}" x2="{xloc2:.2f}" y2="{y1}" stroke="#EEEEEE" stroke-width="40" /> <!-- Base bar -->
            <line x1="{xloc1:.2f}" y1="{y1}" x2="{xFeat:.2f}" y2="{y1}" stroke="teal" stroke-width="40" stroke-opacity=0.5 /> <!-- Sub bar -->
            <text x="{xloc1:.2f}" y="{y2}" fill="black" text-anchor="start" font-size="16" font-weight="regular">{xmin}</text>          
            <text x="{xloc2:.2f}" y="{y2}" fill="black" text-anchor="start" font-size="16" font-weight="regular">{xmax}</text>          
         """.format(h=height,featureName=featureName,xloc1=x1,xloc2=x2,xFeat=xFeat,xmin=int(xmin),xmax=int(xmax),y=25+hOffset, y1=50+hOffset, y2=85+hOffset)

    if wikiMeanFrac != None:
	svgbox += """<line x1="{xWikiMean:.2f}" y1="{y1}" x2="{xWikiMean2:.2f}" y2="{y1}" stroke="green" stroke-width="40" /> <!-- All of Wikipedia mean "line" -->
         """.format(xWikiMean=xWikiMean,xWikiMean2=xWikiMean+4,y1=50+hOffset)
 
    if featuredMeanFrac != None:
        svgbox += """<line x1="{xFeaturedMean:.2f}" y1="{y1}" x2="{xFeaturedMean2:.2f}" y2="{y1}" stroke="blue" stroke-width="40" /> <!-- Featured on Wikipedia mean "line" -->
        """.format(xFeaturedMean=xFeaturedMean, xFeaturedMean2=xFeaturedMean+4,y1=50+hOffset)
 
    if flaggedMeanFrac != None:
        svgbox += """<line x1="{xFlaggedMean:.2f}" y1="{y1}" x2="{xFlaggedMean2:.2f}" y2="{y1}" stroke="red" stroke-width="40" /> <!-- Flagged on Wikipedia mean "line" -->
        """.format(xFlaggedMean=xFlaggedMean, xFlaggedMean2=xFlaggedMean+4,y1=50+hOffset)

    if bLabelWikiMean is True:
        svgbox += """<line x1="{xWikiMean:.2f}" x2="{xWikiMean2:.2f}" y1="{y1}" y2="{y2}" stroke="green" stroke-width="4" /> <!-- Line connecting Wikipedia mean line to text -->
		<text x="{xWikiMean3:.2f}" y="{y2}" fill="green" text-anchor="start" font-size="16" font-weight="regular">Wikipedia Avg</text>
          """.format(xWikiMean=xWikiMean+1.5,xWikiMean2=xWikiMean+102,xWikiMean3=xOffset+15,y1=32+hOffset,y2=-20+hOffset)
 
    if bLabelFeatured is True:
        if bLabelWikiMean and bLabelFlagged:
           svgbox += """<line x1="{xFeaturedMean:.2f}" x2="{xFeaturedMean2:.2f}" y1="{y1}" y2="{y2}" stroke="blue" stroke-width="4" /> <!-- Line connecting featured mean line to text -->
            <text x="{xFeaturedMean3:.2f}" y="{y2}" fill="blue" text-anchor="start" font-size="16" font-weight="regular">Avg High Quality Page</text>
            """.format(xFeaturedMean=xFeaturedMean+1.5,xFeaturedMean2=xOffset+12,xFeaturedMean3=xOffset+15,y1=32+hOffset,y2=20+hOffset)
        else:
             svgbox += """<line x1="{xFeaturedMean:.2f}" x2="{xFeaturedMean2:.2f}" y1="32" y2="18" stroke="blue" stroke-width="4" /> <!-- Line connecting featured mean line to text -->
            <text x="{xFeaturedMean3:.2f}" y="12" fill="blue" text-anchor="start" font-size="16" font-weight="regular">Avg High Quality Page</text>
            """.format(xFeaturedMean=xFeaturedMean+1.5,xFeaturedMean2=xFeaturedMean+9,xFeaturedMean3=xFeaturedMean-40)


    if bLabelFlagged is True:
        svgbox += """<line x1="{xFlaggedMean:.2f}" x2="{xFlaggedMean2:.2f}" y1="{y1}" y2="{y2}" stroke="red" stroke-width="4" /> <!-- Line connecting flagged mean line to text -->
		<text x="{xFlaggedMean3:.2f}" y="{y2}" fill="red" text-anchor="start" font-size="16" font-weight="regular">Avg Low Quality Page</text>
          """.format(xFlaggedMean=xFlaggedMean+1.5,xFlaggedMean2=xOffset+12,xFlaggedMean3=xOffset+15,y1=32+hOffset,y2=0+hOffset)
 
    svgbox += """</svg>"""
    return svgbox

#    if bLabelWikiMean is True:
#        svgbox += """<line x1="{xWikiMean:.2f}" x2="{xWikiMean2:.2f}" y1="68" y2="80" stroke="green" stroke-width="4" /> <!-- Line connecting Wikipedia mean line to text -->
#		<text x="{xWikiMean3:.2f}" y="90" fill="green" text-anchor="start" font-size="16" font-weight="regular">Wikipedia Avg</text>
#          """.format(xWikiMean=xWikiMean+1,xWikiMean2=xWikiMean+14,xWikiMean3=xWikiMean+20)
# 
#    if bLabelFeatured is True:
#        svgbox += """<line x1="{xFeaturedMean:.2f}" x2="{xFeaturedMean2:.2f}" y1="32" y2="20" stroke="blue" stroke-width="4" /> <!-- Line connecting featured mean line to text -->
#		<text x="{xFeaturedMean3:.2f}" y="20" fill="blue" text-anchor="start" font-size="16" font-weight="regular">Avg High Quality Page</text>
#          """.format(xFeaturedMean=xFeaturedMean+3,xFeaturedMean2=xFeaturedMean-9,xFeaturedMean3=xFeaturedMean-160)
#
#    if bLabelFlagged is True:
#        svgbox += """<line x1="{xFlaggedMean:.2f}" x2="{xFlaggedMean2:.2f}" y1="32" y2="20" stroke="red" stroke-width="4" /> <!-- Line connecting flagged mean line to text -->
#		<text x="{xFlaggedMean3:.2f}" y="20" fill="red" text-anchor="start" font-size="16" font-weight="regular">Avg Low Quality Page</text>
#          """.format(xFlaggedMean=xFlaggedMean+1.5,xFlaggedMean2=xFlaggedMean+12,xFlaggedMean3=xFlaggedMean+15)
          
###################################################################
# routine puts data to /data.json
@app.route('/data.json', methods=['POST', 'GET'])
def data():
    wikiscore = getWikiScore()
	
    # grab meta data for this wikipedia page ################################# 
#    out = {'results': [{'label': k, 'value': v} for k, v in featImpDict.iteritems()], 'searchPhrase': searchPhrase}
    out = {'results': [([{'label': k, 'value': v} for k, v in f.iteritems()]) for f in featImpDicts], \
    'searchPhrase': searchPhrase, 'url': searchPhraseDF['url'][0], 'wikiscore': wikiscore}
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
# ANALYTICS PAGE WITH WITH MEANS ACROSS WIKIPEDIA
@app.route('/analytics')
def analytics():
    wiki_avg_svg = genSvgToFile('wiki.averages.svg')
    return render_template('vis.analytics.html',svgtxt=wiki_avg_svg)     # vis.analytics.html

    
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
