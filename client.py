from toscaparser import *
from toscaparser.tosca_template import ToscaTemplate
import os
import sys
import random
import re
import operator
import requests
import time
    
if __name__ == '__main__':
    path = "input.yaml"
    import sys, argparse
 
    a_file = os.path.isfile(path)
    tosca = ToscaTemplate(path)
    #print tosca.tpl
    json = tosca.tpl.get('topology_template').get('node_templates')
    #print json
    deadline = 0

    for j in json:
        #print json[j]
        if not json[j]['type'] == "Switch.nodes.Application.Connection":
	    deadline = int(re.search(r'\d+', json[j]['properties']['QoS']['response_time']).group())

    #get the nodes from the json
    nodeDic = {}
    nodeDic1 = {}
    i = 1
    for j in json:
        if not json[j]['type'] == "Switch.nodes.Application.Connection":
            print j, json[j]
	    nodeDic[j] = i
        nodeDic1[i] = j
        i = i + 1

    #get the links from the json
    links = []
    for j in json:
	if json[j]['type'] == "Switch.nodes.Application.Connection":
	    print json[j]['properties']['source']['component_name']
	    print json[j]['properties']['target']['component_name']
    	    link= {}
	    link['source'] = nodeDic[json[j]['properties']['source']['component_name']]
	    link['target'] = nodeDic[json[j]['properties']['target']['component_name']]
	    link['weight'] = random.randint(1, 10)
	    links.append(link)

    # compose the json as input of the workflow
    wfJson = {}
    wfJson['workflow'] = {}

    nodesList = []
    sorted_nodeDic = sorted(nodeDic.items(), key=operator.itemgetter(1))
    for key, value in sorted_nodeDic:
    	v = {}
    	v['name'] = value
    	nodesList.append(v)
    wfJson['workflow']['nodes'] = nodesList
    wfJson['workflow']['links'] = links
    #print deadline
    
    wfJson['price'] = "5,2,1"
    wfJson['deadline'] = {'2': deadline}

    #generate performance
    performance = {}
    for key, value in sorted_nodeDic:
	performance[str(value)] = "1,2,3"
    wfJson['performance'] = performance
    
    print wfJson

    #send request to the server
    start = time.time()

    res = requests.post('http://145.100.133.143:5000/api/add_message/1234', json=wfJson)
    if res.ok:
        print res.json()
    end = time.time()
    print (end - start)
    topoName = "9bf16845-b0d7-4053-875f-f60333289e20"
    with open('planner_output_all.yml', 'w') as the_file:
        the_file.write('topologies:\n')
        the_file.write('  - topology: '+topoName+'\n')
        the_file.write('    cloudProvider: EC2\n')
    
    with open(topoName+'.yml', 'w') as the_file:
        the_file.write('publicKeyPath: /Users/zh9314/SWITCH/users/zh9314/files/1479928399024/id_dsa.pub\nuserName: zh9314\nsubnets:\n  - name: s1\n    subnet: 192.168.10.0\n    netmask: 255.255.255.0\ncomponents:\n')
        i = 0
        for key, value in sorted_nodeDic:
            if i % 2 == 0:
                the_file.write('  - name: '+'a0acbc80-791f-45d7-8491-aab919dccdaa'+'\n')
                the_file.write('    type: Switch.nodes.Compute\n    nodetype: ')
                the_file.write(res.json()['inf'][str(value)])
                the_file.write('\n')
                the_file.write('    OStype: \"Ubuntu 16.04\"\n    domain: \"ec2.us-east-1.amazonaws.com\"\n    script: null\n    installation: null\n    role: master\n    dockers: \"mogswitch/InputDistributor\"\n    public_address: a0acbc80-791f-45d7-8491-aab919dccdaa\n    ethernet_port: \n      - name: p1\n        subnet_name: s1\n        address: 192.168.10.10 ')
            else:
                the_file.write('  - name: '+nodeDic1[value]+'\n')
                the_file.write('    type: Switch.nodes.Compute\n    nodetype: ')
                the_file.write(res.json()['inf'][str(value)])
                the_file.write('\n')               
                the_file.write('    OStype: \"Ubuntu 16.04\"\n    domain: \"ec2.us-east-1.amazonaws.com\"\n    script: null\n    installation: null\n    role: slave\n    dockers: \"mogswitch/ProxyTranscoder\"\n    public_address: 7cffd689-d282-45dd-a73a-fbeefb12ea97\n    ethernet_port: \n      - name: p1\n        subnet_name: s1\n        address: 192.168.10.11 ')
                