#!/bin/bash
# This script connect to peers and clients emulator setup on remote hosts to run both sequentially. 
# Then it changes config on the server and restarts

MAX_SHARDS=${MAX_SHARDS:-2}
MAX_REPLICAS=${MAX_REPLICAS:-4}
MAX_CLIENTS=${MAX_CLIENTS:-200}
NUM_REPS=${NUM_REPS:-1}

NUM_NODES=32

# Setup an http server on clients server to host the setup file. 
# This is required since the python contracts cannot access environment variables
ssh ${CLIENTS_USER}@${CLIENTS_HOST} "
    cd ${CLIENTS_SURGE_PATH}/stats
    screen -dmSL stats python -m SimpleHTTPServer 4999
"

for REPS in $(seq 1 $NUM_REPS) 
do
    NUM_SHARDS=1
    # NUM_REPLICAS=4
    while [ $NUM_SHARDS -le $MAX_SHARDS ]
    do
        NUM_CLIENTS=50
        NUM_REPLICAS=4
        # NUM_REPLICAS=$(($NUM_NODES/$NUM_SHARDS))
        # Deploy once per shard reconfiguration. Then restart
        ssh ${PEERS_USER}@${PEERS_HOST} "
                cd ${PEERS_SURGE_PATH}
                NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} make redeploy
            "
        
        while [ $NUM_CLIENTS -le $MAX_CLIENTS ]
        do
            echo "

            ***********************************************
            NUM_SHARDS: $NUM_SHARDS, NUM_REPLICAS: $NUM_REPLICAS, NUM_CLIENTS: $NUM_CLIENTS"
            # Set these values in setup.in so that it can be uploaded to CLIENTS_HOST
            cd stats
            printf "$NUM_SHARDS\n$NUM_REPLICAS\n$NUM_CLIENTS\n" > setup.in
            scp setup.in ${CLIENTS_USER}@${CLIENTS_HOST}:${CLIENTS_SURGE_PATH}/setup.in
            cd ..
            ssh ${PEERS_USER}@${PEERS_HOST} "
                    cd ${PEERS_SURGE_PATH}
                    NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} make reset
                "
            sleep 10
            ssh ${CLIENTS_USER}@${CLIENTS_HOST} "
                    cd ${CLIENTS_SURGE_PATH}
                    source .cs.env/bin/activate
                    cd chainspacecontract/chainspacecontract/test
                    NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} PEERS_HOST=${PEERS_HOST} python test_surge_bids.py
                "
            NUM_CLIENTS=$(( $NUM_CLIENTS+50 ))
        done
        NUM_SHARDS=$(($NUM_SHARDS+1))
    done
done
