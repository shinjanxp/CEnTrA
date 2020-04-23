# Introduction
We could do with a better tooling setup for running experiments, so we created a few scripts to get started.

# Howto
* Create a `.env` file by copying the `.env.example` and set the experimental parameters. `PEERS_HOST` and `PEERS_USER` refers to the remote host where peers will be deployed. THe same goes for `CLIENTS_HOST` and `CLIENTS_USER`.
```
cp .env.example .env
```
* Before going forward make sure that you can ssh into the PEERS_HOST and CLIENTS_HOST without needing to enter a password. This can be achieved by using `ssh-copy-id`. 
```
. ./.env
ssh-copy-id ${PEERS_USER}@${PEERS_HOST}
# Enter your password when prompted. That's it!
```
* Build the project using
```
make build-jar
```
* The experimental runtime script is written in `driver.sh`. We've set up the `Makefile` to load the environment variables and run the driver properly. So just wing it with
```
make run-experiments
```
* All statistics will be generated inside the `stats` directory.