#!/bin/sh
set -ex

# We make sure those files are cleanedup at container startup
# If the container is killed, those files may remain
# They would block ipfs process startup
rm -rf /data/ipfs/repo.lock /data/ipfs/datastore/LOCK /data/ipfs/blocks/.temp
