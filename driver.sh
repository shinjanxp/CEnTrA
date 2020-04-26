#!/bin/bash
# This script connect to peers and clients emulator setup on remote hosts to run both sequentially. 
# Then it changes config on the server and restarts

SHARDS_START=${SHARDS_START:-2}
SHARDS_END=${SHARDS_END:-4}
SHARDS_STEP=${SHARDS_STEP:-2}

REPLICAS_START=${REPLICAS_START:-4}
REPLICAS_END=${REPLICAS_END:-4}
REPLICAS_STEP=${REPLICAS_STEP:-1}

CLIENTS_START=${CLIENTS_START:-50}
CLIENTS_END=${CLIENTS_END:-100}
CLIENTS_STEP=${CLIENTS_STEP:-50}

NUM_REPS=${NUM_REPS:-2}

# Varying the number of shards
for (( NUM_SHARDS=$SHARDS_START; NUM_SHARDS<=$SHARDS_END; NUM_SHARDS+=$SHARDS_STEP ))
do  
    # Varying the number of replicas
    for (( NUM_REPLICAS=$REPLICAS_START; NUM_REPLICAS<=$REPLICAS_END; NUM_REPLICAS+=$REPLICAS_STEP ))
    do  

        # Deploy once per shard-replica reconfiguration. Then restart
        ssh ${PEERS_USER}@${PEERS_HOST} "
            cd ${PEERS_CODE_PATH}
            make clean
            NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} make redeploy
        "
        # Varying the number of clients
        for (( NUM_CLIENTS=$CLIENTS_START; NUM_CLIENTS<=$CLIENTS_END; NUM_CLIENTS+=$CLIENTS_STEP ))
        do  
            # Varying the number of repititions
            for (( r=1; r<=$NUM_REPS; r++ ))
            do  
            echo "

                ***********************************************
                $r. NUM_SHARDS: $NUM_SHARDS, NUM_REPLICAS: $NUM_REPLICAS, NUM_CLIENTS: $NUM_CLIENTS"
            
                ssh ${PEERS_USER}@${PEERS_HOST} "
                        cd ${PEERS_CODE_PATH}
                        make clear-logs
                        NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} make reset
                    "
                sleep 10
                ssh ${CLIENTS_USER}@${CLIENTS_HOST} "
                        cd ${CLIENTS_CODE_PATH}
                        source .cs.env/bin/activate
                        cd chainspacecontract/chainspacecontract/measurements
                        RUN_ID=${RUN_ID} NUM_SHARDS=${NUM_SHARDS} NUM_REPLICAS=${NUM_REPLICAS} NUM_CLIENTS=${NUM_CLIENTS} PEERS_HOST=${PEERS_HOST} python ${CLIENTS_EMULATOR_SCRIPT}
                    "
            done
        done
    done
done
