# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 17:06:16 2014

@author: ahna
"""
import pickle
import scrapeWikipedia

qpfile = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/data/qualityPredictor.p'

    
def main():
    # load logistic regression
    with open(qpfile, 'rb') as f:
        qp = pickle.load(f)
    
    # grab meta data for this wikipedia page
    result = scrapeWikipedia.getWikiPageMeta(searchPhrase)
    
    # predict score
    print(['Predicted quality is ' + str(qp.qualityScore(result))])

if __name__ == '__main__': main()