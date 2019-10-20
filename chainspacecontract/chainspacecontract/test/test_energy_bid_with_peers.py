from json            import dumps, loads
import time
import unittest
import requests
# chainsapce
from chainspacecontract import transaction_to_solution
# from chainspacecontract.examples.energy_bidding import contract as energy_bidding_contract
from chainspacecontract.examples import energy_bidding
# crypto
from chainspacecontract.examples.utils import setup, key_gen, pack
from chainspaceapi import ChainspaceClient

G = setup()[0]
(provider_priv, provider_pub) = key_gen(setup())
client = ChainspaceClient(port=5001)

# Init txn
init_transaction = energy_bidding.init()
token = init_transaction['transaction']['outputs'][0]
client.process_transaction(init_transaction)

# Create meter
create_meter_transaction = energy_bidding.create_meter(
    (token,),
    None,
    None,
    pack(provider_pub),
    'Some info about the meter.',
    dumps([5, 3, 5, 3, 5]),  # the tariffs
    dumps(764)               # billing period         
)
token = create_meter_transaction['transaction']['outputs'][2]
meter = create_meter_transaction['transaction']['outputs'][1]
client.process_transaction(create_meter_transaction)

# Submit bid
bid_transaction = energy_bidding.submit_bid(
    (token,),
    (meter,),
    (dumps({'type':'EBBuy','energy':10,'price':50}),),
    pack(provider_priv)
)
token = bid_transaction['transaction']['outputs'][0]
bid = bid_transaction['transaction']['outputs'][1]
client.process_transaction(bid_transaction)
