#!/bin/sh
set -ex

trap stop SIGTERM SIGKILL

start(){
    sleep 1

    echo "Setting proper ownership to ipfs folders"
    chown -fv ipfs /data/ /data/ipfs/ /data/ipfs/datastore/ /data/ipfs/blocks/

    sleep 1

    echo "Enforce permissions"
    chmod -v 755 /data /data/ipfs/ /data/ipfs/datastore/ /data/ipfs/blocks/

    sleep 1

    echo "Deleting possible old lock files"
    rm -rfv /data/ipfs/repo.lock /data/ipfs/datastore/LOCK /data/ipfs/blocks/.temp /data/ipfs/datastore/LOG

    sleep 1

    echo "Starting IPFS daemon"
    gosu ipfs /usr/local/bin/start_ipfs daemon --migrate=true --agent-version-suffix=docker
}

stop(){
   echo "Signal Trapped $? - Shutting down IPFS. 15=SIGTERM, 9=SIGKILL"
   gosu ipfs /usr/local/bin/ipfs shutdown

   exit
}

start

