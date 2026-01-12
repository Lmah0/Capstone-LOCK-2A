import sys
import os
import time

script_dir = os.path.abspath('./..')
sys.path.append(script_dir)

import arm as arm
import connect as connect

vehicle_connection = connect.connect_to_vehicle('127.0.0.1:14550')

arm.arm(vehicle_connection)
print("Vehicle should be armed now.")