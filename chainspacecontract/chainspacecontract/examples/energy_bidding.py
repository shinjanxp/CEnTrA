"""A smart contract that extends smart meter to perform energy bids."""

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
contract = ChainspaceContract('energy_bidding')


####################################################################
# methods
####################################################################
# ------------------------------------------------------------------
# init
# ------------------------------------------------------------------
@contract.method('init')
def init():

    # return
    return {
        'outputs': (dumps({'type' : 'EBToken'}),),
    }

# ------------------------------------------------------------------
# create meter
# NOTE:
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand
# ------------------------------------------------------------------
@contract.method('create_meter')
def create_meter(inputs, reference_inputs, parameters, pub, info, tariffs, billing_period):

    # new meter
    new_meter = {
        'type'           : 'SMMeter', 
        'pub'            : pub, 
        'info'           : info,
        'readings'       : [],
        'billing_period' : loads(billing_period),
        'tariffs'        : loads(tariffs)
    }

    # return
    return {
        'outputs': (inputs[0], dumps(new_meter))
    }

# ------------------------------------------------------------------
# add_reading
# NOTE:
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand
# ------------------------------------------------------------------
@contract.method('add_reading')
def add_reading(inputs, reference_inputs, parameters, meter_priv, reading, opening):

    # compute output
    old_meter = loads(inputs[0])
    new_meter = loads(inputs[0])

    # create commitement to the reading
    (G, g, (h0, _, _, _), _) = setup()
    commitment = loads(reading) * g + unpack(opening) * h0

    # update readings
    new_meter['readings'].append(pack(commitment))

    # hash message to sign
    hasher = sha256()
    hasher.update(dumps(old_meter).encode('utf8'))
    hasher.update(dumps(pack(commitment)).encode('utf8'))

    # sign message
    sig = do_ecdsa_sign(G, unpack(meter_priv), hasher.digest())

    # return
    return {
        'outputs': (dumps(new_meter),),
        'extra_parameters' : (
            pack(commitment),
            pack(sig)
        )
    }


# ------------------------------------------------------------------
# submit_bid
# NOTE:
#   - only 'inputs', 'reference_inputs' and 'parameters' are used to the framework
#   - if there are more than 3 param, the checker has to be implemented by hand
#   - reference_inputs must contain a valid smart_meter object
#   - inputs must contain an EBToken
#   - paramters must contain a bid object containing 3 properties: type, energy and price. 
#   - Type can be EBBuy or EBSell. Energy is in kWh, price is maximum buying price or minimum selling price
# ------------------------------------------------------------------
@contract.method('submit_bid')
def submit_bid(inputs, reference_inputs, parameters, meter_priv):

    # Extract bid object from paramters
    bid = loads(parameters[0])
    smart_meter = loads(reference_inputs[0])
    token = loads(inputs[0])
    bid['pub'] = smart_meter['pub']
    # Create a hash digest of inputs and parameters
    hasher = sha256()
    hasher.update(dumps(token).encode('utf8'))
    hasher.update(dumps(smart_meter).encode('utf8'))
    hasher.update(dumps(bid).encode('utf8'))

    # sign message
    G = setup()[0]
    sig = do_ecdsa_sign(G, unpack(meter_priv), hasher.digest())
    # return
    return {
        'outputs': (inputs[0],dumps(bid)),
        'extra_parameters' : (
            pack(sig),
        )
    }

####################################################################
# checker
####################################################################
# ------------------------------------------------------------------
# check meter's creation
# ------------------------------------------------------------------
@contract.checker('create_meter')
def create_meter_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:

        # loads data
        meter = loads(outputs[1])

        # check format
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(outputs) != 2 or len(returns) != 0:
            return False
        if meter['pub'] == None or meter['info'] == None or meter['billing_period'] == None:
            return False
        if meter['readings'] == None or meter['tariffs'] == None:
            return False

        # check tokens
        if loads(inputs[0])['type'] != 'EBToken' or loads(outputs[0])['type'] != 'EBToken':
            return False
        if meter['type'] != 'SMMeter':
            return False

        # otherwise
        return True

    except (KeyError, Exception):
        return False

# ------------------------------------------------------------------
# check add reading
# ------------------------------------------------------------------
@contract.checker('add_reading')
def add_reading_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:

        # get objects
        old_meter = loads(inputs[0])
        new_meter = loads(outputs[0])

        # check format
        if len(inputs) != 1 or len(reference_inputs) != 0 or len(outputs) != 1 or len(returns) != 0:
            return False
        if old_meter['pub'] != new_meter['pub'] or old_meter['info'] != new_meter['info']:
            return False
        if old_meter['tariffs'] != new_meter['tariffs'] or old_meter['billing_period'] != new_meter['billing_period']:
            return False

        # check tokens
        if old_meter['type'] != new_meter['type']:
            return False

        # check readings' consistency
        if new_meter['readings'] != old_meter['readings'] + [parameters[0]]:
            return False

        # hash message to sign
        hasher = sha256()
        hasher.update(dumps(old_meter).encode('utf8'))
        hasher.update(dumps(parameters[0]).encode('utf8'))

        # verify signature
        G = setup()[0]
        pub = unpack(old_meter['pub'])
        sig = unpack(parameters[1])
        if not do_ecdsa_verify(G, pub, sig, hasher.digest()):
            return False

        # otherwise
        return True

    except (KeyError, Exception):
        return False

# ------------------------------------------------------------------
# check bid submission
# ------------------------------------------------------------------
@contract.checker('submit_bid')
def submit_bid_checker(inputs, reference_inputs, parameters, outputs, returns, dependencies):
    try:
        input_token = loads(inputs[0])
        output_token = loads(outputs[0])
        output_bid = loads(outputs[1])
        smart_meter = loads(reference_inputs[0])
        # check format
        if len(inputs) != 1 or len(reference_inputs) != 1 or len(outputs) != 2 or len(parameters) != 2 or len(returns) != 0:
            return False

        # check tokens
        if input_token['type'] != 'EBToken' or output_token['type'] != 'EBToken':
            return False
        if output_bid['type'] != 'EBBuy' and output_bid['type'] != 'EBSell':
            return False
        if smart_meter['type'] != 'SMMeter':
            return False
        if output_bid['pub'] != smart_meter['pub']:
            return False
        # hash message to verify signature
        hasher = sha256()
        hasher.update(dumps(input_token).encode('utf8'))
        hasher.update(dumps(smart_meter).encode('utf8'))
        hasher.update(dumps(output_bid).encode('utf8'))

        # recompose signed digest
        pub = unpack(smart_meter['pub'])
        sig = unpack(parameters[1])

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
