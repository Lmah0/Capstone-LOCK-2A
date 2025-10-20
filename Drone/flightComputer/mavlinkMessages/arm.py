from pymavlink import mavutil

def arm(connection):
    try:
        # Ensure the vehicle is ready to arm
        connection.mav.command_long_send(
            connection.target_system,
            connection.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, # Confirmation
            1, 0, 0, 0, 0, 0, 0 # Mavlink parameters
        )
        msg = connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        print(msg)
    except Exception as e:
        print(f"Error: Unable to send arm command. See error info: {e}")

def disarm(connection):
    try:
        # Ensure the vehicle is ready to disarm
        connection.mav.command_long_send(
            connection.target_system,
            connection.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, # Confirmation
            0, 0, 0, 0, 0, 0, 0 # Mavlink parameters
        )
        msg = connection.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        print(msg)
    except Exception as e:
        print(f"Error: Unable to send disarm command. See error info: {e}")
