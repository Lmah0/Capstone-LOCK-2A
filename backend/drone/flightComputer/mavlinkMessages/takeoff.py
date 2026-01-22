from pymavlink import mavutil

def takeoff(vehicle_connection, takeoff_height):
    """
    Initiates a takeoff command for the connected vehicle.

    Args:
        vehicle_connection: The MAVLink connection object to the vehicle.
        takeoff_height (float): Desired takeoff altitude in meters.

    Raises:
        Exception: If any error occurs during the command transmission or acknowledgment.
    """
    try:
        # Send the takeoff command using MAVLink COMMAND_LONG
        vehicle_connection.mav.command_long_send(
            vehicle_connection.target_system,      # Target system ID
            vehicle_connection.target_component,   # Target component ID
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,  # Takeoff command ID
            0,                                    # Confirmation (0 = first transmission)
            0,                                    # Pitch angle (for copter, set to 0)
            0, 0, 0,                              # Unused parameters
            0,                                    # Latitude (0 = current position)
            0,                                    # Longitude (0 = current position)
            takeoff_height                        # Altitude in meters
        )

        # Wait for acknowledgment from the vehicle
        ack_msg = vehicle_connection.recv_match(
            type='COMMAND_ACK', blocking=True, timeout=5
        )

        print(f"Takeoff command ACK: {ack_msg}")

    except Exception as e:
        print(f"[ERROR] takeoff() in Copter/Operations/takeoff.py failed: {e}")
