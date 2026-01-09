import sys
import os
import time

script_dir = os.path.abspath('./..')
sys.path.append(script_dir)

import mode as mode
import connect as connect

vehicle_connection = connect.connect_to_vehicle('127.0.0.1:14550')

print("Setting mode to GUIDED...")
mode.set_mode(vehicle_connection, mode.COPTER_MODES["GUIDED"])

time.sleep(0.5)

print("Setting mode to STABILIZE...")
mode.set_mode(vehicle_connection, mode.COPTER_MODES["STABILIZE"])

time.sleep(0.5)

print("Setting mode to LOITER...")
mode.set_mode(vehicle_connection, mode.COPTER_MODES["LOITER"])

time.sleep(0.5)

print("Setting mode to RTL...")
mode.set_mode(vehicle_connection, mode.COPTER_MODES["RTL"])

time.sleep(0.5)

print("Setting mode to ACRO...")
mode.set_mode(vehicle_connection, mode.COPTER_MODES["ACRO"])

print("Setting mode to CIRCLE...")
mode.set_mode(vehicle_connection, mode.COPTER_MODES["CIRCLE"])

print("Mode setting test completed.")
