# -*- coding: utf-8 -*-
"""
Wikipedia quality predictor object

Created on Thu Jun 12 19:07:13 2014
@author: ahna
"""
import numpy as np

class qualPred:
    def __init__(self):
        #self.featreNames = ['length','nextlinks','nimages','nlinks']
#        self.featureNames = ['featured', 'flagged', 'flags', 'meanSentLength', 'meanWordLength', 'medianSentLength', 'medianWordLength', 'nChars', 'nImages', 'nLinks', 'nRefs', 'nSections', 'nSents', 'nWordsSummary', 'pageId', 'revisionId', 'title', 'url']
        #self.iUseFeatures = ['meanWordLength','nImages','nLinks','nRefs','nSections', 'nWordsSummary']
#        self.iUseFeatures = ['nLinks','nWordsSummary']
        self.iUseFeatures = ['nImages', 'nLinks','nRefs', 'nWordsSummary','reading_ease','grade_level']
        self.testPropor = 0.4
        #self.logresfile = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/data/temp.p'
        self.rfclf = []
        self.randfor = []
        self.logres_clf = []
        self.logres = []
        
    # return feature featureVector f for a particular featureVec
    # featureVec is a dict returned from 
    def getFeatures(self,featureVec):
        f = []
        for name in self.iUseFeatures:
#            f.append(featureVec[name][0])
            f.append(featureVec[name])
        return f    

    # return a dictionary of feature importances
    def getFeatImpDict(self,features):
        featImp = self.featureImportances(features)
        featImpDict = dict()
        for i in range(len(self.iUseFeatures)):
            featImpDict[self.iUseFeatures[i]] = featImp[i]  
        return featImpDict

    # return quality score between 0 (low quality) and 1 (high quality)    
    def qualityScore(self,featureVec):
        f = self.getFeatures(featureVec)
        probs = self.randfor.predict_proba(f) 
        #probs = self.logres.predict_proba(f) 
        return(probs[0][1]) # first element is prob of low quality, second element is prob of high quality

    def featureImportances(self,featureVec):
        return self.rfclf.feature_importances_

    def computeQualityOverFeatureGrid(self):
        self.f1 = np.arange(0, 500, 5) # nlinks
        self.f2 = np.arange(0, 1400, 5) # nWordsSummary
        self.featSpaceScores = np.zeros((len(self.f1),len(self.f2)))
        for i1 in range(len(self.f1)):
            for i2 in range(len(self.f2)):
                self.featSpaceScores[i1][i2] = self.randfor.predict_proba([self.f1[i1],self.f2[i2]])[0][1]

    def plot(self):
        import matplotlib.pyplot as plt
        h = plt.contourf(self.f2,self.f1,self.featSpaceScores)
        plt.colorbar(h)


    def computeDistances(self,vec):
        from scipy.spatial.distance import euclidean       
        distances = np.zeros((len(self.f1),len(self.f2)))
        for i1 in range(len(self.f1)):
            for i2 in range(len(self.f2)):
                distances[i1][i2] = euclidean(vec,[self.f1[i1],self.f2[i2]])
        return distances
         
    def suggest(self,distances,thresh=0.9):         
        d2 = distances.reshape(len(self.f1)*len(self.f2),1)
        x2 = np.argsort(d2,axis=0)
        i1 = x2/len(self.f2)
        i2 = np.remainder(x2,len(self.f2))
        t = self.featSpaceScores > thresh
        d3 = distances[i1,i2]
        t3 = t[i1,i2]
        f1_temp = np.multiply(self.f1[i1],t3)
        f2_temp = np.multiply(self.f2[i2],t3)
        f1_indices = []
        f2_indices = []      
        for f in range(len(f1_temp)):
            if f1_temp[f] != 0:
                f1_indices.append(f1_temp[f][0])
                f2_indices.append(f2_temp[f][0])
        return f1_indices,f2_indices        
                

         
