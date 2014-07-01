# -*- coding: utf-8 -*-
"""
learnWikipediaPageQuality.py
Created on Wed Jun 11 17:16:22 2014
Learn to predict the quality of Wikipedia pages

@author: ahna
"""

import pandas as pd
import numpy as np
import sklearn
import sklearn.linear_model
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.metrics import recall_score, precision_score
import pickle
import qualPred
#from app.helpers.qualPred import qualPred
#from qualityPredictor import qualPred
from database import *

#configFileName = '/home/ubuntu/wikiphilia/app/settings/development.cfg'
configFileName = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/app/settings/development.cfg'

def optimizeRegConstant(logres):
    # determine regularization constant. TO DO: make it so it returns best C. also might need to save and restore original C
    Cs = np.linspace(0.01,0.6,20)
    scores = []
    for c in Cs:
        logres.set_params(clf__C=c).fit(X_train, y_train)
        scores.append(logres.score(X_test,y_test))
    print(np.array([Cs,scores]))
    plt.plot(Cs,scores)


def main():
    qp = qualPred.qualPred() 
    
    ##############################################
    # file names
    debug, host, port, user, passwd, dbname, localpath = grabDatabaseSettingsFromCfgFile(configFileName)
    conn = conDB(host,dbname,passwd,port, user)	
    #featured_csvfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/featured.csv'
    #flagged_csvfilename = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/datasets/flagged.csv'
    #qualityPredictorFile = '/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/data/qualityPredictor.p'
    qualityPredictorFile = localpath + 'app/qualityPredictorFile.p'
        
    ##############################################
    # load data from CSV file
#    featuredDF = pd.DataFrame().from_csv(featured_csvfilename) # load existing dataframe from file and append to it
#    flaggedDF = pd.DataFrame().from_csv(flagged_csvfilename) # load existing dataframe from file and append to it
#    flaggedDF['featured']=False
#    featuredDF['flags']='NA'
#    featuredDF['flagged']=0
#    featuredDF['featured']=True
#    DF = pd.concat([featuredDF,flaggedDF])

    ##############################################
    # load data from database
    import pandas.io.sql as psql
    #conn = conDB(host,dbname,passwd=passwd,port=port, user=user)
    DF = psql.frame_query("SELECT * FROM training2", conn)
    closeDB(conn)

    ##############################################
    # set up data matrices
    #useFeatures = [ 'meanSentLen','meanWordLength','medianSentLen','medianWordLength','nChars','nImages','nLinks','nRefs',\
    #'nSections', 'nSents', 'nWordsSummary']
#    useFeatures = ['meanWordLength','nImages','nLinks','nRefs','nSections','nSents', 'nWordsSummary']
    DF = DF[~np.isnan(DF.meanWordLength)] # remove rows with NaN in meanWordLength
    DF = DF[~np.isnan(DF.reading_ease)] # remove rows with NaN in reading_ease  
    X = DF[qp.iUseFeatures].values #.astype('float')
    #X_scaled = preprocessing.scale(X) # feature normalization, save normalization info!
    
    # labels are 1 if featured is True, 0 if flagged is True
    y = DF['score'].values
    
    ##############################################
    # divide into training set and test set
    np.random.seed()    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=qp.testPropor, train_size=1-qp.testPropor, random_state=np.random.random_integers(100))

    ##############################################
    qp.rfclf = RandomForestClassifier(n_estimators=10) #look at feature_importances_
    qp.randfor = Pipeline([("scaler", preprocessing.StandardScaler()), ("clf", qp.rfclf)])
    qp.randfor.fit(X_train, y_train)
    print qp.randfor.score(X_test, y_test)
    for i in range(len(qp.iUseFeatures)):
        print qp.iUseFeatures[i], qp.rfclf.feature_importances_[i]
        
    ##############################################
    # build learning pipeline for logistic regression
    qp.logres_clf = sklearn.linear_model.LogisticRegression(C=0.35) 
    qp.logres = Pipeline([("scaler", preprocessing.StandardScaler()), ("clf", qp.logres_clf)])
    qp.logres.fit(X_train, y_train)
    qp.logres.score(X_test,y_test)

    ##############################################
    # build learning pipeline for logistic regression
    qp.xtrees_clf = sklearn.ensemble.ExtraTreesClassifier(n_estimators=10)
    qp.xtrees = Pipeline([("scaler", preprocessing.StandardScaler()), ("clf", qp.xtrees_clf)])
    qp.xtrees.fit(X_train, y_train)
    qp.xtrees.score(X_test,y_test)



    #qp.computeQualityOverFeatureGrid()
    
    ##############################################
    # save results
    from os import chdir
    #chdir('/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/')
    with open(qualityPredictorFile, 'wb') as f:
        pickle.dump(qp,f)
    
    print qp.logres_clf.raw_coef_
    #chdir('/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/app/')
    with open(qualityPredictorFile, 'rb') as f:
        qp2 = pickle.load(f)
    print("Found: " + str(qp2))

    ##############################################
    # print out accuracy, recall, precision on test set
    print("Random forest score on training data: " + str(qp.randfor.score(X_train, y_train)))
    print("Random forest score on test data: " + str(qp.randfor.score(X_test, y_test)))
    preds = qp.randfor.predict(X_test)
    print("Random forest Recall score on test data: " + str(recall_score(y_test, preds)))
    print("Random forest Precision score on test data: " + str(precision_score(y_test, preds)))

    print("Logistic regression Score on training data: " + str(qp.logres.score(X_train, y_train)))
    print("Logistic regression Score on test data: " + str(qp.logres.score(X_test, y_test)))
    preds = qp.logres.predict(X_test)
    print("Logistic regression Recall score on test data: " + str(recall_score(y_test, preds)))
    print("Logistic regression Precision score on test data: " + str(precision_score(y_test, preds)))
    # Prec = 1, recall = 0.68 means no false negatives, erring on the side of labelling 1 (high quality)    

    print("Extra trees score on training data: " + str(qp.xtrees.score(X_train, y_train)))
    print("Extra trees score on test data: " + str(qp.xtrees.score(X_test, y_test)))
    preds = qp.xtrees.predict(X_test)
    print("Extra trees Recall score on test data: " + str(recall_score(y_test, preds)))
    print("Extra trees Precision score on test data: " + str(precision_score(y_test, preds)))
    
    ##############################################
    # Print out which features matter and drop the ones that don't
    print "Random forest feature importances:"
    print qp.iUseFeatures
    print qp.rfclf.feature_importances_
    
    ##############################################
    # deploy to unlabelled data
    # for final app, ideally i'd compute this index on all of wikipedia
    #sklearn.linear_model.LogisticRegression.predict()    
    #sklearn.linear_model.LogisticRegression.predict()    
    return qp


if __name__ == '__main__': main()
