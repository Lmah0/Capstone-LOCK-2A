from pymavlink import mavutil

def move_to_location(connection, latitude, longitude, altitude):
    # Will use RTH (relative to home) altitude for now
    try:
        connection.mav.send(mavutil.mavlink.MAVLink_set_position_target_global_int_message(
            10,
            connection.target_system,
            connection.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            int(0b110111111000),
            int(latitude * 10 ** 7), 
            int(longitude * 10 ** 7), 
            altitude, # Altitude (in metres) above home [DOES NEED TO BE POSITIVE]
            0, 0, 0, 0, 0, 0, 0, 0))
    except Exception as e:
        print(f"Error commanding drone to location. Error: {e}")
    
def monitor_progress_to_waypoint(connection):
    try:
        while True:
            msg = connection.recv_match(type='NAV_CONTROLLER_OUTPUT', blocking=True, timeout=5)
            print(msg)

            if msg and msg.wp_dist < 1: # If within 1 metre of waypoint
                print("Reached waypoint")
                break
    except Exception as e:
        print(f"Error monitoring progress to waypoint. Error: {e}")
