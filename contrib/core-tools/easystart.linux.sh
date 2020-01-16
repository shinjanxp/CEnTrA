#!/bin/bash
rm -rf chainspacecore-*

for SHARD_ID in 0 1 2 # For each shard that we want to create. Every number here acts as the shard id
do
    for REPLICA_ID in 0 1 2 3 # For each replica that we want to create within a shard. Every number here acts as the replica id
    do
        SCREEN_NAME="s"$SHARD_ID"n"$REPLICA_ID
        cp -r chainspacecore chainspacecore-$SHARD_ID-$REPLICA_ID
        cd chainspacecore-$SHARD_ID-$REPLICA_ID
        printf "shardConfigFile ChainSpaceConfig/shardConfig.txt\nthisShard $SHARD_ID\nthisReplica $REPLICA_ID" > ChainSpaceConfig/config.txt
        screen -dmSL $SCREEN_NAME java -cp lib/bft-smart-1.2.1-UCL.jar:target/chainspace-1.0-SNAPSHOT-jar-with-dependencies.jar uk.ac.ucl.cs.sec.chainspace.bft.TreeMapServer ChainSpaceConfig/config.txt
        cd ../
        sleep 1
    done
done
