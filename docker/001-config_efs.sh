#!/bin/sh
set -ex

# We clean the lock files and temp files that could prevent correct startup
rm -rfv /data/ipfs/repo.lock /data/ipfs/datastore/LOCK /data/ipfs/blocks/.temp /data/ipfs/datastore/LOG
