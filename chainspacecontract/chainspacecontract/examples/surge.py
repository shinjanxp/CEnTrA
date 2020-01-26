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

def pb():
    print "**********************  BEGIN  ******************************"
def pe():
    print "***********************  END  *******************************"

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
        'outputs': (dumps({'id':1,'type' : 'InitToken'}),dumps({'id':2,'type' : 'InitToken'}),dumps({'id':3,'type' : 'InitToken'})),
    }

# ------------------------------------------------------------------
# create surge client
# NOTE:
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand
# ------------------------------------------------------------------
@contract.method('create_surge_client')
def create_surge_client(inputs, reference_inputs, parameters, info):

    pub = parameters[0]
    # new client
    new_surge_client = {
        'type'           : 'SurgeClient', 
        'pub'            : pub, 
        'info'           : info
    }
    vote_slip = {
        'type':'VoteSlipToken',
        'pub':pub
    }
    # return
    return {
        'outputs': ( dumps(new_surge_client), dumps(vote_slip))
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
        # check format
        if len(reference_inputs) != 0 or len(parameters)!=1 or len(outputs) != 2 or len(returns) != 0:
            return False
        if surge_client['pub'] == None or surge_client['info'] == None :
            return False
        # check tokens
        if not(loads(inputs[0])['type'] == 'InitToken' or loads(inputs[0])['type'] == 'CSCVoteToken') or loads(outputs[1])['type'] != 'VoteSlipToken':
            return False
        if surge_client['type'] != 'SurgeClient':
            return False
        
        if loads(inputs[0])['type'] == 'InitToken':
            return True
        # todo: check identity via priv_key
        # validate CSC votes if InitToken is not provided
        voters = {}
        for vote in inputs:
            vote = loads(vote)
            if vote['type']!= 'CSCVoteToken':
                return False
            if vote['granted_to'] != parameters[0]:
                return False
            voters[str(vote['granted_by'])]= True
        
        if len(voters) < REQUIRED_VOTES:
            return False

        # otherwise
        return True

    except (KeyError, Exception):
        return False


# ------------------------------------------------------------------
# cast csc vote
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
    hasher = sha256()
    hasher.update("proof")

    # sign message
    G = setup()[0]
    sig = do_ecdsa_sign(G, unpack(surge_client_priv), hasher.digest())

    vote_token = {
        'type'          : 'CSCVoteToken', 
        'granted_by'    : granted_by_pub,
        'granted_to'    : granted_to_pub
    }
    # vote_slip = {
    #     'type':'VoteSlipToken',
    #     'pub':granted_by_pub
    # }
    # return
    return {
        'outputs': ( dumps(vote_token), inputs[0]),
        'extra_parameters': (
            pack(sig),
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
        
        # check format
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(outputs) != 2 or len(returns) != 0:
            return False
        # check tokens
        if loads(inputs[0])['type'] != 'VoteSlipToken' or loads(outputs[1])['type'] != 'VoteSlipToken' or loads(outputs[0])['type'] != 'CSCVoteToken':
            return False
        
        # check that the signature on the proof is correct
        hasher = sha256()
        hasher.update("proof")

        # recompose signed digest
        pub = unpack(vote_slip['pub'])
        sig = unpack(parameters[0])

        # verify signature
        (G, _, _, _) = setup()
        if not do_ecdsa_verify(G, pub, sig, hasher.digest()):
            return False


        # otherwise
        return True

    except (KeyError, Exception):
        return False

####################################################################
# main
####################################################################
if __name__ == '__main__':
    contract.run()



####################################################################
