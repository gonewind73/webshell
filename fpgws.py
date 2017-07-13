'''
Created on 2017年5月12日

@author: heguofeng
'''
import pickle
import json
from webshell.freqitems import  getKeywordsByApriori, FPGrowth
from webshell.basetool import ObservesState, getDataFromFile, saveDatatoFile
import time
import getopt
import sys



class FPGrowthWebShell(object):
    '''
    classdocs
    '''


    def __init__(self,fpgkeywordsDict={},obsmode = 0,minSupport = 4):
        '''
        Constructor
        fpgkeywordsDict= [{kw1_1,...kw1_n}:[prob,used],... {kw2_1,...kw2_n}:[prob,used]]
        '''
        self.keywordsDict = fpgkeywordsDict
        self.obs = ObservesState(mode = obsmode)
        self.minSupport = minSupport

        
    def loadModel(self, filename="keywords.pkl", code="pickle"):
        if code == "json":
            fr = open(filename, 'r')
            txt = fr.read()
            kwsl = json.loads(txt)["keywordsDict"]
            self.keywordsDict  = dict(map(lambda kw:(frozenset(kw[0]),kw[1]),kwsl))
        elif code == "pickle":
            fr = open(filename, 'rb')
            
            data = pickle.load(fr)
            self.keywordsDict = data["keywordsDict"]
#             data = pickle.load(fr)
#             self.keywordsList = data[keywordsList]
        fr.close()
    
    def saveModel(self, filename="keywords.pkl", code="pickle"):
        ''' 
        json format
        {"keywordsDict": [
                            [['HOME', 'C'],[16, 0]]
                            ...
                            [['HOME', 'C'],[16, 0]]
                        ]
        }
        
        pickle format:
        {"keywordsDict": [
                            [frozenset('HOME', 'C'):[16, 0]]
                            ...
                            [frozenset('HOME', 'C'):[16, 0]]
                        ]
        }
        '''

        data = {
            "keywordsDict": self.keywordsDict,
        }
        if code == "json":
            kwsl = list(map(lambda kw:(list(kw[0]),kw[1]),self.keywordsDict.items()))
            txt = json.dumps({"keywordsDict": kwsl})
            txt = txt.encode('utf-8').decode('unicode-escape')
            fw = open(filename, 'w')
                    
            fw.write(txt)
        elif code == "pickle":
            fw = open(filename, 'wb')
            pickle.dump(data, fw)
        fw.close()
        
    def loadDataFromFile(self,filename,filterfunction=lambda r:r[1]=='w'):
        records=getDataFromFile(filename,filterfunction)
        dataSet = []
        for record in records:
            dataSet.append(self.obs.getObservesFromRecord(record))
        print("record count",len(dataSet))
        return dataSet
    
    def moreTrain(self,inputfilename="",statesfilename=""):
        
        self.needReCalculate = True
    
    def train(self,inputfilename="",statesfilename="",modelfilename = ""):
        '''
        if has statesfilename will use states  
        if have modelfilename will add train
        '''
        print(time.time())
        if len(statesfilename) != 0:
            listrecords = getDataFromFile(statesfilename)
            ids = list(map(lambda r:r[0],listrecords))
            filterfunction = lambda r:r[0] in ids
        else:
            filterfunction = lambda r:r[1]=='w'
             
        myFPGrowth = FPGrowth(minSupport=self.minSupport)
        records = self.loadDataFromFile(inputfilename,filterfunction=filterfunction)
        if len(modelfilename) == 0:
            myFPGrowth.loadData(records)
        else:
            self.loadModel(modelfilename, code = "pickle")
            dataset = dict(map(lambda kws: (kws[0],kws[1][0]),self.keywordsDict.items()))
            dataset.update(myFPGrowth.createInitSet(list(map(lambda r : self.obs.getObservesFromRecord(r),records))))
            myFPGrowth.loadDataSet(dataset)
        print("itemcount:",len(myFPGrowth.getItems(myFPGrowth.dataSet)))
        myFPGrowth.createTree()
        #myFPGrowth.rootTree.disp(1)
        #HeadNode.disp(myFPGrowth.headerTable)
        print("headlen",len(myFPGrowth.headerTable))
        freqItems = myFPGrowth.getFreqItems()
        print("getFreqItems:",len(freqItems))
        
        
        self.keywordsDict = dict(sorted(map(lambda fi:(frozenset(fi[0]),[fi[1],0]),freqItems),key=lambda wk:len(wk[0]),reverse = True))
        #print(self.keywordsDict)
        print(len(self.keywordsDict))
         
        self.verify(inputfilename, statesfilename)
        print("after verify",len(self.keywordsDict))
        
        self.saveModel("keywords.txt", code = "json")

        return self.keywordsDict
    
    def addKeywords(self,kwsfilename):
        ''' just like model file
        {"keywordsDict": [
                            [['HOME', 'C'],[16, 0]]
                            ...
                            [['HOME', 'C'],[16, 0]]
                        ]
        '''
        fr = open(kwsfilename, 'r')
        txt = fr.read()
        kwsl = json.loads(txt)["keywordsDict"]
        self.keywordsDict.update(dict(map(lambda kw:(frozenset(kw[0]),kw[1]),kwsl)))
#         kwsfile = open(kwsfilename,"rt")
#         kwslines = kwsfile.readlines()
#         kwsfile.close()
#         for line in kwslines:
#             keywords = re.findall(r'\{(.*?)\}',line)
#             probs  = re.findall(r'\[(.*?)\]',line)
        pass
            
        
    def verify(self,inputfilename,statesfilename=""):
        if len(statesfilename) != 0:
            listrecords = getDataFromFile(statesfilename)
            ids = list(map(lambda r:r[0],listrecords))
            filterfunction = lambda r:r[0] in ids
            states = listrecords
        else:
            filterfunction = lambda r:True
            states = getDataFromFile(inputfilename,filterfunction=filterfunction)
            
        records =  getDataFromFile(inputfilename,filterfunction=filterfunction)

        keywordsList = sorted(self.keywordsDict.keys(),key=lambda k:len(k),reverse=True)
        #print(keywordsList)
        for i in range(len(records)):
            observes = self.obs.getObservesFromRecord(records[i])
            state = 'n'
            for kws in keywordsList:
                if kws.issubset(observes):
                    if states[i][1]=='n':
                        #print("%s can't correct tagto n! obs %s,remove %s"%(records[i][0],str(observes),str(kws)))
                        self.keywordsDict[kws][1] = -1
                    else:
                        state = 'w'
                        self.keywordsDict[kws][1] += 1
                        break
            for kws in list(self.keywordsDict.keys()):
                if self.keywordsDict[kws][1] == -1:
                    del self.keywordsDict[kws]
                    keywordsList.remove(kws)                
        
            if states[i][1]!= state:
                print("%s can't correct tagto %s ! obs %s"%(records[i][0],states[i][1],str(observes)))
                
        for kws in list(self.keywordsDict.keys()):
            if self.keywordsDict[kws][1] == 0:
                del self.keywordsDict[kws]
                keywordsList.remove(kws)                
                

    def predict(self,observes,verbose = False):
        try:
            obsSet=set(observes)
            keywordsList = sorted(self.keywordsDict.keys(),key=lambda k:len(k),reverse=True)
            for kws in keywordsList:
                if kws.issubset(obsSet):
                    if verbose:
                        print("obs %s match keywords:%s"%(observes,kws))
                    return 'w',1,kws
            return 'n',1,set([])
        except:
            return 'n',0.5,set([])
        
def trainWebShellByFPGrowth(inputfilename,modelfilename="keywords.pkl",statefilename="result.txt"):
    #minsup=[25,20,10,6,4]
    minsup=[10]
    for i in range(len(minsup)):
        print("minsup",minsup[i])
        starttime=time.time() 
        fpgws = FPGrowthWebShell(obsmode= 0,minSupport= minsup[i])
        fpgws.train(inputfilename, statefilename)
        fpgws.saveModel(modelfilename, code="pickle")
        print("end of trainWebShellByFPGrowth use %f second. "%(time.time()-starttime))
            
            
            
def trainWebShellByFPGrowth2(inputfilename,modelfilename="keywords.pkl",statefilename="result.txt"):

    starttime=time.time() 
    fpgws = FPGrowthWebShell(obsmode = 0)
    fpgws.loadModel(modelfilename, code="pickle")
 
    print("end of trainWebShellByFPGrowth use %f second. "%(time.time()-starttime))
            
def predictUrlIsWebShellByFPGrowth(modelfilename = "fpgws.pkl",code="pickle"):
    # this is for hive transform url 
    fpgws = FPGrowthWebShell(obsmode = 0)
    fpgws.loadModel(modelfilename, code=code)
    obs1 = ObservesState(mode = 0)

    for url in sys.stdin: 
        record = ["1","",url]
        observes = obs1.getObservesFromRecord(record)
        #print(record,observes)
        state,prob,kws = fpgws.predict(observes,verbose=False)
        print("%s\t%d\t%s"%(state,prob,str(kws)))    
    
    
def predictWebShellByFPGrowth(inputfilename,modelfilename="keywords.pkl",statefilename="result.txt",idlist=[]):
    starttime=time.time() 

    fpgws = FPGrowthWebShell(obsmode = 0)
    fpgws.loadModel(modelfilename, code="pickle")
    
    #fpgws.addKeywords("mykeywords.txt")
    statelist = []
    stateproblist = []
    
    if len(idlist) == 0 :
        records=getDataFromFile(inputfilename)
        verbose = False  
    else:
        records=getDataFromFile(inputfilename,lambda r:r[0] in idlist)
        verbose = True       
    print("start find webshell in  %s total %d records"%(inputfilename,len(records)))
    obs1 = ObservesState(mode = 0)

    for record in records:
        observes = obs1.getObservesFromRecord(record)
        if verbose:
            print(record[0],observes)
        state,prob,kws = fpgws.predict(observes,verbose=verbose)
        statelist.append([record[0],state])
        stateproblist.append([record[0],state,prob])

    count = saveDatatoFile(statefilename, statelist,lambda r:r[1]=='w')
    countprob = saveDatatoFile(statefilename+".prob", stateproblist,lambda r:r[1]=='w')
    print("find %d webshells in %s .result saved in %s."%(count,inputfilename,statefilename))
    print("end of FPG judge use %f second. "%(time.time()-starttime))
        
if __name__  ==  '__main__':
    
    opts,args = getopt.getopt(sys.argv[1:],"hui:o:s:m:l:tpa",
                              ["help","inputfile","outputfile","statefile",
                               "modelfile","list","train","predict","url"])
    if len(opts) == 0:
        opts.append(("-h",""))
        
    inputfilename = ""
    outputfilename = ""
    statefilename = ""
    modelfilename = ""
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
-a : apriori find keywords
-f : fp_growth find keywords
-u : url from stdin
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

        if op == "-a" or op == "--apriori":
            getKeywordsByApriori(
                            modelfilename = modelfilename,
                            idlist = idlist )            
        if op == "-t" or op == "--fpgrowth":
            trainWebShellByFPGrowth(
                            inputfilename = inputfilename,
                            modelfilename = modelfilename,
                            statefilename = statefilename,
                            )            
        if op == "-p" or op == "--predict":
            predictWebShellByFPGrowth(
                            inputfilename = inputfilename,
                            modelfilename = modelfilename,
                            statefilename = statefilename,
                            idlist = idlist
                            ) 
        if op == "-u" or op == "--url":
            predictUrlIsWebShellByFPGrowth(
                            modelfilename = modelfilename,
                            )             