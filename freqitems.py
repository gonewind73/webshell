'''
Created on 2017年5月9日

@author: heguofeng
'''

from numpy import array

import time
import unittest
import getopt
import sys
from itertools import compress, groupby
from webshell.basetool import getDataFromFile, ObservesState
import pickle



def unDuplicate(items,sortkey=None ):
    '''
    freqItems = [[{'z', 't'}, 3], ... [{'z', 'x', 't'}, 3]]
    if a in b and a.count = b.count 
    '''
    if sortkey != None:
        items.sort(key=sortkey)
#         print(items)
        
    newItems = []
    for i in range(len(items)):
        isSkip = False
        for j in range(i+1,len(items)):
            if items[i][0].issubset(items[j][0]) and items[i][1] == items[j][1]:
                isSkip = True
                break
        if not isSkip:
            newItems.append(items[i])
    
    return newItems

class Apriori(object):
    '''
    classdocs
    '''


    def __init__(self,minSupport=1):
        '''
        Constructor
        '''
        self.dataSet=[]
        self.dataItems = {}
        self.minSupport = minSupport
        self.L0=[]
        self.needRecalculate = True

    def loadDataFromLE(self,lews):
        observeIndexlist=sorted(list(lews.observes.values()))
        wSelector=list(1 if s == 'w' else 0 for s in lews.trainStates)
        self.dataSet = list(compress(lews.trainObserves,wSelector))
        self.dataItems = lews.observes
        self.dataArray=array(list(map(lambda ob:list(1 if x in ob else 0 for x in observeIndexlist),self.dataSet)))
        self.dataList=list(map(lambda ob:list(1 if x in ob else 0 for x in observeIndexlist),self.dataSet))
        self.needRecalculate = False

    
    def loadData(self,dataset):
        for record in dataset:
            self.loadRecord(record)
        dataItemsList = list(map(lambda r:r[1],sorted(self.dataItems.items(),key=lambda r:r[1])))
        self.dataList=list(map(lambda ob:list(1 if x in ob else 0 for x in dataItemsList),self.dataSet))
        self.dataArray=array(self.dataList)
#         print(self.dataItems)
#         print(self.dataSet)
#         print(self.dataArray)
        
    def getDateItemIndex(self,data):
        if data not in self.dataItems.keys():
            self.dataItems[data] = len(self.dataItems)
        return self.dataItems[data]
        
    def loadRecord(self,record):
        self.dataSet.append(list(map(lambda item:self.getDateItemIndex(item),record)))
        self.needRecalculate = True

    def getCount(self,indexs):
        shouldLen = len(indexs)
        selectedArray = self.dataArray[:,indexs]
        factorArray = array(list(1 for x in range(shouldLen)))
        resutlArray = selectedArray.dot(factorArray)
        return len(list(filter(lambda item:item == shouldLen,resutlArray.tolist())))

    def getCount2(self,indexs):
        matchCount = 0
        for r in self.dataList:
            for idx in indexs:
                isMatched = True
                if r[idx]==0:
                    isMatched = False
                    break
            if isMatched:
                matchCount += 1
                if matchCount > self.minSupport:
                    return matchCount
        return matchCount
            
    def getCombines(self,items):
        itemsLength = len(items)
        validCombinedItems=[]
        for i in range(itemsLength):
            for j in range(i+1,itemsLength):
                if items[j][0] < items[i][-1]:
                    continue
                templist=items[i][:]
                templist.extend(items[j])
                combinedItem = list(set(templist))
                if self.getCount2(combinedItem) >= self.minSupport:
                    combinedItem.sort() 
                    validCombinedItems.append(combinedItem)
                    #print(combinedItem)
        return validCombinedItems
 
    def getCombines2(self,items):
        itemsLength = len(items)
        validCombinedItems=[]
        for i in range(itemsLength):
            for j in range(len(self.L0)):
                if self.L0[j][0] <= items[i][-1]:
                    continue
                templist=items[i][:]
                templist.extend(self.L0[j])
                combinedItem = list(set(templist))
                if self.getCount(combinedItem) >= self.minSupport:
                    combinedItem.sort() 
                    validCombinedItems.append(combinedItem)
                    #print(combinedItem)
        return validCombinedItems
                       
    def run(self):
        dataColumSumArray = self.dataArray.sum(axis = 0)
        #selector =  list(map(lambda item:1 if item > self.minSupport else 0,dataColumSumArray))
        selectorIndexs = list(map(lambda item:[item[0]],filter(lambda item:item[1]>=self.minSupport,enumerate(dataColumSumArray))))
        self.L0=sorted(selectorIndexs[:],key=lambda r:r[0])
        print(self.L0)
       
        k=1
        L=[[]]
        L[0].extend(self.L0)
        print(len(L[0]))
        while L[k-1] != []:
            L.append(self.getCombines(L[k-1]))
            print(len(L[-1]))
            k += 1
    
        index2keyword = dict(map(lambda t:(t[1],t[0]), self.dataItems.items()))
        #print(index2keyword)
        U = []
        for l in L:
            for c in  l:
                kws=[]
                for i in c:
                    kws.append(index2keyword[i])
                U.append(kws)
        return U
            
def getKeywordsByApriori(modelfilename="lew.pkl",code="pickle",idlist=[]):
    from webshell.linearequation import LinearEquationWebShell
    starttime=time.time() 
    
    lews = LinearEquationWebShell()
    lews.loadModel(modelfilename, code)
    #print(lews.observes,lews.trainStates)
    
    myApriori = Apriori(minSupport=40)
    myApriori.loadDataFromLE(lews)
    
    keywords = myApriori.run()
    
    print(len(keywords))
    print("end of keywords find use %f second. "%(time.time()-starttime))

class TreeNode(object):
    def __init__(self, nameValue, numOccur, parentNode):
        self.name = nameValue
        self.count = numOccur
        self.nodeLink = None
        self.parent = parentNode
        self.children = {}
 
    def inc(self, numOccur):
        self.count += numOccur
 
    def disp(self, ind=1):
        print( ' ' * ind, self.name, ' ', self.count)
        for child in self.children.values():
            child.disp(ind + 1)

class HeadNode(object):
    def __init__(self, nameValue, numOccur = 1 , nodelink=None):
        self.name = nameValue
        self.count = numOccur
        self.nodeLink = nodelink
 
    def inc(self, numOccur):
        self.count += numOccur
 
    def __str__(self):
        nodecount = 0
        nodelink = self.nodeLink
        while nodelink != None:
            nodecount += 1
            nodelink = nodelink.nodeLink
        return "%-20s: %d occur %d nodes."%(self.name,self.count,nodecount)
    
    @staticmethod
    def disp(headertable):
        
        for key,value in sorted(headertable.items(),key=lambda h:h[1][0]):
            headnode=HeadNode(key,value[0],value[1])
            print(headnode)

class FPGrowth(object):
    def __init__(self,dataset={},minSupport=1):
        self.headerTable={}
        self.dataSet=dataset
        self.minSupport = minSupport
        self.rootTree=None
        self.asASets = {}
        pass
    
    def loadData(self,data):
        '''
        data = [record,...]
        record = [ observe1,observe2,...]
        observe = string
        dataset = { frozenset({'a','b'}):3}
        '''
        self.dataSet = self.createInitSet(data)
        
    def loadDataSet(self,dataset):
        self.dataSet = dataset
        
    def loadDataFromLE(self,lews):
        observeIndexlist=sorted(list(lews.observes.values()))
        wSelector=list(1 if s == 'w' else 0 for s in lews.trainStates)
        dataSet = list(compress(lews.trainObserves,wSelector))
        self.dataSet = self.createInitSet(dataSet)


    def createInitSet(self,dataSet):
        '''
        trans [ [data,...data],...[data,...data]] to {{data,...data}:1,...{data,...data}:1}
        '''
        retDict = {}
        for trans in dataSet:
            retDict[frozenset(trans)] = 1 + retDict.get(frozenset(trans),0)
        return retDict
    
    def splitDataSet(self):
        headlist = sorted(map(lambda h:[h[0],h[1][0]],self.headerTable.items()),key=lambda h:h[1])
        #print(headlist)
        sds = {}
        for key, group in groupby(headlist, lambda kv:kv[1]):
            groupset = set(map(lambda h:h[0],group))
            if len(groupset)>1:
                sds[key] = groupset
        
        #print(sds)
        return sds
    
    def isAsASet(self,dataset,count):
        mycount = 0
        for ds in self.dataSet:
            if dataset.issubset(ds):
                mycount += self.dataSet[ds]
        if mycount == count :
            return True
        return False 
    
    def asASet(self,dataset):
        #update self.dataset and headtable
        newname =  ""
        for s in dataset:
            newname += "~" + s
        self.asASets[newname] = dataset
        #print("new asASets",self.asASets)
        tempdataset = {}
        for ds,count in list(self.dataSet.items()):
            if dataset.issubset(ds):
                newset = (set(ds)-dataset)
                newset.add(newname)
                #print(newset)
                self.dataSet[frozenset(newset)] = count
                del self.dataSet[ds] 
        

        self.headerTable[newname]=[self.headerTable[list(dataset)[0]][0],None]        
        for hn,value in list(self.headerTable.items()):
            if hn in  dataset:
                del self.headerTable[hn]
        
    
    def updateTree(self,items, inTree, count):
        if items[0] in inTree.children:
            # 有该元素项时计数值+1
            inTree.children[items[0]].inc(count)
        else:
            # 没有这个元素项时创建一个新节点
            inTree.children[items[0]] = TreeNode(items[0], count, parentNode = inTree)
            # 更新头指针表或前一个相似元素项节点的指针指向新节点
            self.updateHeaderTable(items[0],inTree.children[items[0]])
#             if headerTable[items[0]][1] == None:
#                 headerTable[items[0]][1] = inTree.children[items[0]]
#             else: # append to chain tail
#                 self.updateHeader(headerTable[items[0]][1], inTree.children[items[0]])
     
        if len(items) > 1:
            # 对剩下的元素项迭代调用updateTree函数
            self.updateTree(items[1::], inTree.children[items[0]],  count)
            
    def updateHeaderTable(self,item,node):
        if self.headerTable[item][1] == None:
            self.headerTable[item][1] = node
        else :
            tempNode = self.headerTable[item][1]
            while (tempNode.nodeLink != None):
                tempNode = tempNode.nodeLink
            tempNode.nodeLink = node
        return
        
    def updateHeader(self,nodeToTest, targetNode):
        while (nodeToTest.nodeLink != None):
            nodeToTest = nodeToTest.nodeLink
        nodeToTest.nodeLink = targetNode
        
    def getItems(self,dataSet):
        itemsTable = {}
        for record in dataSet:
            for item in record:
                itemsTable[item] = [itemsTable.get(item, [0,None])[0] + self.dataSet[record],None]
        return itemsTable

    
    def createTree(self):
    
        ''' 创建FP树 
        dataset = { frozenset({'a','b'}):3}
        
        headerTable = { key:[count,point of first key occur],} #用于存放指向相似元素项指针
        '''
        # 第一次遍历数据集，创建头指针表
#         headerTable = {}
#         for record in self.dataSet:
#             for item in record:
#                 headerTable[item] = [headerTable.get(item, [0,None])[0] + self.dataSet[record],None]
        headerTable = self.getItems(self.dataSet)
        # 移除不满足最小支持度的元素项
        self.headerTable = dict(filter(lambda r:r[1][0]>=self.minSupport,headerTable.items()))

        # try to make aset
        sds = self.splitDataSet()
        for count in sds:
            if self.isAsASet(sds[count], count):
                self.asASet(sds[count])

             
        # 空元素集，返回空
        freqItemSet = set(self.headerTable.keys())
        if len(freqItemSet) == 0:
            return None
                
        self.rootTree = TreeNode('Null Set', 1, None) # 根节点
        # 第二次遍历数据集，创建FP树
        for tranSet ,count in self.dataSet.items():
            localD = {} # 对一个项集tranSet，记录其中每个元素项的全局频率，用于排序 {key:count}
            for item in tranSet:
                if item in freqItemSet:
                    localD[item] = self.headerTable[item][0] 
            if len(localD) > 0:
                tempList = sorted(localD.items(), key=lambda p: p[0]) # 排序by count
                orderedItems = [v[0] for v in sorted(tempList, key=lambda p: p[1], reverse=True)] # 排序by count
                self.updateTree(orderedItems, self.rootTree, count) # 更新FP树
        return self.rootTree
    
    def ascendTree(self,leafNode, prefixPath):
        if leafNode.parent != None:
            prefixPath.append(leafNode.name)
            self.ascendTree(leafNode.parent, prefixPath)
    
    def findPrefixPath(self,treeNode):
        ''' 创建前缀路径 '''
        condPats = {}
        while treeNode != None:
            prefixPath = []
            self.ascendTree(treeNode, prefixPath)
            if len(prefixPath) > 1:
                condPats[frozenset(prefixPath[1:])] = treeNode.count
            treeNode = treeNode.nodeLink
        return condPats
        
    def mineTree(self,prefix,freqItemList,strictmode=False):
        if self.rootTree == None:
            return []
        bigL = [v[0] for v in sorted(self.headerTable.items(), key=lambda p: p[1][0])]
#         freqItemList = []
        for basePat in bigL:
            
            newFreqSet = prefix.copy()
            #originBasePat = self.asASets.get(basePat,{basePat})
            #print("originBasePat",basePat,originBasePat)
            #newFreqSet |= originBasePat
            newFreqSet.add(basePat)
            
            #freqItemList[0] += 1
            freqItemList.append([newFreqSet,self.headerTable[basePat][0]])
            #print(len(freqItemList))
            condPattBases = self.findPrefixPath(self.headerTable[basePat][1])
            #print(condPattBases)
            condFPGrowth = FPGrowth(condPattBases, minSupport = self.minSupport)
            condFPGrowth.createTree()
            #HeadNode.disp(condFPGrowth.headerTable)
            condFPGrowth.mineTree(newFreqSet,freqItemList,strictmode=strictmode)
        
        # check item ,if combineitem reset to items .BY heguofeng 2017.5.16
        for i in range(len(freqItemList)):
            originset = set([])
            for item in list(freqItemList[i][0]):
                originitem =  self.asASets.get(item,{item})
                originset |= originitem
            freqItemList[i][0] = originset   
#                   
            
#             count = 0
#             skipSelf= False
#             for cf in childFreqItems:
# #                 if self.headerTable[basePat][0] == cf[1]:
# #                     if strictmode:
# #                         skipSelf = True
#                 count += cf[1]
#                 freqItemList.append([set(basePat).union(cf[0]),self.headerTable[basePat][0]])
# #             if count == self.headerTable[basePat][0] and strictmode:
# #                 skipSelf = True
#             if not skipSelf:
#                 freqItemList.append([set(basePat),self.headerTable[basePat][0]])
    
        return 
    
    def getFreqItems(self):
        freqItems = []
        self.mineTree(set([]),freqItems)
        print("found freqItems:",len(freqItems),time.time())
        #print("found freqItems:",freqItems[0])
        newItems = freqItems
        newItems = unDuplicate(freqItems)
        print("found freqItems after undupliate:",len(newItems))
        newItems = unDuplicate(newItems,sortkey=lambda f:len(f[0]) )
        #newItems = list(filter(lambda f:len(f[0])>1,newItems))
        newItems.sort(key=lambda f:f[1])
#         of = open("freqitems.txt","w")
#         for kws in newItems:
#             of.write(str(kws)+"\n")
#         of.close()
        return newItems
     
def getKeywordsByFPGrowth(inputfilename,minSupport=4,filterfunction=lambda r:True):
    myFPGrowth = FPGrowth(minSupport=minSupport)
    myFPGrowth.loadDataFromFile(inputfilename,filterfunction=filterfunction)
    myFPGrowth.createTree()
    #myFPGrowth.rootTree.disp(1)
    #HeadNode.disp(myFPGrowth.headerTable)
    print(len(myFPGrowth.headerTable))
    freqItems = []
    myFPGrowth.mineTree(set([]),freqItems)
    print("found freqItems:",len(freqItems))
    newItems = unDuplicate(freqItems)
    print("found freqItems after undupliate:",len(newItems))
    newItems = unDuplicate(newItems,sortkey=lambda f:len(f[0]) )
    #newItems = list(filter(lambda f:len(f[0])>1,newItems))
    newItems.sort(key=lambda f:f[1])
    return newItems

                

    
    

class TestApriori(unittest.TestCase):
    def setUp(self):
        print('Start test Apriori...')
 
    def tearDown(self):
        print( 'end Apriori Test...')
        
    def test_Keywords(self):
        myApriori = Apriori(minSupport=3)
        myApriori.loadData( [ [ 1, 3, 4,5 ], [ 2, 3, 5 ], [ 1, 2, 3,4, 5 ], [ 2,3,4, 5 ] ] )  
        keywords = myApriori.run() 
        print(len(keywords),keywords)
        return 
                   
    def test_FPGrowth(self):
        simpDat = [['r', 'z', 'h', 'j', 'p'],
                   ['z', 'y', 'x', 'w', 'v', 'u', 't', 's'],
                   ['z'],
                   ['r', 'x', 'n', 'o', 's'],
                   ['y', 'r', 'x', 'z', 'q', 't', 'p'],
                   ['y', 'z', 'x', 'e', 'q', 's', 't', 'm']]
        myFPGrowth = FPGrowth(minSupport=3)
        
        myFPGrowth.loadData(simpDat)
        myFPTree = myFPGrowth.createTree()
        myFPTree.disp()
        HeadNode.disp(myFPGrowth.headerTable)
        
        #pat = myFPGrowth.findPrefixPath('x', myFPGrowth.headerTable['x'][1])
        #print(pat)
        freqItems = []
        myFPGrowth.mineTree(set([]),freqItems,strictmode=True)
        print(len(freqItems),freqItems)
        newItems = unDuplicate(freqItems)
        print(len(newItems),newItems)
        newItems = unDuplicate(freqItems,sortkey = lambda f:len(f[0]))
        print(len(newItems),newItems)
        

        return 
                       
if __name__  ==  '__main__':
    
    opts,args = getopt.getopt(sys.argv[1:],"hi:o:s:m:l:tpaf",
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
        if op == "-f" or op == "--fpgrowth":
            getKeywordsByFPGrowth(
                            inputfilename = inputfilename
                            )            
   