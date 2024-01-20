#!/bin/sh
set -ex

# This script is an attempt to cleanup the temporary files when the daemon restarts
# Sometimes the deamon would not shutdown correctly leaving the temp files and preventing a restart
# However, those temp files would sometimes be owned by root, rendering this script useless as it's run by the 'ipfs' user

# We also rely on the entrypoint.sh which runs as root to cleanup those files

rm -rfv /data/ipfs/repo.lock /data/ipfs/datastore/LOCK /data/ipfs/blocks/.temp /data/ipfs/datastore/LOG
