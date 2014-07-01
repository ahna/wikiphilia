# -*- coding: utf-8 -*-
"""
Wikipedia quality predictor class object qualPred()
qualPred objects hold a learning pipeline 
Created on Thu Jun 12 19:07:13 2014
@author: ahna
"""
import numpy as np

#########################################################################
class qualPred:
    def __init__(self):
        self.iUseFeatures = ['nImages', 'nLinks','nRefs', 'nWordsSummary','grade_level']
        self.testPropor = 0.4
        self.rfclf = []
        self.randfor = []
        self.logres_clf = []
        self.logres = []
        
    #########################################################################
    # return feature featureVector f for a particular featureVec dict
    def getFeatures(self,featureVec):
        f = []
        for name in self.iUseFeatures:
            f.append(featureVec[name])
        return f    

    #########################################################################
    # return a dictionary of feature importances from learned model
    def getFeatImpDict(self,features):
        featImp = self.featureImportances(features)
        featImpDict = dict()
        for i in range(len(self.iUseFeatures)):
            featImpDict[self.iUseFeatures[i]] = featImp[i]  
        return featImpDict

    #########################################################################
    # return quality score between 0 (low quality) and 1 (high quality)    
    def qualityScore(self,featureVec):
        f = self.getFeatures(featureVec)
        probs = self.randfor.predict_proba(f) 
        return(probs[0][1]) # first element is prob of low quality, second element is prob of high quality

    #########################################################################
    def featureImportances(self,featureVec):
        return self.rfclf.feature_importances_

    #########################################################################
    # utility function to look at a 2D slice through feature space and see how the quality varies
    # TO DO: generalize this to take in any 2 dimensions (currently hard-coded for nLinks and nWordsSummary)
    def computeQualityOverFeatureGrid(self):
        self.f1 = np.arange(0, 500, 5) # nlinks
        self.f2 = np.arange(0, 1400, 5) # nWordsSummary
        self.featSpaceScores = np.zeros((len(self.f1),len(self.f2)))
        for i1 in range(len(self.f1)):
            for i2 in range(len(self.f2)):
                self.featSpaceScores[i1][i2] = self.randfor.predict_proba([self.f1[i1],self.f2[i2]])[0][1]

    #########################################################################
    def plotQualitySpace(self):
        import matplotlib.pyplot as plt
        h = plt.contourf(self.f2,self.f1,self.featSpaceScores)
        plt.colorbar(h)

    #########################################################################
    # compute distance from feature vector to every point in the quality space
    def computeDistances(self,vec):
        from scipy.spatial.distance import euclidean       
        distances = np.zeros((len(self.f1),len(self.f2)))
        for i1 in range(len(self.f1)):
            for i2 in range(len(self.f2)):
                distances[i1][i2] = euclidean(vec,[self.f1[i1],self.f2[i2]])
        return distances
         
    #########################################################################
    # this function is a bit of a hack not currently being used
    # make a list of suggestions for other combinations of features based on short distances that are above the threshold
    def suggest(self,distances,thresh=0.9):         
        d2 = distances.reshape(len(self.f1)*len(self.f2),1)
        x2 = np.argsort(d2,axis=0)
        i1 = x2/len(self.f2)
        i2 = np.remainder(x2,len(self.f2))
        t = self.featSpaceScores > thresh
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
                

         
