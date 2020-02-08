#!/usr/bin/env python
# coding: utf-8

# In[1]:


from json import dumps, loads
import time, os
import threading, Queue
import ast
import unittest
import requests
import random
import logging
# chainsapce
from chainspacecontract import transaction_to_solution
# from chainspacecontract.examples.surge import contract as surge_contract
from chainspacecontract.examples import surge
# crypto
from chainspacecontract.examples.utils import setup, key_gen, pack
from chainspaceapi import ChainspaceClient

# Setup logging
logging.basicConfig(level=logging.INFO, filename="execution.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
logging.info("Starting test_surge_bids")

# Setup variables
r = requests.get('http://10.129.6.52:4999/setup.in')
setup_str = r.text
setup_str = setup_str.split('\n')
NUM_SHARDS = int(setup_str[0])
NUM_REPLICAS = int(setup_str[1])
NUM_CLIENTS = int(setup_str[2])
logging.info("NUM_SHARDS: %s, NUM_REPLICAS: %s, NUM_CLIENTS: %s "%(NUM_SHARDS, NUM_REPLICAS, NUM_CLIENTS))
CS_HOST='10.129.6.52'
G = setup()[0]


# In[2]:


global_client = ChainspaceClient(host=CS_HOST,port=5000)
init_transaction = surge.init()
init_tokens = init_transaction['transaction']['outputs']
global_client.process_transaction(init_transaction)
client_divs = surge.eq_div(NUM_CLIENTS, NUM_SHARDS)
print client_divs


# In[3]:


# Create prosumer clients for locations 
clients = []
base_port=5000
sreps = []

for s in range(0,NUM_SHARDS):
    clients.append([])
    sreps.append(surge.SREPClient(host=CS_HOST, port=base_port+s))
    
    for c in range(0,client_divs[s]):
        clients[s].append(surge.SurgeClient(host=CS_HOST, port=base_port+s))

print clients

threads = []
for s in range(0,NUM_SHARDS):
    threads.append([])
    for c in range(0,client_divs[s]):
        client = clients[s][c]
        idx = sum(client_divs[:s]) + c
        threads[s].append(threading.Thread(target=client.create_surge_client, args=(init_tokens[idx],)) )

for s in range(0,NUM_SHARDS):
    for c in range(0,client_divs[s]):
        threads[s][c].start()

for s in range(0,NUM_SHARDS):
    for c in range(0,client_divs[s]):
        threads[s][c].join()


# In[5]:


# Create threads for casting srep vote

threads = []
queues = []

for s in range(0,NUM_SHARDS):
    que = Queue.Queue()
    threads.append([])
    for c in range(0,client_divs[s]):
        t = threading.Thread(target=clients[s][c].cast_srep_vote, args=(sreps[s].pub, que)) 
        threads[s].append(t)
    queues.append(que)

# Run bidding threads
start = time.time()
for s in range(0,NUM_SHARDS):
    for c in range(0,client_divs[s]):
        threads[s][c].start()

for s in range(0,NUM_SHARDS):
    for c in range(0,client_divs[s]):
        threads[s][c].join()

# Submit the votes
threads = []
for s in range(0,NUM_SHARDS):
    votes = []
    que = queues[s]
    while not que.empty():
        votes.append(que.get())
    client = sreps[s]
    t = threading.Thread(target=client.create_srep_client, args=(base_port+s, tuple(votes)) )
    threads.append(t)
    
for t in threads:
    t.start()
    
for t in threads:
    t.join()

end = time.time()
duration = end-start
logging.info("Execution took "+ str(duration))
logging.info("TPS: %s"%(NUM_CLIENTS/duration))


with open('stats.csv','a') as f:
    f.write("%s, %s, %s, %s\n"%(NUM_SHARDS, NUM_REPLICAS, NUM_CLIENTS, NUM_CLIENTS/duration))

