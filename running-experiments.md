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
* To drastically improve execution speed and prevent errors arising due to disk write latency (when running multiple peers on the same host, each peer will try to update its database.sqlite concurrently, leading to disk contention and slowdown), we make use of a tmpfs file system. T his allows us to access memory via a file system, so that all file access never actually reaches the disk but is kept completely in memory. This gives us write speeds of upto 1.5 Gbps. To enable tmpfs we need to mount a tmpfs file system. Luckily we have a make script that can do the job. 
```
make mount-tmpfs
# Provide sudo password when asked for
```
You may choose to unmount the file system afterwards. We have a make script for that as well
```
make unmount-tmpfs
# Yeah, just give the sudo password again
```
* The experimental runtime script is written in `driver.sh`. We've set up the `Makefile` to load the environment variables and run the driver properly. So just wing it with
```
make run-experiments
```
* All statistics will be generated inside the `stats` directory.