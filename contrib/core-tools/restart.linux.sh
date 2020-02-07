#!/bin/bash
# Set these values
exec 6< surge-experiments/setup.in
read NUM_SHARDS <&6
read NUM_REPLICAS <&6
read NUM_CLIENTS <&6
export NUM_SHARDS
export NUM_REPLICAS
export NUM_CLIENTS
cd surge-experiments
screen -dmSL surge-experiments-setup python -m SimpleHTTPServer 4999
cd ..

printf "$(date) Deployed shards: $NUM_SHARDS , replicas: $NUM_REPLICAS\n" >> surge-experiments/deploy-log.txt


for SHARD_ID in $(seq 0 $(($NUM_SHARDS-1))) # For each shard that we want to create. Every number here acts as the shard id
do
    for REPLICA_ID in $(seq 0 $(($NUM_REPLICAS-1))) # For each replica that we want to create within a shard. Every number here acts as the replica id
    do
        SCREEN_NAME="s"$SHARD_ID"n"$REPLICA_ID
        # cp -r chainspacecore chainspacecore-$SHARD_ID-$REPLICA_ID
        cd chainspacecore-$SHARD_ID-$REPLICA_ID
        # printf "shardConfigFile ChainSpaceConfig/shardConfig.txt\nthisShard $SHARD_ID\nthisReplica $REPLICA_ID" > ChainSpaceConfig/config.txt
        rm database.sqlite
        screen -dmSL $SCREEN_NAME java -cp lib/bft-smart-1.2.1-UCL.jar:target/chainspace-1.0-SNAPSHOT-jar-with-dependencies.jar uk.ac.ucl.cs.sec.chainspace.bft.TreeMapServer ChainSpaceConfig/config.txt
        cd ../
        sleep 1
    done
    cd chainspacecore 
    SCREEN_NAME="s"$SHARD_ID"-clientService"
    screen -dmSL $SCREEN_NAME ./runclientservice.sh $SHARD_ID
    cd ../
    sleep 1
done
