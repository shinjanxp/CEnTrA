"""A smart contract that implements a hierarchical distributed energy transaction platform."""

####################################################################
# imports
####################################################################
# general
from hashlib import sha256
from json    import dumps, loads
import os
import time, ast
import traceback
import requests
# chainspace
from chainspacecontract import ChainspaceContract
from chainspaceapi import ChainspaceClient
# crypto
from petlib.ecdsa import do_ecdsa_sign, do_ecdsa_verify
from chainspacecontract.examples.utils import setup, key_gen, pack, unpack

## contract name
contract = ChainspaceContract('centra')


## Class definitions for clients
DELTA = 5
class CentraClient:
        
    def __init__(self, host='127.0.0.1', port=5000, init_token=None):
        (self.priv, self.pub) = key_gen(setup())
        self.cs_client = ChainspaceClient(host=host, port=port)
        if init_token:
            self.create_centra_client(init_token)
        
    def create_centra_client(self,token):
        if type(token) is not tuple:
            token = (token,)
        create_centra_client_txn = create_centra_client(
            token,
            None,
            (pack(self.pub),),
            pack(self.priv),
        )
        self.centra_client = create_centra_client_txn['transaction']['outputs'][0]
        self.vote_slip = create_centra_client_txn['transaction']['outputs'][1]
        self.ebtoken = create_centra_client_txn['transaction']['outputs'][2]
        self.cs_client.process_transaction(create_centra_client_txn)
    
    def cast_csc_vote(self, client_pub):
        cast_csc_vote_txn = cast_csc_vote(
            (self.vote_slip,),
            None,
            None,
            pack(self.priv),
            pack(client_pub),
        )
        vote_token = cast_csc_vote_txn['transaction']['outputs'][0]
        self.vote_slip = cast_csc_vote_txn['transaction']['outputs'][1]
        self.cs_client.process_transaction(cast_csc_vote_txn)
        return vote_token

    def cast_lrep_vote(self, rep_pub, queue=None):
        cast_lrep_vote_txn = cast_lrep_vote(
            (self.vote_slip,),
            None,
            None,
            pack(self.priv),
            pack(rep_pub),
        )
        vote_token = cast_lrep_vote_txn['transaction']['outputs'][0]
        self.vote_slip = cast_lrep_vote_txn['transaction']['outputs'][1]
        self.cs_client.process_transaction(cast_lrep_vote_txn)
        if queue:
            queue.put(vote_token)
        return vote_token
    
    def submit_bid(self, bid_type, quantity):
        bid_proof_txn = submit_bid_proof(
            (self.ebtoken,),
            None,
            (bid_type,),
            pack(self.priv),
            quantity
        )
        bid_proof = bid_proof_txn['transaction']['outputs'][0]
        self.ebtoken = bid_proof_txn['transaction']['outputs'][1]
        self.cs_client.process_transaction(bid_proof_txn)
        # wait for others to submit their bid proofs
        # time.sleep(2*DELTA)
        
        # bid_txn = submit_bid(
        #     (bid_proof,),
        #     None,
        #     (quantity,),
        #     pack(self.priv)
        # )
        # bid = bid_txn['transaction']['outputs'][0]
        # self.cs_client.process_transaction(bid_txn)
        # return bid
        
class LREPClient (CentraClient):
    
    def create_lrep_client(self, host='127.0.0.1', lrep_port=5000, vote_tokens=None):
        self.lrep_cs_client = ChainspaceClient(host=host, port=lrep_port, max_wait=lrep_port-5000)
        create_lrep_client_txn = create_lrep_client(
            vote_tokens,
            None,
            (pack(self.pub),),
            pack(self.priv),
        )
        self.vote_slip = create_lrep_client_txn['transaction']['outputs'][1]
        self.lrep_client = create_lrep_client_txn['transaction']['outputs'][0]
        self.lrep_cs_client.process_transaction(create_lrep_client_txn)
        
    def accept_bids(self):
        time.sleep(DELTA)
        bid_proofs = self.lrep_cs_client.get_objects({'location':loads(self.lrep_client)['location'], 'type':'BidProof'})
        bidders = {}
        for bid in bid_proofs:
            bid = loads(bid)
            bidders[str(bid['quantity_sig'])]= True
        
        time.sleep(2*DELTA)
        buy_bids = self.lrep_cs_client.get_objects({'location':loads(self.lrep_client)['location'], 'type':'EBBuy'})
        sell_bids = self.lrep_cs_client.get_objects({'location':loads(self.lrep_client)['location'], 'type':'EBSell'})
        # process bid
        accepted_bids = []
        for bid in buy_bids:
            if not bidders.has_key(loads(bid)['quantity_sig']):
                continue
            accepted_bids.append(bid)
        for bid in sell_bids:
            if not bidders.has_key(loads(bid)['quantity_sig']):
                continue
            accepted_bids.append(bid)
        if len(accepted_bids)==0:
            return None
        accept_bids_txn = accept_bids(
            tuple(accepted_bids),
            None,
            (pack(self.pub),),
            pack(self.priv),
        )
        bid_accept = accept_bids_txn['transaction']['outputs'][0]
        self.lrep_cs_client.process_transaction(accept_bids_txn)
        return bid_accept
        
## Helper functions
def pb():
    print "**********************  BEGIN  ******************************"
def pe():
    print "***********************  END  *******************************"

def eq_div(N, i):
    return [] if i <= 0 else [N // i + 1] * (N % i) + [N // i] * (i - N % i)

def validate(object, keys):
    for key in keys:
        if not object.has_key(key):
            raise Exception("Invalid object format")
        if object[key] == None:
            raise Exception("Invalid object format")

def check_type(object, T):
    if not object['type'] == T:
        raise Exception("Invalid object type")

def equate(a, b):
    if a!=b:
        raise Exception(str(a) + "not equal to " + str(b))

def generate_sig(priv, msg = "proof"):
    hasher = sha256()
    hasher.update(msg)

    # sign message
    G = setup()[0]
    sig = do_ecdsa_sign(G, unpack(priv), hasher.digest())
    return pack(sig)

def validate_sig(sig, pub, msg="proof"):
    # check that the signature on the proof is correct
    hasher = sha256()
    hasher.update(msg)
    # verify signature
    (G, _, _, _) = setup()
    if not do_ecdsa_verify(G, unpack(pub), unpack(sig), hasher.digest()):
        raise Exception("Invalid signature")

####################################################################
# methods and checkers
####################################################################
# ------------------------------------------------------------------
# init
# ------------------------------------------------------------------
@contract.method('init')
def init():
    # Get setup variables from env

    NUM_SHARDS = int(os.getenv('NUM_SHARDS', 2))
    NUM_REPLICAS = int(os.getenv('NUM_REPLICAS', 4))
    NUM_CLIENTS = int(os.getenv('NUM_CLIENTS', 200))
        
    init_tokens = []
    client_divs = eq_div(NUM_CLIENTS, NUM_SHARDS)
    for l in range(0,NUM_SHARDS):
        for i in range(0,client_divs[l]):
            init_tokens.append(dumps({'type' : 'InitToken', 'location':l}))
    init_tokens = tuple(init_tokens)
    # return
    return {
        'outputs': init_tokens,
    }

# ------------------------------------------------------------------
# create centra client
# NOTE:
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand
# ------------------------------------------------------------------
@contract.method('create_centra_client')
def create_centra_client(inputs, reference_inputs, parameters, priv):

    pub = parameters[0]
    # new client
    new_centra_client = {
        'type'           : 'CentraClient', 
        'pub'            : pub, 
        'location'       : loads(inputs[0])['location'],
        'timestamp' : time.time()
    }
    vote_slip = {
        'type':'VoteSlipToken',
        'pub':pub,
        'location':loads(inputs[0])['location'],
        'timestamp' : time.time()
    }
    ebtoken = {
        'type':'EBToken',
        'pub':pub,
        'location':loads(inputs[0])['location'],
        'timestamp' : time.time()
    }
    # return
    return {
        'outputs': ( dumps(new_centra_client), dumps(vote_slip), dumps(ebtoken)),
        'extra_parameters': (
            generate_sig(priv),
        )
    }

# ------------------------------------------------------------------
# check create_centra_client
# ------------------------------------------------------------------
@contract.checker('create_centra_client')
def create_centra_client_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:
        REQUIRED_VOTES=2 # set to the number of CSCVoteTokens required to be accepted as a client

        # loads data
        centra_client = loads(outputs[0])
        vote_slip = loads(outputs[1])
        ebtoken = loads(outputs[2])
        
        # check argument lengths
        if len(inputs) < 1 or len(reference_inputs) != 0 or len(parameters)!=2 or len(outputs) != 3 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(centra_client, ['type','pub','location', 'timestamp'])
        validate(vote_slip, ['type','pub','location', 'timestamp'])
        validate(ebtoken, ['type','pub','location', 'timestamp'])
        
        # type checks
        # Since input can be InitToken or CSCVoteToken we cannot check type here
        check_type(centra_client, 'CentraClient')
        check_type(vote_slip, 'VoteSlipToken')
        check_type(ebtoken, 'EBToken')
        # explicit type checks
        if not(loads(inputs[0])['type'] == 'InitToken' or loads(inputs[0])['type'] == 'CSCVoteToken'):
            raise Exception("Invalid input token types")
        # equality checks
        equate(centra_client['pub'], parameters[0])
        equate(centra_client['pub'], vote_slip['pub'])
        equate(centra_client['pub'], ebtoken['pub'])
        equate(centra_client['location'], vote_slip['location'])
        equate(centra_client['location'], loads(inputs[0])['location'])
        equate(centra_client['location'], ebtoken['location'])
        
        # signature validation
        validate_sig(parameters[1], parameters[0])

        # contract logic
        if loads(inputs[0])['type'] == 'InitToken' :
            return True
        # validate CSC votes if InitToken is not provided
        voters = {}
        for vote in inputs:
            vote = loads(vote)
            check_type(vote, 'CSCVoteToken')
            equate(vote['granted_to'], parameters[0])
            voters[str(vote['granted_by'])]= True
        
        if len(voters) < REQUIRED_VOTES:
            raise Exception("Not enough voters")

    except Exception as e:
        print e
        return False    
    
    return True


# ------------------------------------------------------------------
# cast csc (create centra client) vote
# NOTE:
#   - cast a vote to allow a new client to be added to the platform
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand 
#   - inputs must contain a valid VoteSlipToken
#   - parameters contain a proof signed by the caster's private key
#   - the CentraClient object will be used to validate the signature
# ------------------------------------------------------------------
@contract.method('cast_csc_vote')
def cast_csc_vote(inputs, reference_inputs, parameters, centra_client_priv, granted_to_pub):

    # vote_slip = inputs[0]
    # proof = parameters[0]
    granted_by_pub = loads(inputs[0])['pub']

    vote_token = {
        'type'          : 'CSCVoteToken', 
        'granted_by'    : granted_by_pub,
        'granted_to'    : granted_to_pub,
        'location'      : loads(inputs[0])['location'],
        'timestamp' :   time.time()
    }

    return {
        'outputs': ( dumps(vote_token), inputs[0]),
        'extra_parameters': (
            generate_sig(centra_client_priv),
        )
    }
    
# ------------------------------------------------------------------
# check cast_csc_vote
# ------------------------------------------------------------------
@contract.checker('cast_csc_vote')
def cast_csc_vote_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:

        # loads data
        vote_slip = loads(inputs[0])
        vote_token = loads(outputs[0])
        new_vote_slip = loads(outputs[1])
        
        # check argument lengths
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(parameters)!=1 or len(outputs) != 2 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(vote_token, ['type','granted_by', 'granted_to','location', 'timestamp'])
        validate(new_vote_slip, ['type','pub','location', 'timestamp'])
        # type checks
        check_type(vote_slip, 'VoteSlipToken')
        check_type(vote_token, 'CSCVoteToken')
        check_type(new_vote_slip, 'VoteSlipToken')
        # equality checks
        equate(vote_slip['pub'], new_vote_slip['pub'])
        equate(vote_slip['location'], new_vote_slip['location'])
        equate(vote_token['granted_by'], vote_slip['pub'])
        equate(vote_token['location'], vote_slip['location'])        
        # signature validation
        validate_sig(parameters[0], vote_slip['pub'])
        
    except Exception as e:
        print e
        return False
    return True



# ------------------------------------------------------------------
# cast lrep (shard representative) vote 
# NOTE:
#   - cast a vote to allow a client to act as shard representative
#   - inputs must contain a valid VoteSlipToken
#   - parameters contain a proof signed by the caster's private key
# ------------------------------------------------------------------
@contract.method('cast_lrep_vote')
def cast_lrep_vote(inputs, reference_inputs, parameters, priv, granted_to_pub):

    # vote_slip = inputs[0]
    # proof = parameters[0]
    granted_by_pub = loads(inputs[0])['pub']

    vote_token = {
        'type'          : 'LREPVoteToken', 
        'granted_by'    : granted_by_pub,
        'granted_to'    : granted_to_pub,
        'location'      : loads(inputs[0])['location'],
        'timestamp'     : time.time()
    }

    return {
        'outputs': ( dumps(vote_token), inputs[0]),
        'extra_parameters': (
            generate_sig(priv),
        )
    }
    
# ------------------------------------------------------------------
# check cast_lrep_vote
# ------------------------------------------------------------------
@contract.checker('cast_lrep_vote')
def cast_lrep_vote_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:

        # loads data
        vote_slip = loads(inputs[0])
        vote_token = loads(outputs[0])
        new_vote_slip = loads(outputs[1])
        
        # check argument lengths
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(parameters)!=1 or len(outputs) != 2 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(vote_token, ['type','granted_by', 'granted_to','location', 'timestamp'])
        validate(new_vote_slip, ['type','pub','location', 'timestamp'])
        # type checks
        check_type(vote_slip, 'VoteSlipToken')
        check_type(vote_token, 'LREPVoteToken')
        check_type(new_vote_slip, 'VoteSlipToken')
        # equality checks
        equate(vote_slip['pub'], new_vote_slip['pub'])
        equate(vote_slip['location'], new_vote_slip['location'])
        equate(vote_token['granted_by'], vote_slip['pub'])
        equate(vote_token['location'], vote_slip['location'])        
        # signature validation
        validate_sig(parameters[0], vote_slip['pub'])
        
    except Exception as e:
        print e
        return False
    return True


# ------------------------------------------------------------------
# create lrep client
# NOTE:
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand
# ------------------------------------------------------------------
@contract.method('create_lrep_client')
def create_lrep_client(inputs, reference_inputs, parameters, priv):

    pub = parameters[0]
    # new client
    lrep_client = {
        'type'           : 'LREPClient', 
        'pub'            : pub, 
        'location'       : loads(inputs[0])['location'],
        'timestamp'      : time.time()
    }
    vote_slip = {
        'type':'VoteSlipToken',
        'pub':pub,
        'location':loads(inputs[0])['location'],
        'timestamp'      : time.time()
    }
    # return
    return {
        'outputs': ( dumps(lrep_client), dumps(vote_slip)),
        'extra_parameters': (
            generate_sig(priv),
        )
    }

# ------------------------------------------------------------------
# check create_lrep_client
# ------------------------------------------------------------------
@contract.checker('create_lrep_client')
def create_lrep_client_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:
        REQUIRED_VOTES=2 # set to the number of CSCVoteTokens required to be accepted as a client

        # loads data
        lrep_client = loads(outputs[0])
        vote_slip = loads(outputs[1])
        lrep_vote_1 = loads(inputs[0])
        
        # check argument lengths
        if len(reference_inputs) != 0 or len(parameters)!=2 or len(outputs) != 2 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(lrep_client, ['type','pub','location', 'timestamp'])
        validate(vote_slip, ['type','pub','location', 'timestamp'])
        validate(lrep_vote_1, ['type','granted_by', 'granted_to','location', 'timestamp'])
        
        # type checks
        check_type(lrep_client, 'LREPClient')
        check_type(vote_slip, 'VoteSlipToken')
        check_type(lrep_vote_1, 'LREPVoteToken')
        # equality checks
        equate(lrep_client['pub'], parameters[0])
        equate(lrep_client['pub'], vote_slip['pub'])
        equate(lrep_client['location'], vote_slip['location'])
        equate(lrep_client['location'], lrep_vote_1['location'])
        
        # signature validation
        validate_sig(parameters[1], parameters[0])

        # validate CSC votes if InitToken is not provided
        voters = {}
        for vote in inputs:
            vote = loads(vote)
            check_type(vote, 'LREPVoteToken')
            equate(vote['granted_to'], parameters[0])
            equate(vote['location'], lrep_client['location'])
            voters[str(vote['granted_by'])]= True
        
        if len(voters) < REQUIRED_VOTES:
            raise Exception("Not enough voters")

    except Exception as e:
        print e
        return False    
    
    return True




# ------------------------------------------------------------------
# submit bid proof
# NOTE:
#   - before making a bit each client must submit a bid hash to prove the bid value
#   - inputs must contain a valid EBToken
#   - parameters must contain the bid type
#   - outputs must contain a valid BidProof and another EBToken
#   - client's private key to be provided as extra argument to be used for signature
#   - bid quantity to be provided as extra argument 
# ------------------------------------------------------------------
@contract.method('submit_bid_proof')
def submit_bid_proof(inputs, reference_inputs, parameters, priv, quantity):
    ebtoken = loads(inputs[0])
    bid_proof = {
        'type':'BidProof',
        'bid_type' : parameters[0],
        'quantity_sig' : generate_sig(priv, '{}|{}'.format(quantity, ebtoken['pub'])),
        'pub':ebtoken['pub'],
        'location' : ebtoken['location'],
        'timestamp' : time.time()
    }
    return {
        'outputs' : (dumps(bid_proof), dumps(ebtoken)),
        'extra_parameters': (generate_sig(priv),)
    }
# ------------------------------------------------------------------
# check submit_bid_proof
# ------------------------------------------------------------------
@contract.checker('submit_bid_proof')
def submit_bid_proof_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:

        # loads data
        old_ebtoken = loads(inputs[0])
        bid_proof = loads(outputs[0])
        new_ebtoken = loads(outputs[1])
        
        # check argument lengths
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(parameters)!=2 or len(outputs) != 2 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(old_ebtoken, ['type','pub','location', 'timestamp'])
        validate(bid_proof, ['type', 'bid_type', 'quantity_sig', 'pub', 'location', 'timestamp'])
        validate(new_ebtoken, ['type','pub','location', 'timestamp'])
        # type checks
        check_type(old_ebtoken, 'EBToken')
        check_type(new_ebtoken, 'EBToken')
        check_type(bid_proof, 'BidProof')
        # equality checks
        equate(old_ebtoken['pub'], bid_proof['pub'])
        equate(old_ebtoken['pub'], new_ebtoken['pub'])

        equate(old_ebtoken['location'], bid_proof['location'])
        equate(old_ebtoken['location'], new_ebtoken['location'])        
        # signature validation
        validate_sig(parameters[1], old_ebtoken['pub'])
        
    except Exception as e:
        print e
        return False
    return True


# ------------------------------------------------------------------
# submit bid
# NOTE:
#   - make a bid for buying or selling some fixed unit of energy for the next time slot
#   - inputs must contain a valid BidProof object
#   - outputs must contain a valid EBBuy or EBSell object
#   - client's private key to be provided as extra argument to be used for signature
#   - 
# ------------------------------------------------------------------
@contract.method('submit_bid')
def submit_bid(inputs, reference_inputs, parameters, priv):
    bid_proof = loads(inputs[0])
    bid = {
        'type' : bid_proof['bid_type'],
        'quantity' : parameters[0],
        'quantity_sig':bid_proof['quantity_sig'],
        'pub':bid_proof['pub'],
        'location' : bid_proof['location'], 
        'timestamp' : time.time()
    }
    return {
        'outputs' : (dumps(bid),),
        'extra_parameters': (generate_sig(priv),)
    }
# ------------------------------------------------------------------
# check submit_bid
# ------------------------------------------------------------------
@contract.checker('submit_bid')
def submit_bid_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:

        # loads data
        bid_proof = loads(inputs[0])
        bid = loads(outputs[0])
        
        # check argument lengths
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(parameters)!=2 or len(outputs) != 1 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(bid_proof, ['type', 'bid_type', 'quantity_sig','pub','location', 'timestamp'])
        validate(bid, ['type', 'quantity', 'quantity_sig', 'pub', 'location', 'timestamp'])
        # type checks
        check_type(bid_proof, 'BidProof')
        if not (bid['type'] == 'EBBuy' or bid['type'] == 'EBSell'):
            raise Exception("Invalid bid type")
        # equality checks
        equate(bid_proof['pub'], bid['pub'])
        equate(bid_proof['quantity_sig'], bid['quantity_sig'])

        equate(bid_proof['location'], bid['location'])     
        # signature validation
        validate_sig(parameters[1], bid_proof['pub'])

        # quantity signature validation
        validate_sig(bid_proof['quantity_sig'], bid_proof['pub'], '{}|{}'.format(bid['quantity'], bid['pub']))

        
    except Exception as e:
        print e
        return False
    return True



# ------------------------------------------------------------------
# accept bids
# NOTE:
#   - LREP executes this contract to accept bids and calculate diff
#   - inputs must contain list of EBBuy or EBSell objects
#   - outputs must contain a valid EBAccept object
#   - client's private key to be provided as extra argument to be used for signature
#   - 
# ------------------------------------------------------------------
@contract.method('accept_bids')
def accept_bids(inputs, reference_inputs, parameters, priv):
    total_buy = 0
    total_sell = 0
    for bid in inputs:
        b = loads(bid)
        if b['type'] == 'EBBuy':
            total_buy+= b['quantity']
        if b['type'] == 'EBSell':
            total_sell+= b['quantity']
    
    bid_accept = {
        'type' : 'BidAccept',
        'total_buy' : total_buy,
        'total_sell' : total_sell,
        'pub': parameters[0],
        'location' : loads(inputs[0])['location'],
        'timestamp' : time.time()
    }
    return {
        'outputs' : (dumps(bid_accept),),
        'extra_parameters': (generate_sig(priv),)
    }
# ------------------------------------------------------------------
# check accept_bids
# ------------------------------------------------------------------
@contract.checker('accept_bids')
def accept_bids_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:

        # loads data
        bid_accept = loads(outputs[0])
        
        # check argument lengths
        if len(inputs) < 1 or len(reference_inputs) != 0 or len(parameters)!=2 or len(outputs) != 1 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(bid_accept, ['type', 'total_buy', 'total_sell','pub','location', 'timestamp'])
        # type checks
        check_type(bid_accept, 'BidAccept')
        # equality checks
        total_buy = 0
        total_sell = 0
        for bid in inputs:
            b = loads(bid)
            equate(bid_accept['location'], b['location'])
            if b['type'] == 'EBBuy':
                total_buy+= b['quantity']
            if b['type'] == 'EBSell':
                total_sell+= b['quantity']

        equate(total_buy, bid_accept['total_buy'])
        equate(total_sell, bid_accept['total_sell'])
        # signature validation
        validate_sig(parameters[1], parameters[0])

        
    except Exception as e:
        traceback.print_exc()
        return False
    return True

####################################################################
# main
####################################################################
if __name__ == '__main__':
    contract.run()



####################################################################
