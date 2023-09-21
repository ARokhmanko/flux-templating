#!/bin/bash

## for all json files in this directory, run create-cluster.py with the arguments passed to this script
for file in *.json; do
    /usr/bin/python3 create-cluster.py --config $file $@
done