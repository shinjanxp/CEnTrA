*Please note: this is prototype code which serves as a validation of the ideas expressed in the paper 'CEnTrA:City-scale Energy Transaction Application for the Smart Grid' submitted to [Powercon 2020](https://www.powercon2020.org/)*


# CEnTrA

CEnTrA is an application of using sharding in distributed ledger technology to develop a novel hierarchical model capable of processing P2P energy sharing transactions at city-scale. This prototype code is based on a fork of [Chainspace](https://github.com/chainspace/chainspace-prototype). Chainspace is a distributed ledger platform for high-integrity and transparent processing of transactions within a decentralized system.

## Developer Installation

The bulk of the code is to be found in `chainspacecore`. To run a network of chainspace nodes, you need to first compile and package this module. Please refer [getting-started](getting-started.md) for instructions on how to install and compile this project.


### Run

The core of the application is written in Java and the smart contracts are written in Python. There are 2 parts to the chainspace network: the peers and the client service. The peers are a set of nodes that are communicating with each other based on the BFT SMaRt library. The client service is an http server which connects to the peers and allows you to submit transactions.

The Python smart contracts connect to the client service at a known port and submit transactions.

There are multiple ways to run the application.

#### Fully automated
We have created a script to run the application with various shard-replica configurations. Refer [running-experiments](running-experiments.md) for details.

#### Separate network and clients
* Start the network by running
```
NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} make start-nodes
```
Replace the environment variables above to your desired values.
* Activate the virtual environment
```
source .cs.env/bin/activate
```
* Run any of the test contracts in `chainspacecontract/chainspacecontract/measurements`
```
cd chainspacecontract/chainspacecontract/measurements
RUN_ID=${RUN_ID} NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} PEERS_HOST=${PEERS_HOST} python ${CLIENTS_EMULATOR_SCRIPT}
```

## Developer Setup [Visual Studio Code]

Visual Studio Code has support for running Python files (.py) as Jupyter notebooks. Install the ipykernel package inside the virtual environment.
```
source .cs.env/bin/activate
pip install ipykernel
```
Open any of the contract measurement files in `chainspacecontract/chainspacecontract/measurements`
Click `Run Cell` to launch a Jupyter kernel and execute the contract. Make sure to launch the network beforehand by running
```
make start-nodes
```
