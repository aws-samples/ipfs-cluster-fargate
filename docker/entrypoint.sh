#!/bin/sh

trap stop SIGTERM SIGINT SIGQUIT SIGHUP ERR

start(){
    echo "Fixing ownership and deleting lock files"
    chown -fR ipfs /data/ipfs/ || true
    rm -rf /data/ipfs/repo.lock /data/ipfs/datastore/LOCK /data/ipfs/blocks/.temp

    echo "Starting IPFS daemon"
    tini -- gosu ipfs /usr/local/bin/start_ipfs daemon --migrate=true --agent-version-suffix=docker
}

stop(){
   echo "Shutting down IPFS"
   tini -- gosu ipfs /usr/local/bin/ipfs shutdown

   exit
}

start

