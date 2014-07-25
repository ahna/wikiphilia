# -*- coding: utf-8 -*-
"""
Wikipedia quality predictor class object qualPred()
qualPred objects hold a learning pipeline
learn() is the main function that learns the quality of Wikipedia pages, saves the pipeline for future predictions
It learns from featured and flagged Wikipedia pages: 
Featured Wikipedia pages are "high quality" (wikiscore = 1)
Flagged Wikipedia pages are "low quality" (wikiscore = 0)
The Wikiscore as the probability that a given page is high quality
qualityScore() returns the wikiscore given a dictionary of feature values

Created on Thu Jun 12 19:07:13 2014
@author: ahna
"""
import numpy as np
import sklearn
import sklearn.linear_model
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.metrics import recall_score, precision_score
from app.database import *
#configFileName = '/home/ubuntu/wikiphilia/app/settings/development.cfg'
#configFileName = '/Users/ahna/Documents/Work/insightdatascience/project/wikiscore/webapp/app/settings/development.cfg'
configFileName = 'app/settings/development.cfg'

#########################################################################
class qualPred:
    def __init__(self):
        self.iUseFeatures = ['nImages', 'nLinks','nRefs', 'nWordsSummary','grade_level']
        self.discretize= {'nImages':True, 'nLinks':True, 'nRefs':True, 'nWordsSummary':True, 'grade_level':False}
        self.testPropor = 0.4
        self.rfclf = []
        self.randfor = []
        self.logres_clf = []
        self.logres = []
        self.bUsingBuckets = True

    #########################################################################
    # learn() is the main function that fits the data and saves the pipeline for future predictions
    def learn(self):
        self.setUpLearningPipeline()
        self.setUpData()
        self.fitData()
        self.save()
        self.printReport()
        
    #########################################################################
    # return feature featureVector f for a particular featureVec dict
    def getFeatures(self,featureVec):
        f = []
        from pandas.core.series import Series as Series
        for name in self.iUseFeatures:
            thisFeature = featureVec[name]
            if type(thisFeature) == Series:
                thisFeature = thisFeature[0]
            f.append(thisFeature) 
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
        print("features = " + str(f))
        if len([x for x in f if np.isnan(x)]) > 0:
            return 0.0
        else:
            if self.bUsingBuckets:
                f = self.getBuckets(f) # if using buckets, put into buckets before scoring
            probs = self.randfor.predict_proba(f) 
            return(probs[0][1]) # first element is prob of low quality, second element is prob of high quality

    #########################################################################
    def featureImportances(self):
        return self.rfclf.feature_importances_

    #########################################################################
    # learning pipeline setup
    def setUpLearningPipeline(self):
        # create random forest classifier pipeline
        self.rfclf = RandomForestClassifier(n_estimators=10) 
        self.randfor = Pipeline([("scaler", preprocessing.StandardScaler()), ("clf", self.rfclf)])
        # build learning pipeline for logistic regression classifier
        self.logres_clf = sklearn.linear_model.LogisticRegression(C=0.35) 
        self.logres = Pipeline([("scaler", preprocessing.StandardScaler()), ("clf", self.logres_clf)])
        # build learning pipeline for extra trees classifier
        self.xtrees_clf = sklearn.ensemble.ExtraTreesClassifier(n_estimators=10)
        self.xtrees = Pipeline([("scaler", preprocessing.StandardScaler()), ("clf", self.xtrees_clf)])

    #########################################################################
    # grab appropriate data from data base and split for testing
    def setUpData(self):
    
        debug, host, port, user, passwd, dbname, localpath = grabDatabaseSettingsFromCfgFile(configFileName)
        self.qualityPredictorFile = localpath + 'app/qualityPredictorFile.p'
        conn = conDB(host,dbname,passwd,port, user)	
        #featured_csvfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/featured.csv'
        #flagged_csvfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/flagged.csv'

        # load data from database
        import pandas.io.sql as psql
        DF = psql.frame_query("SELECT * FROM testing2 WHERE flagged = 1 OR featured = 1", conn)        
        DF = DF[~np.isnan(DF.meanWordLength)]   # remove rows with NaN in meanWordLength
        DF = DF[~np.isnan(DF.reading_ease)]     # remove rows with NaN in reading_ease  
        X = DF[self.iUseFeatures].values         #.astype('float')
        
        if self.bUsingBuckets: 
            maxes = list()
            for i in range(len(self.iUseFeatures)):
                sql = "SELECT AVG({}), STD({}) FROM testing2 WHERE featured = 1".format(self.iUseFeatures[i],self.iUseFeatures[i])
                temp = psql.frame_query(sql, conn)
                maxes.append(sum(temp.ix[0])) # add up average + standard dev of featued pages to be used for the maximum bucket value
            self.computeBuckets(X,maxes)                  # for some of the features, compute buckets so as not to use raw values but use "low","med","high" or more values
            X = self.getAllBuckets(X)               # put some of the features into buckets
            
        y = DF['score'].values                  # labels are 1 if featured is True, 0 if flagged is True
        np.random.seed()                        # divide into training set and test set
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(\
        X, y, test_size=self.testPropor, train_size=1-self.testPropor, random_state=np.random.random_integers(100))
        closeDB(conn)

    #########################################################################
    # for certain features, discretize into buckets and mark left edge of bucket
    def computeBuckets(self,X,maxes):
        self.buckets = dict()
        nBuckets = 100
        for i in range(len(self.iUseFeatures)):
            if self.discretize[self.iUseFeatures[i]]:
                bins = np.linspace(0, maxes[i], nBuckets)
                self.buckets[self.iUseFeatures[i]] = bins[0:len(bins)-1] # remove last bin since these are left edges of bins

    #########################################################################
    def getBuckets(self,f):
        # f is a feature vector (array) of same length and ordering as self.iUseFeatures
        # t is a transformed version of f    
        t = list()
        for i in range(len(self.iUseFeatures)): # for each feature
            if self.discretize[self.iUseFeatures[i]]: # if it is a feature we are discretizing
                buckets2 = self.buckets[self.iUseFeatures[i]]
                t.append(len(buckets2)) # default to last bucket
                for b in range(1,len(buckets2)): # step through the buckets unti we find the right one
                    if f[i] < buckets2[b]:
                        t[i] = b-1 # nearest bucket
                        break;
            else:
                t.append(f[i])  # not discretizing- just keep original version
        return t      

    #########################################################################
    # for a matrix of feature value, grab nearest bucket
    # X has the same number of columns as in self.iUseFeatures and same ordering
    def getAllBuckets(self,X):
        n = len(X[:,0])
        X2 = np.zeros(X.shape)
        for j in range(n): # for each index j in the list of values of that feature
            X2[j,:] = self.getBuckets(X[j,:])  
        return X2    
              

    #########################################################################
    # fit the data using random forest, logistic regression, and decision trees
    def fitData(self):
        self.randfor.fit(self.X_train, self.y_train)
        print self.randfor.score(self.X_test, self.y_test)
        for i in range(len(self.iUseFeatures)):
            print self.iUseFeatures[i], self.rfclf.feature_importances_[i]
        self.logres.fit(self.X_train, self.y_train)
        self.logres.score(self.X_test,self.y_test)
        self.xtrees.fit(self.X_train, self.y_train)
        self.xtrees.score(self.X_test,self.y_test)

    #########################################################################
    # print out report of accuracy, recall, precision on test set
    def printReport(self):
        preds = self.randfor.predict(self.X_test)
        print("Random forest score on training data: " + str(self.randfor.score(self.X_train, self.y_train)))
        print("Random forest score on test data: " + str(self.randfor.score(self.X_test, self.y_test)))
        print("Random forest recall score on test data: " + str(recall_score(self.y_test, preds)))
        print("Random forest precision score on test data: " + str(precision_score(self.y_test, preds)))
    
        print "Random forest feature importances:"         # Print out which features matter and drop the ones that don't
        print self.iUseFeatures
        print self.rfclf.feature_importances_

        preds = self.logres.predict(self.X_test)
        print("Logistic regression score on training data: " + str(self.logres.score(self.X_train, self.y_train)))
        print("Logistic regression score on test data: " + str(self.logres.score(self.X_test, self.y_test)))
        print("Logistic regression recall score on test data: " + str(recall_score(self.y_test, preds)))
        print("Logistic regression precision score on test data: " + str(precision_score(self.y_test, preds))) # Prec = 1, recall = 0.68 means no false negatives, erring on the side of labelling 1 (high quality)    
    
        preds = self.xtrees.predict(self.X_test)
        print("Extra trees score on training data: " + str(self.xtrees.score(self.X_train, self.y_train)))
        print("Extra trees score on test data: " + str(self.xtrees.score(self.X_test, self.y_test)))
        print("Extra trees recall score on test data: " + str(recall_score(self.y_test, preds)))
        print("Extra trees precision score on test data: " + str(precision_score(self.y_test, preds)))

        
    #########################################################################
    # save results to pickled object TO DO: consider removing data first
    def save(self):    
        import pickle
        with open(self.qualityPredictorFile, 'wb') as f:
            pickle.dump(self,f)
    
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
        # first find the matrix indices of each distance, sorted in ascending order
        d2 = distances.reshape(len(self.f1)*len(self.f2),1)
        x2 = np.argsort(d2,axis=0)
        i1 = x2/len(self.f2)
        i2 = np.remainder(x2,len(self.f2))
        # determine those above threshold
        t = self.featSpaceScores > thresh
        t3 = t[i1,i2]
        f1_temp = np.multiply(self.f1[i1],t3)
        f2_temp = np.multiply(self.f2[i2],t3)
        f1_indices = []
        f2_indices = []      
        # make a list of the sorted above threshold indices in the original distances matrix 
        for f in range(len(f1_temp)):
            if f1_temp[f] != 0:
                f1_indices.append(f1_temp[f][0])
                f2_indices.append(f2_temp[f][0])
        return f1_indices,f2_indices        
                

         
