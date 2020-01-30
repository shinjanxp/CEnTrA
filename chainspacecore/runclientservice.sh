#!/bin/bash
SHARD_ID=$1
printf "shardConfigFile ChainSpaceConfig/shardConfig.txt\nthisClient $SHARD_ID\nport 500$SHARD_ID" > ChainSpaceClientConfig/config.txt


BFT_SMART_LIB=lib/bft-smart-1.2.1-UCL.jar
CLIENT_API_DB=../chainspacecore-$SHARD_ID-0/database

rm config/currentView
java -Dclient.api.database=${CLIENT_API_DB} -cp ${BFT_SMART_LIB}:target/chainspace-1.0-SNAPSHOT-jar-with-dependencies.jar uk.ac.ucl.cs.sec.chainspace.Client ChainSpaceClientConfig/config.txt
