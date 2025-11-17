#!/bin/bash

cd ~/.local/lib/python3.11/bin/MAVProxy # Navigate to MAVPRoxy directory
python mavproxy.py --out=udp:127.0.0.1:5006 & # Run MAVProxy in background and open up a port to talk to MAVLink

module load lock # Load the mavproxy module for geolocation extraction (might need to manually enter this)

cd ~/LOCK2A/Capstone-LOCK-2A/Drone/flightComputer
python server.py