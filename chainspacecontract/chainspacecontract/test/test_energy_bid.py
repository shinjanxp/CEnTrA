""" test authenticated bank transfer """

####################################################################
# imports
###################################################################
# general
from multiprocessing import Process
from json            import dumps, loads
import time
import unittest
import requests
# chainsapce
from chainspacecontract import transaction_to_solution
from chainspacecontract.examples.energy_bidding import contract as energy_bidding_contract
from chainspacecontract.examples import energy_bidding
# crypto
from chainspacecontract.examples.utils import setup, key_gen, pack


####################################################################
# authenticated bank transfer
####################################################################
class TestBankAuthenticated(unittest.TestCase):
    # --------------------------------------------------------------
    # test init
    # --------------------------------------------------------------
    def test_init(self):
        ##
        ## run service
        ##
        checker_service_process = Process(target=energy_bidding_contract.run_checker_service)
        checker_service_process.start()
        time.sleep(0.1)

        ##
        ## create transaction
        ##
        transaction = energy_bidding.init()

        ##
        ## submit transaction
        ##
        response = requests.post(
            'http://127.0.0.1:5000/' + energy_bidding_contract.contract_name + '/init', json=transaction_to_solution(transaction)
        )
        self.assertTrue(response.json()['success'])

        ##
        ## stop service
        ##
        checker_service_process.terminate()
        checker_service_process.join()


    # --------------------------------------------------------------
    # test create meter
    # --------------------------------------------------------------
    def test_create_meter(self):
        ##
        ## run service
        ##
        checker_service_process = Process(target=energy_bidding_contract.run_checker_service)
        checker_service_process.start()
        time.sleep(0.1)

        ##
        ## create transaction
        ##
        # create provider's public key
        (_, provider_pub) = key_gen(setup())

        # init
        init_transaction = energy_bidding.init()
        token = init_transaction['transaction']['outputs'][0]

        # create meter
        transaction = energy_bidding.create_meter(
            (token,),
            None,
            None,
            pack(provider_pub),
            'Some info about the meter.',   # some info about the meter
            dumps([5, 3, 5, 3, 5]),         # the tariffs 
            dumps(764)                      # the billing period
        )
        print transaction

        ##
        ## submit transaction
        ##
        response = requests.post(
            'http://127.0.0.1:5000/' + energy_bidding_contract.contract_name + '/create_meter', json=transaction_to_solution(transaction)
        )
        self.assertTrue(response.json()['success'])

        ##
        ## stop service
        ##
        checker_service_process.terminate()
        checker_service_process.join()


    # --------------------------------------------------------------
    # test add reading
    # --------------------------------------------------------------
    def test_submit_bid(self):
        ##
        ## run service
        ##
        checker_service_process = Process(target=energy_bidding_contract.run_checker_service)
        checker_service_process.start()
        time.sleep(0.1)

        ##
        ## create transaction
        ##
        # generate crypto params
        G = setup()[0]
        (provider_priv, provider_pub) = key_gen(setup())

        # init
        init_transaction = energy_bidding.init()
        token = init_transaction['transaction']['outputs'][0]

        # create meter
        create_meter_transaction = energy_bidding.create_meter(
            (token,),
            None,
            None,
            pack(provider_pub),
            'Some info about the meter.',
            dumps([5, 3, 5, 3, 5]),  # the tariffs
            dumps(764)               # billing period         
        )
        token = create_meter_transaction['transaction']['outputs'][0]
        meter = create_meter_transaction['transaction']['outputs'][1]

        # Submit bid
        transaction = energy_bidding.submit_bid(
            (token,),
            (meter,),
            (dumps({'type':'EBBuy','energy':10,'price':50}),),
            pack(provider_priv)
        )
        token = bid_transaction['transaction']['outputs'][0]
        bid = bid_transaction['transaction']['outputs'][1]
        print transaction


        ##
        ## submit transaction
        ##
        response = requests.post(
            'http://127.0.0.1:5000/' + energy_bidding_contract.contract_name + '/submit_bid', json=transaction_to_solution(transaction)
        )
        self.assertTrue(response.json()['success'])

        ##
        ## stop service
        ##
        checker_service_process.terminate()
        checker_service_process.join()




####################################################################
# main
###################################################################
if __name__ == '__main__':
    unittest.main()
