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
# from chainspacecontract.examples.centra import contract as centra_contract
from chainspacecontract.examples import centra
# crypto
from chainspacecontract.examples.utils import setup, key_gen, pack
from chainspaceapi import ChainspaceClient

# Get setup variables from env

RUN_ID = os.getenv('RUN_ID', str(random.randint(1, 999)))
NUM_SHARDS = int(os.getenv('NUM_SHARDS', 2))
NUM_REPLICAS = int(os.getenv('NUM_REPLICAS', 4))
NUM_CLIENTS = int(os.getenv('NUM_CLIENTS', 200))
CS_HOST=os.getenv('PEERS_HOST', 'localhost')

# Setup logging
logging.basicConfig(level=logging.INFO, filename="../../../stats/"+RUN_ID+"_execution.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
logging.info("Starting test_centra_bids")


logging.info("NUM_SHARDS: %s, NUM_REPLICAS: %s, NUM_CLIENTS: %s "%(NUM_SHARDS, NUM_REPLICAS, NUM_CLIENTS))
G = setup()[0]


# In[2]:


global_client = ChainspaceClient(host=CS_HOST,port=5000)
init_transaction = centra.init()
init_tokens = init_transaction['transaction']['outputs']
global_client.process_transaction(init_transaction)
client_divs = centra.eq_div(NUM_CLIENTS, NUM_SHARDS)
print client_divs


# In[3]:


# Create prosumer clients for locations 
clients = []
base_port=5000


for s in range(0,NUM_SHARDS):
    clients.append([])
    for c in range(0,client_divs[s]):
        
#         clients[s].append(centra.CentraClient(host=CS_HOST, port=base_port+s, init_token=init_tokens[idx]))
        clients[s].append(centra.CentraClient(host=CS_HOST, port=base_port+s))

print clients

threads = []
for s in range(0,NUM_SHARDS):
    threads.append([])
    for c in range(0,client_divs[s]):
        client = clients[s][c]
        idx = sum(client_divs[:s]) + c
        threads[s].append(threading.Thread(target=client.create_centra_client, args=(init_tokens[idx],)) )

for s in range(0,NUM_SHARDS):
    for c in range(0,client_divs[s]):
        threads[s][c].start()

for s in range(0,NUM_SHARDS):
    for c in range(0,client_divs[s]):
        threads[s][c].join()

# c00 = centra.CentraClient(5000, init_token[0]) # location=0
# Create sreps for locations 0 and 1 which will be clients in location 2
# rep0 = centra.SREPClient(5002, init_token[4]) # location=2

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

with open('../../../stats/'+RUN_ID+'_stats.csv','a') as f:
    f.write("%s, %s, %s, %s\n"%(NUM_SHARDS, NUM_REPLICAS, NUM_CLIENTS, NUM_CLIENTS/duration))

# In[6]:


# '{}|{}'.format(50, loads(r1.ebtoken)['pub'])
# global_client.fix_json("{'type':'EBBuy','location':0")
# global_client = ChainspaceClient(port=5001)
# global_client.get_objects({'location':0,'type':'BidAccept'})
# print buy_bids

# print loads(objs[0])['type']
# bid_proofs = rep1.client.get_objects({ 'type':'EBBuy'})
# print init_token1

