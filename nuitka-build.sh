#!/bin/bash

# this script builds a binary from python sources

nuitka3 ./src/pnethack.py --standalone --plugin-enable=pylint-warnings 

