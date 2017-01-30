'''
Created on Nov 20, 2015

@author: junchao
'''

import os
import sys
import re
import random
import networkx as nx
import numpy as np
import json
from subprocess import call
import time
from NewInstance import NewInstance       
import collections

class Workflow():     
    
    def add_entry_exit(self, g):
        # add entry node to the graph
        g.add_node(0, est = -1, eft = -1, lft =-1)
        for vertex in g:
            if len(g.predecessors(vertex)) == 0 and not vertex == 0:   
                self.G.add_weighted_edges_from([(0, vertex, 0)])
        # add exit node to the graph
        g.add_node(self.vertex_num-1, est = -1, eft = -1, lft =-1)
        startnodes = []
        for vertex in g:
            if len(g.successors(vertex)) == 0 and not vertex == self.vertex_num-1:   
                startnodes.append(vertex)
                
        for node in startnodes:        
            self.G.add_weighted_edges_from([(node, self.vertex_num-1, 0)])

    def init(self, content):
        self.G = nx.DiGraph()
        self.vertex_num =0 
         
        for (key, value) in content['workflow'].items():
            if isinstance(value, list) :
                if key == 'nodes' :
                    self.vertex_num = len(value)
                    for node in value:
                        self.G.add_node(node['name'], est = -1, eft = -1, lft =-1)    
                if key == 'links' :
                    for link in value:
                        self.G.add_weighted_edges_from([(link['source'], link['target'], link['weight'])])
        print self.G.nodes
        
        #parse the performance matrix
        p = []
        od = collections.OrderedDict(sorted(content['performance'].items()))
        for (key, value) in od.items():
            row = []
            row.append(0)
            for i in value.split(','):
                row.append(int(i))
            row.append(0)
            print row
            p.append(row)
        self.p_table = np.matrix(p)
        #parse the price vector
        self.vm_price = []
        for i in content['price'].split(','):
            self.vm_price.append(int(i))
        
        #parse the deadline
        self.d_list = []
        for (key, value) in content['deadline'].items():
            self.d_list.append([int(key), int(value)])
        self.d_table = np.matrix(self.d_list)
        self.successful = 0
     
        self.vertex_num += 2
        self.add_entry_exit(self.G) 
        
        #test whether the DAG contains cycles
        if len(list(nx.simple_cycles(self.G))) > 0:
            print "the DAG contains cycles"
            sys.exit()

        self.assigned_list = [-1]*(self.vertex_num)
                
        self.instances = []
        self.G.node[0]['est'] = 0
        self.G.node[0]['eft'] = 0
        self.cal_est(0)
        self.G.node[self.vertex_num-1]['lft'] = self.d_table[self.d_table.shape[0]-1,1]#self.p_table[0, child], self.p_table.shape[0]
        self.cal_lft(self.vertex_num-1)
    
    def init1(self, workflow_file_name, performance_file_name, price_file_name, deadline_file_name):
        
        #Initialization
        self.G=nx.DiGraph()
        self.vertex_num = 0
        self.successful = 0
        #Read the workflow information

        graph = pydot.graph_from_dot_file(workflow_file_name)
        nx_graph = nx.from_pydot(graph)
        self.G=nx.DiGraph()
        for node in nx_graph:
            #print node
            self.G.add_node(int(node)+1, est = -1, eft = -1, lft =-1)
            self.vertex_num += 1 
        #print nx_graph.edge
        #print workflow_file_name
        for link in nx_graph.edges_iter():
            #print link[0], link[1]
            self.G.add_weighted_edges_from([(int(link[0])+1, int(link[1])+1, int(float(nx_graph[link[0]][link[1]][0]['weight'])))])   
        
        self.vertex_num += 2
        self.add_entry_exit(self.G) 
        
        #test whether the DAG contains cycles
        if len(list(nx.simple_cycles(self.G))) > 0:
            print "the DAG contains cycles"
            sys.exit()
        #read performance table
        l = [ map(int,line.split(',')) for line in open(performance_file_name, 'r')]
        #append the entry and exit node information
        for row in l:
            row.insert(0, 0)
            row.insert(len(row),0)
        self.p_table = np.matrix(l)
        
        self.assigned_list = [-1]*(self.vertex_num)
        
        self.vm_price = map(int,open(price_file_name,'r').readline().split(','))
        
        self.instances = []
        
        self.d_list = [ map(int,line.split('\t')) for line in open(deadline_file_name, 'r')]
        tmpList = self.d_list[len(self.d_list)-1]
        self.d_table = np.matrix(tmpList)
        #deadline = open(deadline_file_name, 'r').readline()  
        self.G.node[0]['est'] = 0
        self.G.node[0]['eft'] = 0
        self.cal_est(0)
        self.G.node[self.vertex_num-1]['lft'] = self.d_table[self.d_table.shape[0]-1,1]#self.p_table[0, child], self.p_table.shape[0]
        self.cal_lft(self.vertex_num-1)
        
    #The following two functions are to initialize the EST, EFT and LFT
    #calculate the earliest start time and earliest finish time    
    def cal_est(self, i):
        for child in self.G.successors(i):
            est = self.G.node[i]['eft']+self.G[i][child]['weight']
            if est>self.G.node[child]['est']:
                self.G.node[child]['est'] = est
                self.G.node[child]['eft'] = est + self.p_table[0, child]
                self.cal_est(child)
    
    def cal_lft(self, d):
        for parent in self.G.predecessors(d):
            lft  = self.G.node[d]['lft'] - self.p_table[0, d] - self.G[parent][d]['weight']
            d_table_list = []
            for deadline in self.d_table:
                d_table_list.append(deadline[0, 0])
                
            if parent in d_table_list:
                deadline = self.d_table[d_table_list.index([parent]),1]
                if deadline < lft:
                    lft = deadline
            if self.G.node[parent]['lft'] == -1 or lft<self.G.node[parent]['lft']:
                # parent may not finish later
                self.G.node[parent]['lft'] = lft
                #print "call graphAssignLFT(",graph.node[parent]['name'],")"
                self.cal_lft(parent)     
    
    #Finding critical path
    def ic_pcp(self):
        self.assigned_list[0] = 0
        self.assigned_list[self.vertex_num-1] = 0  
        self.assign_parents(self.vertex_num-1)
    
    def has_unassigned_parent(self, i):
        for parent in self.G.predecessors(i): 
            if (self.assigned_list[parent] == -1): 
                return True
        return False
                    
    def assign_parents(self, i):  
        while (self.has_unassigned_parent(i)):  
            if self.successful == 1:   #resources cannot be met
                break            
            pcp = []
            self.find_critical_path(i, pcp)
            
            assigned_vms = self.assign_path(pcp)     
            
            if -1 in assigned_vms:
                print 'resource cannot be met'
                break
            self.G.node[pcp[len(pcp)-1]]['eft'] = self.G.node[pcp[len(pcp)-1]]['est'] + self.p_table[assigned_vms[len(pcp)-1], pcp[len(pcp)-1]]
            self.update_est(pcp[len(pcp)-1], pcp, assigned_vms)
            self.update_lft(pcp[0], pcp, assigned_vms)
            #split according to the types of assigned VMs and add it to the new instance
            ni = NewInstance(assigned_vms, self.G.node[pcp[len(pcp)-1]]['est'], self.G.node[pcp[0]]['eft'], pcp)
            
            for j in xrange(len(pcp)):
                ni.cost = ni.cost + self.vm_price[assigned_vms[j]]
            
            self.instances.append(ni)                 
            for j in reversed(pcp):                 #also in the paper they didn't mention the order
                self.assign_parents(j)
                    
    #TODO: A very tricky thing on updating the EST and EFT.
       
    def update_est(self, i, pcp, assigned_vms):
        for child in self.G.successors(i):
            if child not in pcp:
                est = self.G.node[i]['eft']+self.G[i][child]['weight']
                
                if self.assigned_list[i] == -1:
                    eft = est + self.p_table[0, child]
                else:
                    eft = est + self.p_table[self.assigned_list[child], child]
            else:
                if pcp.index(child) == len(pcp) - 1:
                    est = self.G.node[i]['eft'] 
                    eft = est + self.p_table[self.assigned_list[child], child]
                else:
                    pos = pcp.index(child)
                    est = self.G.node[i]['eft'] + self.G[pcp[pos+1]][pcp[pos]]['weight']
                    eft = est + self.p_table[self.assigned_list[child], child] 
                                                
            #decide whether the assignment will violate other parent data dependency            
            all_smaller = True
            for parent in self.G.predecessors(child):
                if not parent == i:
                    if self.G.node[parent]['eft'] + self.G[parent][child]['weight'] > est:   
                        all_smaller = False
            if all_smaller:
                self.G.node[child]['est'] = est
                self.G.node[child]['eft'] = eft
                self.update_est(child, pcp, assigned_vms)         
                      
    def update_lft(self, d, pcp, assigned_vms):        
        for parent in self.G.predecessors(d):            
            if parent not in pcp:                
                if self.assigned_list[d] == -1:
                    lft = self.G.node[d]['lft'] - self.p_table[0, d] - self.G[parent][d]['weight']  
                else:
                    lft = self.G.node[d]['lft'] - self.p_table[self.assigned_list[d], d] - self.G[parent][d]['weight']           
            else:
                pos = pcp.index(parent)
                #if pos < len(pcp) -1:
                if assigned_vms[pos] == assigned_vms[pos-1]:#9, 6, 2
                    lft = self.G.node[d]['lft'] - self.p_table[self.assigned_list[d], d]
                else:
                    lft = self.G.node[d]['lft'] - self.p_table[self.assigned_list[d], d] - self.G[pcp[pos]][pcp[pos-1]]['weight']
 
            if lft < self.G.node[parent]['lft']:
                self.G.node[parent]['lft'] = lft
                self.update_lft(parent, pcp, assigned_vms)    


    def find_critical_path(self, i, pcp):
        cal_cost = 0
        critical_parent = -1
        for n in self.G.predecessors(i):
            if self.assigned_list[n] == -1: #parent of node i is not assigned
                if self.G.node[n]['eft'] + self.G.edge[n][i]['weight'] > cal_cost:
                    cal_cost = self.G.node[n]['eft'] + self.G.edge[n][i]['weight']
                    critical_parent = n
        if not critical_parent == -1:
            pcp.append(critical_parent)   
            self.find_critical_path(critical_parent, pcp)
    
    def exec_time_sum(self, pcp, vm_type):
        sum = 0
        for i in pcp:
            sum += self.p_table[vm_type, i]
        return sum
    
    #look forward one step when assigning a vm to a pcp how the est varies
    def est_vary(self, pcp, d):
        head_pcp = pcp[len(pcp)-1]  
        original_est = self.G.node[head_pcp]['est']       
        biggest_est = -1 
        biggest_parent = -1
        for parent in self.G.predecessors(head_pcp):
            if parent == d:
                est = self.G.node[parent]['eft']
            else:
                est = self.G.node[parent]['eft'] + self.G[parent][head_pcp]['weight']
            if biggest_est < est:
                biggest_est = est
                biggest_parent =  parent
        return original_est-biggest_est
            
    #choose the best existing available instance for the pcp
    def choose_exist_instance(self, pcp):
        best_vm = None
        best_exec_time = -1
        best_vary_time = -1
        for vm in self.instances:
            head_pcp = pcp[len(pcp)-1]     
            for parent in self.G.predecessors(head_pcp):
                head_exist_pcp = vm.task_list[0]   #The last node of the previous critical path
                if parent == head_exist_pcp:
                    if best_vm == None:
                        best_vm = vm
                        exec_time = self.exec_time_sum(pcp, vm.vm_type)
                        best_exec_time = exec_time
                        best_vary_time = self.est_vary(pcp, head_exist_pcp)
                    else:
                        best_vm_head = vm.task_list[0]
                        # if assigned to the vm, what will the est be
                        exec_time = self.exec_time_sum(pcp, vm.vm_type)
                        # calculate the lft
                        varied_time = self.G.node[head_pcp]['est']-self.est_vary(pcp, head_exist_pcp)
                        lft = varied_time+exec_time
                        if (exec_time - self.est_vary(pcp, head_exist_pcp))*self.vm_price[vm.vm_type]> \
                        (best_exec_time - self.est_vary(pcp, best_vm.task_list[0]))*self.vm_price[best_vm.vm_type] \
                        and lft < self.G.node[head_pcp]['lft']:  #also should not violate the lft
                            best_vm = vm
                            best_exec_time = exec_time
                            best_vary_time = varied_time
        if not best_vm == None:
            best_vm.vm_end = self.G.node[pcp[len(pcp)-1]]['est']-best_vary_time+best_exec_time
        return best_vm
               
    def assign_path(self, pcp): 
        cheapest_vm = -1
        cheapest_sum = 9999999  #the initialized value should be a very large number

        for i in xrange(self.p_table.shape[0]):   # use the the shape of the performance table to identify how many VM types are there
            violate_LFT = 0
            start = self.G.node[pcp[len(pcp)-1]]['est'] 
            cost_sum = 0
            for j in xrange(len(pcp)-1, -1, -1):
                cost_sum += self.vm_price[i]
                if j == len(pcp)-1:
                    start = start + self.p_table[i, pcp[j]]
                else:
                    start = start + self.p_table[i, pcp[j]]+ self.G[pcp[j+1]][pcp[j]]['weight']
                    
                if self.G.node[pcp[j]]['lft'] < start:
                    violate_LFT = 1
                #launch a new instance of the cheapest service which can finish each task of P before its LFT
            if violate_LFT == 0 and cost_sum < cheapest_sum:
                cheapest_vm = i
                cheapest_sum = cost_sum
        for i in xrange(len(pcp)):
            self.assigned_list[pcp[i]] =  cheapest_vm
    
        return [cheapest_vm]*len(pcp)
  
     
    def generate_string(self, node):
        s = "name "+str(node)+"\n"
        for i in xrange(len(self.vm_price)):
            s = s+str(self.p_table[i, node])+"\n"
        s = s+"assigned vm: " + str(self.assigned_list[node]+1) 
        return s       
          
    def generateJSON(self):
        #load the cloud profile 
        with open('cloudprofile') as data_file:    
            data = json.load(data_file)
        
        print data
        
        content = {}
        for i in xrange(1, self.vertex_num-1, 1):
            content[str(i)] = data[str(i)]
            '''
            if self.assigned_list[i] == 0:
                content[str(i)] = 't2.large'
            if self.assigned_list[i] == 1:
                content[str(i)] = 't2.medium'
            if self.assigned_list[i] == 2:
                content[str(i)] = 't2.small'
            '''
        return content
    
    #calculate the total execution cost
    def cal_cost(self):
        cost = 0
        for vm in self.instances:
            cost = cost + vm.cost
        return cost
    
    def cal_cost1(self):
        cost = 0
        for i in range(1, len(self.assigned_list)-1):
            cost += self.vm_price[self.assigned_list[i]]
        
        return cost
        
    def has_edge_vm(self, vm1, vm2):
        for node1 in vm1.task_list:
            for node2 in vm2.task_list:
                if self.G.has_edge(node1, node2) or self.G.has_edge(node2, node1):
                    return True
        return False


