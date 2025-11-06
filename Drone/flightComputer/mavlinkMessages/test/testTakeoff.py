import sys
import os
import time

script_dir = os.path.abspath('./../..')
sys.path.append(script_dir)

import Drone.flightComputer.arm as arm
import Drone.flightComputer.mode as mode
import Drone.flightComputer.connect as connect
import Drone.flightComputer.takeoff as takeoff
import Drone.flightComputer.commandToLocation as commandToLocation

vehicle_connection, valid_connection = connect.connect_to_vehicle('udpin:127.0.0.1:14550')

arm.arm(vehicle_connection)
time.sleep(1)
mode.set_mode(vehicle_connection, mode.COPTER_MODES["GUIDED"])
time.sleep(1)
takeoff.takeoff(vehicle_connection, 10)
