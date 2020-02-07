#!/usr/bin/env python
# coding: utf-8

# In[1]:


from json import dumps, loads
import time, os
import threading 
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


for s in range(0,NUM_SHARDS):
    clients.append([])
    for c in range(0,client_divs[s]):
        
#         clients[s].append(surge.SurgeClient(host=CS_HOST, port=base_port+s, init_token=init_tokens[idx]))
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

# c00 = surge.SurgeClient(5000, init_token[0]) # location=0
# Create sreps for locations 0 and 1 which will be clients in location 2
# rep0 = surge.SREPClient(5002, init_token[4]) # location=2

# Elect rep1 as SREP for location 0
# votes = (c00.cast_srep_vote(rep0.pub), c01.cast_srep_vote(rep0.pub))
# rep0.create_srep_client(5000, votes) 

# Elect rep2 as SREP for location 1
# votes = (c10.cast_srep_vote(rep1.pub), c11.cast_srep_vote(rep1.pub))
# rep1.create_srep_client(5001, votes) 


# In[4]:


# Create threads for bidding
threads = []
for s in range(0,NUM_SHARDS):
    threads.append([])
    for c in range(0,client_divs[s]):
        client = clients[s][c]
        bid_value = random.randint(0,100)
        threads[s].append(threading.Thread(target=client.submit_bid, args=(random.choice(['EBBuy', 'EBSell']),bid_value)) )

# trep0 = threading.Thread(target=rep0.accept_bids) 


# In[5]:


# Run bidding threads
start = time.time()
for s in range(0,NUM_SHARDS):
    for c in range(0,client_divs[s]):
        threads[s][c].start()

for s in range(0,NUM_SHARDS):
    for c in range(0,client_divs[s]):
        threads[s][c].join()

end = time.time()
duration = end-start
logging.info("Execution took "+ str(duration))
logging.info("TPS: %s"%(NUM_CLIENTS/duration))


# In[6]:


# '{}|{}'.format(50, loads(r1.ebtoken)['pub'])
# global_client.fix_json("{'type':'EBBuy','location':0")
# global_client = ChainspaceClient(port=5001)
# global_client.get_objects({'location':0,'type':'BidAccept'})
# print buy_bids

# print loads(objs[0])['type']
# bid_proofs = rep1.client.get_objects({ 'type':'EBBuy'})
# print init_token1

