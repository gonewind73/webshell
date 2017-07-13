# coding:utf-8
'''
Created on 2017年5月4日

@author: heguofeng
'''

from numpy import mat
import unittest
import getopt
import pickle
import json
import time

from  webshell.basetool import ObservesState,getDataFromFile,saveDatatoFile
import sys
from itertools import compress

from webshell.fpgws import FPGrowthWebShell


class LinearEquationWebShell(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.states = ['wn']
        self.observes = {}
        self.trainObserves = []
        #self.trainMatrix = [[]]
        self.trainStates = []
        self.keyObserves = {}
        self.keyObserveProbs = []
        self.needRecalculate = True
        
    def getObserveIndex(self,observe):
        if observe not in self.observes.keys():
            self.observes[observe] = len(self.observes)
        return self.observes[observe]
        
    def train(self,observes,state):
        self.trainObserves.append(list(map(lambda ob:self.getObserveIndex(ob),observes)))
        self.trainStates.append(state)
        self.needRecalculate = True
        
    def saveModel(self,modelfilename="lewsmodel.pkl",code='pickle'):

        fw = open(modelfilename, 'wb')
        data = {
            "observes": self.observes,
            "trainObserves":self.trainObserves,
            "trainStates":self.trainStates,
            "keyObserves": self.keyObserves,
            "keyObserveProbs": self.keyObserveProbs,
            "needRecalculate":self.needRecalculate,
        }
        #print(data)
        if code == "json":
            txt = json.dumps(data)
            txt = txt.encode('utf-8').decode('unicode-escape')
            fw.write(txt)
        elif code == "pickle":
            pickle.dump(data,fw)
        fw.close()
        
    def loadModel(self, modelfilename="lewsmodel.pkl", code="pickle"):
        fr = open(modelfilename, 'rb')
        if code == "json":
            txt = fr.read()
            model = json.loads(txt)
        elif code == "pickle":
            model = pickle.load(fr)
        fr.close()
        
        self.observes = model["observes"]
        self.trainObserves = model["trainObserves"]
        self.trainStates = model["trainStates"]
        self.keyObserveProbs = model["keyObserveProbs"]
        self.keyObserves = model["keyObserves"]
        self.needRecalculate= model["needRecalculate"]
        
    @staticmethod
    def getObservesBySelector(originObserves,originObserveLists,selector):     
        indexmap={}
        oldindex = newindex = 0
        
        for s in selector:
            if s == 1 :
                indexmap[oldindex]=newindex
                newindex += 1
            oldindex += 1
        print(oldindex,newindex)
        
        oldindexlist=sorted(indexmap.keys())
        
        newObserves={}
        for ob,index in originObserves.items():
            if index in oldindexlist:
                newObserves[ob]=indexmap[index]
                
        newObserveLists = list(map(lambda r:list(compress(r,selector)),originObserveLists))
        return newObserves,newObserveLists
               
        
    def getProbs(self):
        if not self.needRecalculate:
            return self.keyObserveProbs
        
        trainObserveLists = []
        recordscount = len(self.trainObserves)
        #print(self.trainObserves)
        
        observeIndexlist=sorted(list(self.observes.values()))
        #print(observeIndexlist)
        
        '''
        count all
        '''
#         for i in range(0,len(self.trainObserves)):
#             trainObservelist=list(1 if x in self.trainObserves[i] else 0 for x in observeIndexlist)
#             trainObserveMatrix.append(trainObservelist)

        trainStateList = list(1 if s == 'w' else 0 for s in self.trainStates)
        trainObserveLists=list(map(lambda ob:list(1 if x in ob else 0 for x in observeIndexlist),self.trainObserves))
         
        
        #only 'w'

        wSelector=trainStateList[:]
        trainWObserveLists=list(map(lambda ob:list(1 if x in ob else 0 for x in observeIndexlist),compress(self.trainObserves,wSelector)))
        trainWStateList = list(filter(lambda s:s==1,trainStateList))  #filter 'w'

        #only 'n'
        nSelector = list(1 if s == 'n' else 0 for s in self.trainStates)
        trainNObserveLists=list(map(lambda ob:list(1 if x in ob else 0 for x in observeIndexlist),compress(self.trainObserves,nSelector)))
        trainNStateList = list(filter(lambda s:s==0,trainStateList))  #filter 'n'
            
        #all records        
        mySelectors = list(1 for x in range(len(self.trainObserves)))
        
        '''process optimal matrix
        '''
        #1 remove only one
#         sumMat=observesMat.sum(axis = 0) #colum
#         mySelectors=list(map(lambda r:1 if r>1 else 0,sumMat.tolist()[0]))
        
        #2 remove n have more 
        wObservesMat = mat(trainWObserveLists)
        wSumList = wObservesMat.sum(axis = 0).tolist()[0]
        nObservesMat = mat(trainNObserveLists)
        nSumList = nObservesMat.sum(axis = 0).tolist()[0]
        #print(wSumList,nSumList)
        if len(nSumList)==0:
            mySelectors = list(map(lambda r:1 if r>1 else 0,wSumList))
        else:
        # r[1] ob count in nState r[0] ob count in wState  r[0]>1 means less count is 2
#         mySelectors = list(map(lambda r:1 if r[1]<1 and r[0]>1 else 0,zip(wSumList,nSumList)))
            mySelectors = list(map(lambda r:1 if r[0]>1 else 0,zip(wSumList,nSumList)))
        #print("myselector",mySelectors)

        #calculate
        self.keyObserves,observeLists = LinearEquationWebShell.getObservesBySelector(self.observes,trainObserveLists,mySelectors)
        #observesMat=mat(list(map(lambda r:list(compress(r,mySelectors)),trainObserveLists)))
        observesMat = mat(observeLists)
        statesMat = mat(trainStateList).T
        #print(observeLists,trainStateList)
        observeProbsMat = observesMat.I * statesMat
        
        #3 remove negitive obs and recalculate
        #print(observeProbsMat.T.tolist()[0])
        for i in range(10):
            mySelectors = list(map(lambda r:1 if r > 0  else 0,observeProbsMat.T.tolist()[0]))
            self.keyObserves,observeLists = LinearEquationWebShell.getObservesBySelector(self.keyObserves,observeLists,mySelectors)
            observesMat = mat(observeLists)
            #statesMat = mat(trainStateList).T
            observeProbsMat = observesMat.I * statesMat
            if len(list(filter(lambda r:r<0,observeProbsMat.T.tolist()[0])))==0:
                break
        
#         newStatesMat = observesMat * observeProbsMat
#         print(sum(newStatesMat.T.tolist()[0]),newStatesMat.T.tolist()[0])
#         print(sum(statesMat.T.tolist()[0]),statesMat.T.tolist()[0])
        
        #save probs
        self.keyObserveProbs =list(map(lambda r:r[0], observeProbsMat.tolist()))
        self.saveProbToFile("obprobs.txt")

        self.needRecalculate = False
        return self.keyObserveProbs

    def saveProbToFile(self,filename):
        data=[]
        for key,value in self.keyObserves.items():
            data.append([key,self.keyObserveProbs[value]])
        data.sort(key=lambda r:r[1],reverse=True)
        saveDatatoFile(filename, data)
        return 
    
    def getPredict(self,observes):
        probs  =  self.getProbs()[:]
        probslen = len(probs)
        #probs.append([0])  #for notfound item =0
        #print(probs)
        prob  =  0
        keywords=""
        for ob in observes:
            obIndex = self.keyObserves.get(ob,-1)
            #print(obIndex)
            if obIndex != -1:
                prob +=  probs[obIndex]
                keywords += "," + ob
        #print("keywords",keywords)
        #print(prob)
        if prob>0.5:
            return 'w',prob,keywords
        else:
            return 'n',prob,keywords
        pass
            
def trainLEWebShell(samplefilename,statefilename,modelfilename="lew.pkl",code="pickle"):
    starttime=time.time()
    trainrecords=getDataFromFile(samplefilename)
    staterecords=getDataFromFile(statefilename)
    if len(trainrecords) != len(staterecords):
        print("statefile length (%d) is not equal samplefile (%d).Quit!"%())
    webshellcount=len(list(filter(lambda r:r[1]=='w',staterecords)))
    print("start train with %s and statesfile %s , total %d records with %d webshells." %( samplefilename,statefilename,len(trainrecords),webshellcount))
        
    os1 = ObservesState()
    os2 = ObservesState()
    lews = LinearEquationWebShell()
    for record in trainrecords:
        observes=os1.getObservesFromRecord(record)
        state=os2.getStateFromRecord(record)
        lews.train(observes, state)
    
    #lews.saveModel(modelfilename, code)
    lews.getProbs()
    lews.saveModel(modelfilename, code)
    
    print("training used %f second."%(time.time()-starttime))
    
    return

def trainLEWithKeywords(keywordsfilename,modelfilename="lew.pkl",code="pickle"):
    starttime=time.time()
    
    fpgws = FPGrowthWebShell()
    fpgws.loadModel(keywordsfilename, code=code)
    
    webshellcount=sum(list(map(lambda r:r[1][1],fpgws.keywordsDict.items())))
    print("start train with keywords  %s total %d webshells." %( keywordsfilename,webshellcount))

    lews = LinearEquationWebShell()
    for kws in fpgws.keywordsDict:
        count = fpgws.keywordsDict[kws][1]
        observes = list(kws)
        #print(observes)
        state = 'w'
        for i in range(count):
            lews.train(observes, state)
    
    #lews.saveModel(modelfilename, code)
    lews.getProbs()
    lews.saveModel(modelfilename, code)
    
    print("training used %f second."%(time.time()-starttime))
    
    return

def predictLEWebShell(inputfilename,statefilename,modelfilename="lew.pkl",code="pickle",idlist=[]):

    starttime=time.time() 
    
    lews = LinearEquationWebShell()
    lews.loadModel(modelfilename, code)
    #print(lews.observes,lews.trainStates)
    statelist = []
    stateproblist = []
    
    if len(idlist) == 0 :
        records=getDataFromFile(inputfilename)
        verbose = False  
    else:
        records=getDataFromFile(inputfilename,lambda r:r[0] in idlist)
        verbose = True       
    print("start find webshell in  %s total %d records"%(inputfilename,len(records)))
    obs1 = ObservesState()

    for record in records:
        observes = obs1.getObservesFromRecord(record)

        state,prob,keywords = lews.getPredict(observes)
        statelist.append([record[0],state])
        stateproblist.append([record[0],state,prob])
        if verbose :
            print(observes,state,prob,keywords)
    #print(statelist)
    count = saveDatatoFile(statefilename, statelist,lambda r:r[1]=='w')
    countprob = saveDatatoFile(statefilename+".prob", stateproblist,lambda r:r[1]=='w')
    print("find %d webshells in %s .result saved in %s."%(count,inputfilename,statefilename))
    print("end of LE judge use %f second. "%(time.time()-starttime))

    

class TestLEWebShell(unittest.TestCase):
    def setUp(self):
        print('Start test LEWebshell...')
 
    def tearDown(self):
        print( 'end LEWebshell Test...')
        
    def test_WebShellKeyword(self):
        
        return 
                   
if __name__  ==  '__main__':
    
    opts,args = getopt.getopt(sys.argv[1:],"hi:o:s:m:l:tpk",
                              ["help","inputfile","outputfile","statefile",
                               "modelfile","list","train","predict","trainwithkeywords"])
    if len(opts) == 0:
        opts.append(("-h",""))
        
    inputfilename = "input.txt"
    outputfilename = "output.txt"
    statefilename = "state.txt"
    modelfilename = "model.pkl"
    idlist=[]
    
    for op,value in opts:
        if op == "-h" or op == "--help" :
            print("LinearEquation WebShell version 1.0.by Heguofeng")
            print('''
-h --version :help this information.
-i inputfilename
-o outputfilename
-s statefilename
-m modelfilename
-l id1[,id2]
-t :train
-p :predict
-k : trainwithkeywords
                ''')
        if op == "-i" or op == "--input":
            inputfilename = value
        if op == "-o" or op == "--output":
            outputfilename = value
        if op == "-s" or op == "--output":
            statefilename = value
        if op == "-m" or op == "--output":
            modelfilename = value
        if op == "-l" or op == "--list":
            idlist = list(value.strip().split(","))
        if op == "-t" or op == "--train":
            trainLEWebShell(samplefilename = inputfilename,
                            statefilename = statefilename,
                            modelfilename = modelfilename)
        if op == "-k" or op == "--trainwithkeywords":
            trainLEWithKeywords(keywordsfilename = inputfilename,
                            modelfilename = modelfilename)
        if op == "-p" or op == "--predict":
            predictLEWebShell(inputfilename = inputfilename,
                            statefilename = statefilename,
                            modelfilename = modelfilename,
                            idlist = idlist )
    