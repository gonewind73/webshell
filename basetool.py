'''
Created on 2017年5月5日

@author: heguofeng
'''
from urllib.parse import urlparse, parse_qsl, unquote
from math import ceil, floor
from itertools import repeat
from base64 import b64decode
import re
import getopt
import sys
from email.generator import DecodedGenerator

knownkeywords={"op=systeminfo":1,"a=Files":1,"shell":1,"_POST":1,
                      "z0=":1,"z1=":1,"z2=":1,"System":1,"fileName=":1,
                      "p1=":1,"p2=":1,"z9=":1,"z9=BaSE64_dEcOdE":1,
                      "web.xml":1,"b4che10rpass":1,"eval":1,
                      "aG8o":1,"ZWNo":1,"Y2hv":1,  #echo( 
                      "aW5p":1,"bmlf":1,"aV9z":1,  #ini_s
                      "c2V0":1,"ZXRf":1,"dF90":1,   #set_t
                      "Zm9w":1,"b3Bl":1,"cGVu":1,  #fopen
                      "X1BP":1,"UE9T":1,"T1NU":1,  #_POST
                      "Zndy":1,"d3Jp":1,"cml0":1,  #fwrite
                      "QGluaV9zZXQo":1,         #@ini_set(
                      "__VIEWSTATE=dDw":1,"_POS":1,
                      "%271%27%3D%271":1,"smoking=":1,
                      "%20anD%20":0.5,"type=downDb":1,
                      "%20anD%2053%3D53%20%":1,
                      "envlpass":1,
                      "FolderPath":1,
                      "u=../":1,
                      "Action=":1,
                      "port=":1,
#                       "&_=":0.5,
#                       "pass=":0.5,
                      "file=C%3A%7Call%7C00999%2Easp":1,
                      "adminpass=hhunter":0.5,
                      "filE=.user.ini":1,
                      "p1=mkdir":1,
                      "netstat":1,
                      "ZSnXu=Login":1,
                      "web.config":1,
                      "Execute":1,
                      }

def getKeywords(item):
                        
    keywords=[]
    for keyword in knownkeywords.keys():
        if item.upper().find(keyword.upper())>=0:
                keywords.append(keyword)
    return keywords

def getRecordFromLine(line,urlsafe):
    
    fields=line.strip().split(",")
    if len(fields)<2:
        #print(line)
        return []
    record=[]
    if urlsafe:
        record.extend(map(lambda d:unquote(d.strip()),fields))
    else:
        record.extend(fields)
    return record

def getDataFromFile(filename,filterfunction=lambda r:True,urlsafe=True):
    myfile=open(filename,'r',encoding='UTF-8')
    mylines=myfile.readlines()
    myfile.close()
 
    mydata=[]
    for line in mylines:
        record=getRecordFromLine(line,urlsafe)
        if len(record)!=0:
            mydata.append(record)
    #print("%d record read from %s"%(len(mydata),filename))     
    return list(filter(filterfunction,mydata))   

def saveDatatoFile(outputfilename,data,filterfunction=lambda r:True):
    myfile=open(outputfilename,"wt")
    #for record in filter(lambda h:h[0]=='1016096',urldecodeddata):
    myfile.write("ID,FLAG\n")
    count=0
    for record in filter(filterfunction,data):
        #decoded=list(map(lambda d:unquote(d),record))
        decoded=record[:]
        dumpstring=""
        for field in decoded:
            dumpstring += str(field) + ","
        dump=dumpstring[:-1]
        dump+="\n"   
        #print(dump)
        myfile.write("%s"%(dump))
        count += 1
    myfile.close()
    return count

def joinWebShell(originfilename,resultfilename,joinedfilename,method="add"):
    bothids,moreids,lessids = compareWebShell(originfilename, resultfilename)
    
    print(method)
    fw=open(joinedfilename,'w')
    fw.write("ID,FLAG\n")
    
    if method=="add":
        for r in bothids:
            fw.write("%s,w\n"%(r))
        for r in moreids:
            fw.write("%s,w\n"%(r))
        for r in lessids:
            fw.write("%s,w\n"%(r))
        print("joined webshells %d"%(len(bothids)+len(moreids)+len(lessids)))
    elif method=="cross":
        for r in bothids:
            fw.write("%s,w\n"%(r))
        print("joined webshells %d"%(len(bothids)))
    elif method == "more":
        for r in moreids:
            fw.write("%s,w\n"%(r))
        print("joined webshells %d"%(len(moreids)))        
    elif method == "less":
        for r in lessids:
            fw.write("%s,w\n"%(r))
        print("joined webshells %d"%(len(lessids)))        
    fw.close()
    
    return

def compareWebShell(originfilename,resultfilename):
    originrecords=getDataFromFile(originfilename,lambda r:r[1]=='w')  
    resultrecords=getDataFromFile(resultfilename,lambda r:r[1]=='w')  
    #print(resultrecords)
    originrecordids=list(map(lambda r:r[0],originrecords))
    resultrecordids=list(map(lambda r:r[0],resultrecords))
    bothids=list(filter(lambda r:r in resultrecordids,originrecordids))
    moreids=list(filter(lambda r:r not in originrecordids,resultrecordids))
    lessids=list(filter(lambda r:r not in resultrecordids,originrecordids))
    
    print("find %d webshell in both file."%(len(bothids)))
    print("Error:find %d webshell in %s but not in %s"%(len(moreids),resultfilename,originfilename))
    print(list(filter(lambda r:moreids.index(r)<20,moreids)))
    print("Warning:find %d webshell in %s but not in %s"%(len(lessids),originfilename,resultfilename))
    print(list(filter(lambda r:lessids.index(r)<20,lessids)))
    
    return bothids,moreids,lessids

def safeB64Decode(item):
    try:
        newitem = item[:]
        for i in range((4-len(item)%4)%4):
            newitem +="="
        decoded=b64decode(re.sub(r'\s','+',newitem)).decode()  #byte to string
        return decoded
    except Exception:
        return item

class ObservesState(object):
    def __init__(self,mode = 3):
        self.mayStates = ['w','n']  #"" "w" "n"
        self.mode=mode # 0 splitword & base64decode  1+ key=value 2+ server + path   3+ keywords 
        self.empty()
        pass
    
    def empty(self):
        self.observes = []
        self.states=[]
        
    
    def getObservesAndStatesFromRecord(self,record): 
        self.getObservesFromRecord(record)
        self.states=list((repeat(self.getStateFromRecord(record),len(self.observes))))
        return self.observes,self.states
    
    def getObservesFromRecord(self,record):
        observes=[]
        parastring=""
        hasState=0
        if record[1] in self.mayStates:
            hasState=1
        recordlen=len(record)
    
        
        if recordlen>2+hasState & self.mode > 1:
            urlitems=urlparse(record[1+hasState])
#             observes.append(urlitems[1])
#             observes.append(urlitems[2])
        #observes.extend(getObservesFromItem(urlitems[1])
        if recordlen>=3+hasState:
            parastring=record[3+hasState-1]
            for i in range(3+hasState,recordlen):
                parastring+=record[i]
            
            if self.mode >2 :
                observes.extend(map(lambda w:"kw_"+w,getKeywords(parastring)))
            
            parameters=parse_qsl(parastring,keep_blank_values=True)
            if len(parameters)==0:
                observes.extend(self.getObservesFromItem(parastring))
                               
            for key,value in parameters:
                if self.mode > 0 and len(value) < 32 and len(key) < 32:
                    observes.append("eq_"+key+"="+value)
                #print(key,value)
                observes.extend(ObservesState.getObservesFromItem(key))
                observes.extend(ObservesState.getObservesFromItem(value))
        
        #observes = list(set(observes)) #去重
        #print(observes)
        self.observes = list(filter(lambda h:len(h)>0,set(map(lambda r:r.upper(),observes))))

        return self.observes
        #return filter(lambda ob:len(ob)>1,observes)  #get off nomeaning obs

    @staticmethod
    def getObservesFromItem(item):
        observes=[]
        if len(item)>32:
            try:
                newitem = item[:]
                for i in range((4-len(item)%4)%4):
                    newitem +="="
                decoded=b64decode(re.sub(r'\s','+',newitem)).decode()  #byte to string
                words=re.findall(r'\w+',decoded)  
                observes.extend(map(lambda w:"b64_"+w,words))
            except Exception:
                words=re.findall(r'\w+',item)
                for word in  words:
                    if len(word)>32:
                        decoded = safeB64Decode(word)
                        words2=re.findall(r'\w+',decoded) 
                        observes.extend(map(lambda w:"b64_"+w,words2))   
                    else:
                        observes.append(word)
        else:
            words=re.findall(r'\w+',item)
            observes.extend(words)
        return observes

    def getObServesFromLine(self,line):
        self.getObservesFromRecord(getRecordFromLine(line))
        return self.observes
    
    def getStateFromRecord(self,record):
        if record[1] in self.mayStates:
            self.states=[record[1]]
        return self.states[0]


    
    
def findcount():  #fileB 2486 
    score=70.599036
    totalline=1871
    mina=floor(totalline*score/(200-score))
    maxb=ceil((200-score*2)/score*totalline)
    for a in range(mina,totalline):
        for b in range(maxb):
            if abs(float(a)/(totalline+a+b)*200 - score) <0.000001:
                print(a,b)
    return

if __name__  ==  '__main__':
    
    opts,args = getopt.getopt(sys.argv[1:],"hi:o:s:l:cd:j:",
                              ["help","inputfile","outputfile","statefile",
                               "list","dump","compare"])
    if len(opts) == 0:
        opts.append(("-h",""))
        
    inputfilename = "input.txt"
    outputfilename = "output.txt"
    statefilename = "state.txt"
    modelfilename = "model.pkl"
    idlist=[]
    
    for op,value in opts:
        if op == "-h" or op == "--help" :
            print("WebShell BaseTool version 1.0.by Heguofeng")
            print('''
-h --version :help this information.
-i inputfilename
-o outputfilename
-s statefilename
-l id1[,id2] 
-c :compare  compare with inputfile and outputfile
-d 1 :dump records with idlist or idlist from statefile  1 means with urldecode 0 no decode
-j (both|add|more|less) must after with -i -s -o 
                ''')
        if op == "-i" or op == "--input":
            inputfilename = value
        if op == "-o" or op == "--output":
            outputfilename = value
        if op == "-s" or op == "--output":
            statefilename = value
        if op == "-l" or op == "--list":
            idlist = list(value.strip().split(","))
        if op == "-d" or op == "--dump":
            urlsafe=True if value=='1' else False
            if len(idlist) == 0:
                idlistinfile=getDataFromFile(statefilename)
                idlist=list(map(lambda r:r[0],idlistinfile))
            records=getDataFromFile(inputfilename,lambda r: r[0] in idlist,urlsafe)
            count=saveDatatoFile(outputfilename, records)
            print("%d record save into %s ."%(count,outputfilename))
        if op == "-c" or op == "--compare":
            compareWebShell(inputfilename,outputfilename)
        if op == "-j" or op == "--join":
            method = value
            joinWebShell(inputfilename,statefilename,outputfilename,method)     
#         if op=="-j":
#             files=value.split(",")
#             if len(files)<4:
#                 break
#             if len(files)>=4:
#                 inputfilename=files[0]
#                 inputfile2name=files[1]
#                 outputfilename=files[2]
#                 method=files[3]
#                 joinWebShell(inputfilename, inputfile2name, outputfilename, method)      
#             
