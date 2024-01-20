#!/bin/sh
set -ex

start(){
    echo "Starting IPFS daemon"
    /usr/local/bin/start_ipfs daemon --migrate=true --agent-version-suffix=docker
}

start
