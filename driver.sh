#!/bin/bash
# This script connect to peers setup on server and client emulator setup on night-king to run both sequentially. Then it changes config in server and restarts

MAX_SHARDS=2
# MAX_REPLICAS=4
MAX_CLIENTS=200

NUM_NODES=32
# NUM_SHARDS=1
NUM_REPS=1

# Setup an http server to host the setup file. This is required since the python contracts cannot access environment variables
cd stats
screen -dmSL stats python -m SimpleHTTPServer 4999
cd ..

for REPS in $(seq 1 $NUM_REPS) 
do
    NUM_SHARDS=1
    # NUM_REPLICAS=4
    while [ $NUM_SHARDS -le $MAX_SHARDS ]
    do
        NUM_CLIENTS=200
        NUM_REPLICAS=4
        # NUM_REPLICAS=$(($NUM_NODES/$NUM_SHARDS))
        # Deploy once per shard reconfiguration. Then restart
        ssh shinjan@localhost "
                cd ~/Workspaces/MTP/surge/
                NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} make redeploy
            "
        
        while [ $NUM_CLIENTS -le $MAX_CLIENTS ]
        do
            echo "NUM_SHARDS: $NUM_SHARDS, NUM_REPLICAS: $NUM_REPLICAS, NUM_CLIENTS: $NUM_CLIENTS"
            printf "${NUM_SHARDS}\n${NUM_REPLICAS}\n${NUM_CLIENTS}" >> stats/setup.in
            ssh shinjan@localhost "
                    cd ~/Workspaces/MTP/surge/
                    NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} make reset
                "
            sleep 10
            ssh shinjan@localhost "
                    cd ~/Workspaces/MTP/surge/
                    source .cs.env/bin/activate
                    cd chainspacecontract/chainspacecontract/test
                    python test_surge_bids.py
                "
            NUM_CLIENTS=$(( $NUM_CLIENTS+50 ))
        done
        NUM_SHARDS=$(($NUM_SHARDS+1))
    done
done
