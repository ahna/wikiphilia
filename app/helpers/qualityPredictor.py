# -*- coding: utf-8 -*-
"""
Wikipedia quality predictor object

Created on Thu Jun 12 19:07:13 2014
@author: ahna
"""

class qualPred:
    def __init__(self):
        self.featureNames = ['length','nextlinks','nimages','nlinks']
        self.testPropor = 1./3.
        #self.logres = []
        #self.logresfile = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/data/temp.p'

    # return feature vector f for a particular result
    # result is a dict returned from 
    def getFeatures(self,result):
        f = []
        for name in self.featureNames:
            f.append(result[name])
        return f    

    # return quality score between 0 (low quality) and 1 (high quality)    
    def qualityScore(self,result):
        f = self.getFeatures(result)
        print f
        probs = self.logres.predict_proba(f) 
        return(probs[0][1]) # first element is prob of low quality, second element is prob of high quality

