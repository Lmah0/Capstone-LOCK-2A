#!/bin/bash
set -x
set -v 

if [ "$#" -ne 1 ]; then # Must pass the location of the MavProxy module.
    echo "Usage: $0 <source_file>"
    exit 1
fi

MAVPROXY_MODULE="$1"

if [ ! -f "$MAVPROXY_MODULE" ]; then
    echo "Error: Location for MAVPROXY_MODULE does not exist."
    exit 1
fi

PYTHON_ENV_DIR="$HOME/LOCK2A/venv"

PYTHON_LIB_DIR=$(find "$PYTHON_ENV_DIR/lib/" -maxdepth 1 -type d -name "python3.*" | head -n 1)

if [ -z "$PYTHON_LIB_DIR" ]; then
    echo "Error: No python3.X directory found in $HOME/LOCK2A/venv/lib/"
    exit 1
fi

MAVPROXY_MODULES_DEST="$PYTHON_LIB_DIR/site-packages/MAVProxy/modules"

if [ ! -d "$MAVPROXY_MODULES_DEST" ]; then
    echo "Error: Location for MavProxy does not exist in site-packages, pip installing MavProxy."
    source $PYTHON_ENV_DIR/bin/activate
    pip3 install MAVProxy
fi


FILENAME=$(basename "$MAVPROXY_MODULE")
DIRNAME=$(dirname "$MAVPROXY_MODULE")
if [[ ! "$FILENAME" =~ ^mavproxy_ ]]; then
    NEW_FILENAME="mavproxy_$FILENAME"
    mv "$MAVPROXY_MODULE" "$DIRNAME/$NEW_FILENAME"
    MAVPROXY_MODULE="$DIRNAME/$NEW_FILENAME"
    echo "Renamed mavproxy module to $NEW_FILENAME"
fi

echo "Copying $MAVPROXY_MODULE to $MAVPROXY_MODULES_DEST"
cp "$MAVPROXY_MODULE" "$MAVPROXY_MODULES_DEST"

if [ $? -eq 0 ]; then
    echo "Success: MAVProxy module setup correctly."
else
    echo "Error: MAVProxy module setup failed."
fi
