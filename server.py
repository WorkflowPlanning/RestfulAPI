from flask import Flask, request, jsonify
import networkx as nx
import sys
import numpy as np

app = Flask(__name__)
from ICPCP import Workflow

def jsonParser(content):
    print content['workflow']
    print content['performance']
    print content['price']
    print content['deadline']

    #parse the workflow
    G = nx.DiGraph()
    
    for (key, value) in content['workflow'].items():
        if isinstance(value, list) :
            if key == 'nodes' :
                vertex_num = len(value)
                for node in value:
                    G.add_node(node['name'], est = -1, eft = -1, lft =-1)    
            if key == 'links' :
                for link in value:
                    G.add_weighted_edges_from([(link['source'], link['target'], link['throughput'])])
    print G.nodes
    
    #parse the performance matrix
    p_table = []
    for (key, value) in content['performance'].items():
        row = []
        row.append(0)
        for i in value.split(','):
            row.append(int(i))
        row.append(0)
        print row
        p_table.append(row)
    
    #parse the price vector
    vm_price = []
    for i in content['price'].split(','):
        vm_price.append(int(i))
    
    #parse the deadline
    d_list = []
    for (key, value) in content['deadline'].items():
        d_list.append([int(key), int(value)]) 
    
@app.route('/api/add_message/<uuid>', methods=['GET', 'POST'])
def add_message(uuid):
    content = request.json
    wf = Workflow()
    wf.init(content)
    wf.ic_pcp()
    #print content['workflow']
    #return 
    print wf.generateJSON()
    return jsonify({"inf":wf.generateJSON()})

if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True)
