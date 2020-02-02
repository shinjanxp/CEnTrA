"""A smart contract that implements a hierarchical distributed energy transaction platform."""

####################################################################
# imports
####################################################################
# general
from hashlib import sha256
from json    import dumps, loads
# chainspace
from chainspacecontract import ChainspaceContract
# crypto
from petlib.ecdsa import do_ecdsa_sign, do_ecdsa_verify
from chainspacecontract.examples.utils import setup, key_gen, pack, unpack

## contract name
contract = ChainspaceContract('surge')

## Helper functions
def pb():
    print "**********************  BEGIN  ******************************"
def pe():
    print "***********************  END  *******************************"

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

def generate_sig(priv):
    hasher = sha256()
    hasher.update("proof")

    # sign message
    G = setup()[0]
    sig = do_ecdsa_sign(G, unpack(priv), hasher.digest())
    return pack(sig)

def validate_sig(sig, pub):
    # check that the signature on the proof is correct
    hasher = sha256()
    hasher.update("proof")
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

    # return
    return {
        'outputs': (dumps({'type' : 'InitToken', 'location':0}),
        dumps({'type' : 'InitToken', 'location':0}),
        dumps({'type' : 'InitToken', 'location':1}),
        dumps({'type' : 'InitToken', 'location':1})),
    }

# ------------------------------------------------------------------
# create surge client
# NOTE:
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand
# ------------------------------------------------------------------
@contract.method('create_surge_client')
def create_surge_client(inputs, reference_inputs, parameters, priv):

    pub = parameters[0]
    # new client
    new_surge_client = {
        'type'           : 'SurgeClient', 
        'pub'            : pub, 
        'location'       : loads(inputs[0])['location']
    }
    vote_slip = {
        'type':'VoteSlipToken',
        'pub':pub,
        'location':loads(inputs[0])['location']
    }
    ebtoken = {
        'type':'EBToken',
        'pub':pub,
        'location':loads(inputs[0])['location']
    }
    # return
    return {
        'outputs': ( dumps(new_surge_client), dumps(vote_slip), dumps(ebtoken)),
        'extra_parameters': (
            generate_sig(priv),
        )
    }

# ------------------------------------------------------------------
# check create_surge_client
# ------------------------------------------------------------------
@contract.checker('create_surge_client')
def create_surge_client_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:
        REQUIRED_VOTES=2 # set to the number of CSCVoteTokens required to be accepted as a client

        # loads data
        surge_client = loads(outputs[0])
        vote_slip = loads(outputs[1])
        ebtoken = loads(outputs[2])
        
        # check argument lengths
        if len(reference_inputs) != 0 or len(parameters)!=2 or len(outputs) != 3 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(surge_client, ['type','pub','location'])
        validate(vote_slip, ['type','pub','location'])
        validate(ebtoken, ['type','pub','location'])
        
        # type checks
        # Since input can be InitToken or CSCVoteToken we cannot check type here
        check_type(surge_client, 'SurgeClient')
        check_type(vote_slip, 'VoteSlipToken')
        check_type(ebtoken, 'EBToken')
        # explicit type checks
        if not(loads(inputs[0])['type'] == 'InitToken' or loads(inputs[0])['type'] == 'CSCVoteToken'):
            raise Exception("Invalid input token types")
        # equality checks
        equate(surge_client['pub'], parameters[0])
        equate(surge_client['pub'], vote_slip['pub'])
        equate(surge_client['pub'], ebtoken['pub'])
        equate(surge_client['location'], vote_slip['location'])
        equate(surge_client['location'], loads(inputs[0])['location'])
        equate(surge_client['location'], ebtoken['location'])
        
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
# cast csc (create surge client) vote
# NOTE:
#   - cast a vote to allow a new client to be added to the platform
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand 
#   - inputs must contain a valid VoteSlipToken
#   - parameters contain a proof signed by the caster's private key
#   - the SurgeClient object will be used to validate the signature
# ------------------------------------------------------------------
@contract.method('cast_csc_vote')
def cast_csc_vote(inputs, reference_inputs, parameters, surge_client_priv, granted_to_pub):

    # vote_slip = inputs[0]
    # proof = parameters[0]
    granted_by_pub = loads(inputs[0])['pub']

    vote_token = {
        'type'          : 'CSCVoteToken', 
        'granted_by'    : granted_by_pub,
        'granted_to'    : granted_to_pub,
        'location'      : loads(inputs[0])['location']
    }

    return {
        'outputs': ( dumps(vote_token), inputs[0]),
        'extra_parameters': (
            generate_sig(surge_client_priv),
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
        validate(vote_token, ['type','granted_by', 'granted_to','location'])
        validate(new_vote_slip, ['type','pub','location'])
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
# cast srep (shard representative) vote 
# NOTE:
#   - cast a vote to allow a client to act as shard representative
#   - inputs must contain a valid VoteSlipToken
#   - parameters contain a proof signed by the caster's private key
# ------------------------------------------------------------------
@contract.method('cast_srep_vote')
def cast_srep_vote(inputs, reference_inputs, parameters, priv, granted_to_pub):

    # vote_slip = inputs[0]
    # proof = parameters[0]
    granted_by_pub = loads(inputs[0])['pub']

    vote_token = {
        'type'          : 'SREPVoteToken', 
        'granted_by'    : granted_by_pub,
        'granted_to'    : granted_to_pub,
        'location'      : loads(inputs[0])['location']
    }

    return {
        'outputs': ( dumps(vote_token), inputs[0]),
        'extra_parameters': (
            generate_sig(priv),
        )
    }
    
# ------------------------------------------------------------------
# check cast_srep_vote
# ------------------------------------------------------------------
@contract.checker('cast_srep_vote')
def cast_srep_vote_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:

        # loads data
        vote_slip = loads(inputs[0])
        vote_token = loads(outputs[0])
        new_vote_slip = loads(outputs[1])
        
        # check argument lengths
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(parameters)!=1 or len(outputs) != 2 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(vote_token, ['type','granted_by', 'granted_to','location'])
        validate(new_vote_slip, ['type','pub','location'])
        # type checks
        check_type(vote_slip, 'VoteSlipToken')
        check_type(vote_token, 'SREPVoteToken')
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
# create srep client
# NOTE:
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand
# ------------------------------------------------------------------
@contract.method('create_srep_client')
def create_srep_client(inputs, reference_inputs, parameters, priv):

    pub = parameters[0]
    # new client
    srep_client = {
        'type'           : 'SREPClient', 
        'pub'            : pub, 
        'location'       : loads(inputs[0])['location']
    }
    vote_slip = {
        'type':'VoteSlipToken',
        'pub':pub,
        'location':loads(inputs[0])['location']
    }
    # return
    return {
        'outputs': ( dumps(srep_client), dumps(vote_slip)),
        'extra_parameters': (
            generate_sig(priv),
        )
    }

# ------------------------------------------------------------------
# check create_srep_client
# ------------------------------------------------------------------
@contract.checker('create_srep_client')
def create_srep_client_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:
        REQUIRED_VOTES=2 # set to the number of CSCVoteTokens required to be accepted as a client

        # loads data
        srep_client = loads(outputs[0])
        vote_slip = loads(outputs[1])
        srep_vote_1 = loads(inputs[0])
        
        # check argument lengths
        if len(reference_inputs) != 0 or len(parameters)!=2 or len(outputs) != 2 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(srep_client, ['type','pub','location'])
        validate(vote_slip, ['type','pub','location'])
        validate(srep_vote_1, ['type','granted_by', 'granted_to','location'])
        
        # type checks
        check_type(srep_client, 'SREPClient')
        check_type(vote_slip, 'VoteSlipToken')
        check_type(srep_vote_1, 'SREPVoteToken')
        # equality checks
        equate(srep_client['pub'], parameters[0])
        equate(srep_client['pub'], vote_slip['pub'])
        equate(srep_client['location'], vote_slip['location'])
        equate(srep_client['location'], srep_vote_1['location'])
        
        # signature validation
        validate_sig(parameters[1], parameters[0])

        # validate CSC votes if InitToken is not provided
        voters = {}
        for vote in inputs:
            vote = loads(vote)
            check_type(vote, 'SREPVoteToken')
            equate(vote['granted_to'], parameters[0])
            equate(vote['location'], srep_client['location'])
            voters[str(vote['granted_by'])]= True
        
        if len(voters) < REQUIRED_VOTES:
            raise Exception("Not enough voters")

    except Exception as e:
        print e
        return False    
    
    return True


# ------------------------------------------------------------------
# submit bid
# NOTE:
#   - make a bid for buying or selling some fixed unit of energy for the next time slot
#   - inputs must contain a valid EBToken
#   - outputs must contain a valid EBBuy or EBSell object and another EBToken
#   - client's private key to be provided as extra argument to be used for signature
#   - 
# ------------------------------------------------------------------
@contract.method('submit_bid')
def submit_bid(inputs, reference_inputs, parameters, priv):
    ebtoken = loads(inputs[0])
    bid = {
        'type' : parameters[0],
        'quantity' : parameters[1],
        'pub':ebtoken['pub'],
        'location' : ebtoken['location']
    }
    return {
        'outputs' : (dumps(bid), dumps(ebtoken)),
        'extra_parameters': (generate_sig(priv),)
    }
# ------------------------------------------------------------------
# check submit_bid
# ------------------------------------------------------------------
@contract.checker('submit_bid')
def submit_bid_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:

        # loads data
        old_ebtoken = loads(inputs[0])
        bid = loads(outputs[0])
        new_ebtoken = loads(outputs[1])
        
        # check argument lengths
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(parameters)!=3 or len(outputs) != 2 or len(returns) != 0:
            raise Exception("Invalid argument lengths")
        # key validations
        validate(old_ebtoken, ['type','pub','location'])
        validate(bid, ['type', 'quantity', 'pub', 'location'])
        validate(new_ebtoken, ['type','pub','location'])
        # type checks
        check_type(old_ebtoken, 'EBToken')
        check_type(new_ebtoken, 'EBToken')
        if not (bid['type'] == 'EBBuy' or bid['type'] == 'EBSell'):
            raise Exception("Invalid bid type")
        # equality checks
        equate(old_ebtoken['pub'], bid['pub'])
        equate(old_ebtoken['pub'], new_ebtoken['pub'])

        equate(old_ebtoken['location'], bid['location'])
        equate(old_ebtoken['location'], new_ebtoken['location'])        
        # signature validation
        validate_sig(parameters[2], old_ebtoken['pub'])
        
    except Exception as e:
        print e
        return False
    return True

####################################################################
# main
####################################################################
if __name__ == '__main__':
    contract.run()



####################################################################
