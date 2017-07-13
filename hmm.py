# coding:utf-8
'''
Created on 2017年4月29日

@author: heguofeng
'''

# encoding=utf-8
import pickle
import json
import copy

import math


#EPS = 0.00001
EPS = -5
VERBOSE=False

def setVerbose(flag):
    global VERBOSE
    VERBOSE=flag

def saveMattoFile(data,filename):
    keywords=sorted(data.items(),key=lambda r:r[1],reverse=True)
    fw=open(filename,'w')
    for l in keywords:
        fw.write("%s %d\n"%(l[0],l[1]))
    fw.close()
    pass

class HMModel:
    def __init__(self):
        self.trans_mat = {}  # trans_mat[status][status] = int
        self.emit_mat = {}  # emit_mat[status][observe] = int
        self.init_vec = {}  # init_vec[status] = int
        self.state_count = {}  # state_count[status] = int
        self.states = {}
        self.inited = False
        self.real_init_vec={}   #float  
        self.real_trans_mat={}  #float 
        self.real_emit_mat={}   #float 
        self.real_need_recalculate=True #prevent calculate every time

    def setup(self):
        for state in self.states:
            # build trans_mat
            self.trans_mat[state] = {}
            for target in self.states:
                self.trans_mat[state][target] = 0.0
            # build emit_mat
            self.emit_mat[state] = {}
            # build init_vec
            self.init_vec[state] = 0
            # build state_count
            self.state_count[state] = 0
        self.inited = True

    def save(self, filename="hmm.json", code='json'):
        fw = open(filename, 'wb')
        data = {
            "trans_mat": self.trans_mat,
            "emit_mat": self.emit_mat,
            "init_vec": self.init_vec,
            "state_count": self.state_count
        }
        if code == "json":
            txt = json.dumps(data)
            txt = txt.encode('utf-8').decode('unicode-escape')
            fw.write(txt)
        elif code == "pickle":
            pickle.dump(data, fw)
        fw.close()

    def load(self, filename="hmm.json", code="json"):
        fr = open(filename, 'rb')
        if code == "json":
            txt = fr.read()
            model = json.loads(txt)
        elif code == "pickle":
            model = pickle.load(fr)
        self.trans_mat = model["trans_mat"]
        self.emit_mat = model["emit_mat"]
        self.init_vec = model["init_vec"]
        self.state_count = model["state_count"]
        self.inited = True
        fr.close()
        self.real_need_recalculate=True

    def do_train(self, observes, states):
        if not self.inited:
            self.setup()

        for i in range(len(states)):
            if i == 0:
                self.init_vec[states[0]] += 1
                self.state_count[states[0]] += 1
                #add observe 0 2017.5.1 
                if observes[i] not in self.emit_mat[states[i]]:
                    self.emit_mat[states[i]][observes[i]] = 1
                else:
                    self.emit_mat[states[i]][observes[i]] += 1                
            else:
                self.trans_mat[states[i - 1]][states[i]] += 1
                self.state_count[states[i]] += 1
                if observes[i] not in self.emit_mat[states[i]]:
                    self.emit_mat[states[i]][observes[i]] = 1
                else:
                    self.emit_mat[states[i]][observes[i]] += 1
        if len(states)>0:
            self.real_need_recalculate=True
           
            
    def printemit_mat(self):
        for state in self.states:
            print(sorted(self.emit_mat[state].items(),key=lambda d:d[1],reverse=True))
        return

    def get_prob(self):
        '''
        set flag avoid recal everytime
        del some meanless such as only 1 time obeserve
        '''
        
        if self.real_need_recalculate==False:
            return self.real_init_vec,self.real_trans_mat,self.real_emit_mat
    
        #self.printemit_mat() 
        #remove observes=1
        temp_init_vec = copy.deepcopy(self.init_vec)
        temp_trans_mat = copy.deepcopy(self.trans_mat)
        temp_emit_mat = copy.deepcopy(self.emit_mat)
        temp_state_count=copy.deepcopy(self.state_count)
        
        for state in ['w']:
            for ob,count in temp_emit_mat[state].items():
                if count<1:
                    temp_emit_mat[state].pop(ob)
#                     temp_state_count[state]-=count
#                     temp_trans_mat[state][state]-=count
                elif ob in temp_emit_mat['n'].keys():
                    if temp_emit_mat['n'][ob]>0:
                        temp_emit_mat[state].pop(ob)
                        #temp_state_count[state] -= count
#                         temp_trans_mat[state][state]-=count
                        #temp_emit_mat['n'].pop(ob)
#                         temp_state_count['n']-=temp_emit_mat['n'][ob]
#                         temp_trans_mat['n']['n'] -= count
#                         
        saveMattoFile(self.emit_mat['w'],"keywordsw.txt")             
        saveMattoFile(self.emit_mat['n'],"keywordsn.txt")             
        saveMattoFile(temp_emit_mat['w'],"keywordswt.txt")             
        saveMattoFile(temp_emit_mat['n'],"keywordsnt.txt")       
              
        init_vec = {}
        trans_mat = {}
        emit_mat = {}
        default = max(temp_state_count.values())  # avoid ZeroDivisionError
        # convert init_vec to prob
        for key in temp_init_vec:
            if temp_init_vec[key]==0:
                init_vec[key]=-100
                continue
            
            if temp_state_count[key] != 0:
                init_vec[key] = math.log10(float(temp_init_vec[key]) / temp_state_count[key])
            else:
                init_vec[key] = math.log10(float(temp_init_vec[key]) / default)
        # convert trans_mat to prob
        for key1 in temp_trans_mat:
            trans_mat[key1] = {}
            for key2 in temp_trans_mat[key1]:
                if temp_trans_mat[key1][key2]==0:
                    trans_mat[key1][key2]=-100
                    continue
                if temp_state_count[key1] != 0:
                    trans_mat[key1][key2] = math.log10(float(temp_trans_mat[key1][key2]) / temp_state_count[key1])
                else:
                    trans_mat[key1][key2] = math.log10(float(temp_trans_mat[key1][key2]) / default)
        # convert emit_mat to prob
        for key1 in temp_emit_mat:
            emit_mat[key1] = {}
            for key2 in temp_emit_mat[key1]:
                if temp_emit_mat[key1][key2]==0:
                    emit_mat[key1][key2]=-100
                    continue                
                if temp_state_count[key1] != 0:
                    emit_mat[key1][key2] = math.log10(float(temp_emit_mat[key1][key2]) / temp_state_count[key1])
                else:
                    emit_mat[key1][key2] = math.log10(float(temp_emit_mat[key1][key2]) / default)
#         default = max(self.state_count.values())  # avoid ZeroDivisionError
#         # convert init_vec to prob
#         for key in self.init_vec:
#             if self.state_count[key] != 0:
#                 init_vec[key] = float(self.init_vec[key]) / self.state_count[key]
#             else:
#                 init_vec[key] = float(self.init_vec[key]) / default
#         # convert trans_mat to prob
#         for key1 in self.trans_mat:
#             trans_mat[key1] = {}
#             for key2 in self.trans_mat[key1]:
#                 if self.state_count[key1] != 0:
#                     trans_mat[key1][key2] = float(self.trans_mat[key1][key2]) / self.state_count[key1]
#                 else:
#                     trans_mat[key1][key2] = float(self.trans_mat[key1][key2]) / default
#         # convert emit_mat to prob
#         for key1 in self.emit_mat:
#             emit_mat[key1] = {}
#             for key2 in self.emit_mat[key1]:
#                 if self.state_count[key1] != 0:
#                     emit_mat[key1][key2] = float(self.emit_mat[key1][key2]) / self.state_count[key1]
#                 else:
#                     emit_mat[key1][key2] = float(self.emit_mat[key1][key2]) / default
        
        self.real_need_recalculate=False
        self.real_init_vec=init_vec.copy()
        self.real_trans_mat=trans_mat.copy()
        self.real_emit_mat=emit_mat.copy()
        
        return init_vec, trans_mat, emit_mat

    def do_predict(self, sequence):
        tab = [{}]
        path = {}
        init_vec, trans_mat, emit_mat = self.get_prob()
        
        

        # init
        for state in self.states:
            tab[0][state] = init_vec[state] + emit_mat[state].get(sequence[0], EPS)
#            tab[0][state] = init_vec[state] * emit_mat[state].get(sequence[0], EPS)
            path[state] = [state]
        
        # build dynamic search table
        #print(sequence)
        for t in range(1, len(sequence)):
            tab.append({})
            new_path = {}
            for state1 in self.states:
                items = []
                for state2 in self.states:
                    if tab[t - 1][state2] == 0:
                        continue
                    prob = tab[t - 1][state2] + trans_mat[state2].get(state1, EPS) + emit_mat[state1].get(sequence[t], EPS)
#                    prob = tab[t - 1][state2] * trans_mat[state2].get(state1, EPS) * emit_mat[state1].get(sequence[t], EPS)
                    items.append((prob, state2))
                best = max(items)  # best: (prob, state)
                tab[t][state1] = best[0]
                new_path[state1] = path[best[1]] + [state1]
            path = new_path

        #add verbose 2017.5.4
        #print(VERBOSE)
        if VERBOSE==True:
            print("verbose",len(sequence))
            for state in self.states:
                for s in sequence:
                    #print(s)
                    if s in emit_mat[state].keys():
                        print("state %s encount %s with prob %e."%(state,s,emit_mat[state].get(s,EPS)))
                print("state %s total prob:%e"%(state,tab[len(sequence) - 1][state]))  
        # search best path
        prob, state = max([(tab[len(sequence) - 1][state], state) for state in self.states])
        return path[state],prob
