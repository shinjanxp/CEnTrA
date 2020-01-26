from json            import dumps, loads
import time
import unittest
import requests
# chainsapce
from chainspacecontract import transaction_to_solution
# from chainspacecontract.examples.surge import contract as surge_contract
from chainspacecontract.examples import surge
# crypto
from chainspacecontract.examples.utils import setup, key_gen, pack
from chainspaceapi import ChainspaceClient

G = setup()[0]
(provider_priv1, provider_pub1) = key_gen(setup())
(provider_priv2, provider_pub2) = key_gen(setup())
(provider_priv3, provider_pub3) = key_gen(setup())
client1 = ChainspaceClient(port=5000)
client2 = ChainspaceClient(port=5001)
client3 = ChainspaceClient(port=5000)

# Init txn
init_transaction = surge.init()
init_s0_token1 = init_transaction['transaction']['outputs'][0]
client1.process_transaction(init_transaction)

init_transaction = surge.init()
init_s1_token1 = init_transaction['transaction']['outputs'][0]
client2.process_transaction(init_transaction)

###########################################################################
############################  Client 1  ###################################
###########################################################################

# Create surge client
create_surge_client_txn = surge.create_surge_client(
    (init_s0_token1,),
    None,
    (pack(provider_pub1),),
    'Some info about the client.',
)
vote_slip1 = create_surge_client_txn['transaction']['outputs'][1]
surge_client1 = create_surge_client_txn['transaction']['outputs'][0]
client1.process_transaction(create_surge_client_txn)

###########################################################################
############################  Client 2  ###################################
###########################################################################

# Create surge client
create_surge_client_txn = surge.create_surge_client(
    (init_s1_token1,),
    None,
    (pack(provider_pub2),),
    'Some info about the client.',
)
vote_slip2 = create_surge_client_txn['transaction']['outputs'][1]
surge_client2 = create_surge_client_txn['transaction']['outputs'][0]
client2.process_transaction(create_surge_client_txn)

###########################################################################
#############  Clients 1 and 2 cast vote for client 3  ####################
###########################################################################


# Cast vote
cast_csc_vote_txn = surge.cast_csc_vote(
    (vote_slip1,),
    None,
    None,
    pack(provider_priv1),
    pack(provider_pub3),
)
vote_token1 = cast_csc_vote_txn['transaction']['outputs'][0]
vote_slip1 = cast_csc_vote_txn['transaction']['outputs'][1]
client1.process_transaction(cast_csc_vote_txn)

cast_csc_vote_txn = surge.cast_csc_vote(
    (vote_slip2,),
    None,
    None,
    pack(provider_priv2),
    pack(provider_pub3),
)
vote_token2 = cast_csc_vote_txn['transaction']['outputs'][0]
vote_slip2 = cast_csc_vote_txn['transaction']['outputs'][1]
client2.process_transaction(cast_csc_vote_txn)

###########################################################################
############################  Client 3  ###################################
###########################################################################

create_surge_client_txn = surge.create_surge_client(
    (vote_token1, vote_token2,),
    None,
    (pack(provider_pub3),),
    'Some info about the client.',
)
vote_slip3 = create_surge_client_txn['transaction']['outputs'][1]
surge_client3 = create_surge_client_txn['transaction']['outputs'][0]
client3.process_transaction(create_surge_client_txn)




# # Submit bid
# bid_transaction = energy_bidding.submit_bid(
#     (token,),
#     (meter,),
#     (dumps({'type':'EBBuy','energy':10,'price':50}),),
#     pack(provider_priv)
# )
# token = bid_transaction['transaction']['outputs'][0]
# bid = bid_transaction['transaction']['outputs'][1]
# client.process_transaction(bid_transaction)
