# coding:utf-8
'''
Created on 2017年4月29日

@author: heguofeng

1\ doTrain
2\
'''

import re
from base64 import b64decode
from urllib.parse import urlparse, parse_qsl, unquote
from webshell.hmm import HMModel
from webshell.basetool import *
import datetime
from itertools import repeat
import unittest
import time


STATES = {'w', 'n', }


class KeywordPredict(object):
    '''
    classdocs
    '''

    def __init__(self):
        #self.keywords={}  #{key:prob}}
        self.keywords={"op=systeminfo":1,"aG8o":1,"ZWNo":1,"Y2hv":1,"a=Files":1,"shell":1,
                          "z0=":1,"z1=":1,"System":1,"fileName=":1,
                          "web.xml":1,"b4che10rpass":1,"anD%2053":1}
        pass
    
    def addKeyWords(self,keywords):
        for key,value in keywords:
            self.keywords[key]=value
        pass
    
    def findHasKey(self,data):
        prob=0
        for key in knownkeywords:
            if data.find(key)>=0:
                prob += knownkeywords[key]
                if prob>=1:
                    return True
        return False

    def findWebShell(self,inputfilename,outputfilename):
        myfile=open(inputfilename,'r')
        mylines=myfile.readlines()
        myfile.close()
        
        myfilew=open(outputfilename,"w")
        myfilew.write("ID,FLAG\n")
        webshellrecords=filter(self.findHasKey,mylines)
        count=0
        for wr in webshellrecords:
            record=getRecordFromLine(wr)
            count+=1
            myfilew.write("%s,w\n"%(record[0]))
        #print(count)
        myfilew.close()

        return count
     
    def splitAndDecode(self):
        mydata=getDataFromFile("subject2_sample.txt")
        filtereddata=[]
        urldecodeddata=[]
        filtereddata=filter(lambda d:d[1]=='w',mydata)
        print(len(filtereddata))
        for d in filtereddata:
            urldecodeddata.append(map(lambda d:unquote(d),d))
            #print(urldecodeddata)
        print(filtereddata[0])
        print(urldecodeddata[0])
        myfile=open("decodesample.txt","w")
        #for record in filter(lambda h:h[0]=='1016096',urldecodeddata):
        for record in urldecodeddata:
            dumpstring=""
            for data in record:
                 dumpstring += data + ","
            dumpstring +="\n"   
            #print(dumpstring)
            myfile.writelines(dumpstring)
        myfile.close()
        return

    def splitword(self,datastring):
        words=[]
        return words
       
    def train(self,filename):

        return
    
    def decodeBase64(self,base64string):
        
        return str
    
    def doTrainning(self,observe,states):
        
        return 
    
    def doPredict(self,observe):
        stauts=""
        return stauts
 
def judgeWebShellByKeywords(inputfilename,outputfilename):
        mydata0=getDataFromFile(inputfilename)
        #print("found %d webshells in %s by tag origin:"%(len(mydata0),inputfilename))
        sp=KeywordPredict()
        count=sp.findWebShell(inputfilename,outputfilename)
        print("found %d webshells in %s by keywords. result saved into %s."%(count,
                                                                              inputfilename,
                                                                              outputfilename))
        return count
           

# def getObservesAndStatesFromRecord(record): 
#     observes=getObservesFromRecord(record)
#     
#     states=[]
#     states.extend(repeat(record[1],len(observes)))
# 
#     return observes,states
# 
# def getObservesFromItem(item):
#     observes=[]
#     if len(item)>32:
#         try:
#             decoded=b64decode(re.sub(r'\s','',item))
#             words=re.findall(r'\w+',decoded)
#             observes.extend(map(lambda w:"b64_"+w,words))
# #             decoded=b64decode(item)
# #             observes.append("base64code")
# #             observes.extend(getKeywords(item))
# #             observes.append(item)
#         except Exception:
# #             observes.append(item)
#             words=re.findall(r'\w+',item)
#             observes.extend(words)
#     else:
# #         observes.append(item)
#         words=re.findall(r'\w+',item)
#         observes.extend(words)
#     return observes
# 
# def getObservesFromRecord(record): 
# 
#     observes=[]
#     parastring=""
#     hasState=0
#     if record[1] in "wn":
#         hasState=1
#     recordlen=len(record)
# 
#     
#     if recordlen>2+hasState:
#         urlitems=urlparse(record[1+hasState])
#         observes.append(urlitems[1])
#         observes.append(urlitems[2])
#     #observes.extend(getObservesFromItem(urlitems[1])
#     if recordlen>=3+hasState:
#         parastring=record[3+hasState-1]
#         for i in range(3+hasState,recordlen):
#             parastring+=record[i]
#     
#         observes.extend(map(lambda w:"kw_"+w,getKeywords(parastring)))
#         
#         parameters=parse_qsl(parastring)
#         if len(parameters)==0:
#             observes.extend(getObservesFromItem(parastring))
#                            
#         for key,value in parameters:
#             observes.append(key+"="+value)
#             observes.extend(getObservesFromItem(key))
#             observes.extend(getObservesFromItem(value))
#     
#     #observes = list(set(observes)) #去重
#     #print(observes)
#     observes = list(filter(lambda h:len(h)>0,set(observes)))
#     #print(observes)
# #     for ob in observes:
# #         print(ob)
#     
#     
#     return observes
#     #return filter(lambda ob:len(ob)>1,observes)  #get off nomeaning obs

class HMMWebShell(HMModel):

    def __init__(self, *args, **kwargs):
        HMModel.__init__(self)
        self.states = STATES
        self.data = None
        self.obs=ObservesState(mode=3)


    def load_data(self, filename):
        self.data=getDataFromFile(filename)
        return self.data

    
    def train(self,trainfilename="",statesfilename=""):
        '''
        trainfile: id,w,httpurl,data or id,httpurl,data
        statesfile: id,w 
        '''
        
        if not self.inited:
            self.setup()
        
        if len(trainfilename)>0:
            trainRecords=getDataFromFile(trainfilename)
        else:
            return
            
        if len(statesfilename)>0:
            statesDict=getDataFromFile(statesfilename)
        else:
            statesDict=dict((r[0],r[1]) for r in trainRecords)

        # train
        for record in trainRecords:
            # pre processing
            if record[0] in statesDict:
                state=statesDict[record[0]]
            else:
                state='n'
            observes=self.obs.getObservesFromRecord(record)
            states=[]
            states.extend(repeat(state,len(observes)))
            self.do_train(observes, states)

    def judge(self, record,retrain=False):
        try:
            observes=self.obs.getObservesFromRecord(record)
            states,prob = self.do_predict(observes)
            if retrain:
                self.do_train(observes, states)
            #return judge_sent(record, states)
            #print(record[0],states[-1],prob)
            result=True if states[-1]=='w' else False
            return result,prob
        except:
            return False,0.5


    def test(self,record):

        result = self.judge(record)
        pass

def judgeWebShell(inputfilename,modelfilename="webshell.pkl",statefilename="result.txt",id=""):
    
    ws=HMMWebShell()
    ws.load(filename=modelfilename, code="pickle")

    starttime=time.time() 

    if id=="":
        mydata0=getDataFromFile(inputfilename)
    else:
        mydata0=getDataFromFile(inputfilename,lambda r:r[0]==id)   
    print("start find webshell in  %s total %d records"%(inputfilename,len(mydata0)))
    count=0 
    outputfile=open(statefilename,"w")
    outputfile2=open(statefilename+".prob","w")
    outputfile2.write("ID,FLAG,PROB\r\n")
    outputfile.write("ID,FLAG\r\n")

    for line in mydata0:
        #isWebShell,prob=ws.judge(line,retrain=True)
        isWebShell,prob=ws.judge(line,retrain=False)
        if isWebShell:
            count+=1
            outputfile2.write("%s,w,%e\r\n"%(line[0],prob))
            outputfile.write("%s,w\r\n"%(line[0]))

    outputfile.close()
    outputfile2.close()
           
    print("find %d webshells in %s .result saved in %s."%(count,inputfilename,statefilename))
    print("end of HMM judge use %f second. with retrain"%(time.time()-starttime))

    return count

def trainWebShell(samplefilename,statefilename,modelfilename="webshelltrain.pkl"):
    starttime=time.time()
#     samplestatefilename="../result.txt"
#     samplefilename="../filelist_A.txt"
    records=getDataFromFile(statefilename, lambda r:r[1]=='w')
    print("start train with %s and statesfile %s has %d webshells." %( samplefilename,statefilename,len(records)))
    ws=HMMWebShell()
    if samplefilename!="data/subject2_sample.txt":
        ws.train("data/subject2_sample.txt")
    ws.train(samplefilename, statefilename)
    print("training used %f second."%(time.time()-starttime))
    ws.save(code="pickle",filename=modelfilename)
    return 


class TestWebShell(unittest.TestCase):
    def setUp(self):
        print('Start test Webshell...')
 
    def tearDown(self):
        print( 'end Webshell Test...')
        
    def test_WebShellKeyword(self):
        judgeWebShellByKeywords(inputfilename="filelist_B.txt", 
                                outputfilename="data/kwresult.txt")
        return 
        
    def test_WebShell(self):
        trainWebShell(samplefilename="data/subject2_sample.txt",
                       samplestatefilename="data/subject2_sample.txt",
                       trainfilename="data/webshelltrain.pkl")
        judgeWebShell(inputfilename="data/subject2_sample.txt", 
                      trainfilename="data/webshelltrain.pkl", 
                      outputfilename="data/result.txt")
        compareWebShell("data/subject2_sample.txt","data/result.txt")

        return 
   
    def test_readtestfile(self):
        ws=HMMWebShell()
        ws.load(filename="webshell.pkl", code="pickle")
        myfile=open("../filelist_A.txt",'r')
        lines=myfile.readlines(5000000)
        myfile.close()
        
        print("start find webshell in  filelist_A.txt with retrain")
        starttime=time.time()
        
        testcount=500
        
        count=0
        for i in range(testcount):
            record=getRecordFromLine(lines[i])
            #isWebShell,prob=ws.judge(record)
            isWebShell,prob=ws.judge(record,retrain=True)
            if isWebShell:
                count+=1
#                 #print(record[0],'w',prob,record[1],record[2])
#             else:
#                 #print(record[0],'n',prob)
        print("find %d webshells in filelist_A.txt in first %d lines ."%(count,testcount))
        print("end of HMM judge use %f second. with retrain"%(time.time()-starttime))       
        ws.save(filename="hmmwebshellr.pkl",code="pickle")

        starttime=time.time()
        count=0    
        for i in range(testcount):
            record=getRecordFromLine(lines[i])
            isWebShell,prob=ws.judge(record)
            if isWebShell:
                count+=1
                #print(record[0],'w',prob,record[1],record[2])
#             else:
#                 print(record[0],'n')
        print("find %d webshells in filelist_A.txt in first %d lines after retrain."%(count,testcount))
        print("end of HMM judge use %f second. without retrain"%(time.time()-starttime)) 
        return 
            
    def test_certfile(self):
        judgeWebShell(inputfilename="filelist_A.txt",
                       trainfilename="webshell/webshellmt.pkl",
                        outputfilename="result.txt")
        return 
    

if __name__  ==  '__main__':
    
    opts,args = getopt.getopt(sys.argv[1:],"hi:o:s:m:l:tp",
                              ["help","inputfile","outputfile","statefile",
                               "modelfile","list","train","predict"])
    if len(opts) == 0:
        opts.append(("-h",""))
        
    inputfilename = "input.txt"
    outputfilename = "output.txt"
    statefilename = "state.txt"
    modelfilename = "model.pkl"
    idlist=[]
    
    for op,value in opts:
        if op == "-h" or op == "--help" :
            print("HMM WebShell version 1.0.by Heguofeng")
            print('''
-h --version :help this information.
-i inputfilename
-o outputfilename
-s statefilename
-m modelfilename
-l id1[,id2]
-t :train
-p :predict
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
            trainWebShell(samplefilename = inputfilename,
                            statefilename = statefilename,
                            modelfilename = modelfilename)
        if op == "-p" or op == "--predict":
            judgeWebShell(inputfilename = inputfilename,
                            statefilename = statefilename,
                            modelfilename = modelfilename)
    
#     observes=[]
# 
#     
#     hasState=0
#     if record[1] in "wn":
#         hasState=1
#     if len(record)<3+hasState:
#         return observes,states
#     
# #     urlitems=urlparse(record[1+hasState])
#     parameters=parse_qsl(record[2+hasState])
# 
# 
# 
# #     observes.append(urlitems[1])
# #     observes.append(urlitems[2])
#                
#     for key,value in parameters:
#         observes.append(key)
#         if len(value)>16:
#             try:
#                 decoded=b64decode(value)
#                 words=re.findall(r'\w+',decoded)
#                 observes.extend(words)
#             except Exception:
#                 observes.append(value)
#         else:
#             observes.append(value)
#     
#     filterobs=filter(lambda ob:len(ob)>1,observes) 

#             #print(record)
#             state=record[1]
#             #print(state)

# 
#             observes=[]
#             urlitems=urlparse(record[2])
#             
#             parameters=parse_qsl(record[3])
#             #print(urlitems,parameters)
#             observes.append(urlitems[1])
#             observes.append(urlitems[2])
#                         
#             for key,value in parameters:
#                 #print(key,value)
#                 observes.append(key)
#                 if len(value)>16:
#                     try:
#                         decoded=b64decode(value)
#                         words=re.findall(r'\w+',decoded)
#                         observes.extend(words)
#                     except Exception:
#                         observes.append(value)
#                 else:
#                     observes.append(value)
