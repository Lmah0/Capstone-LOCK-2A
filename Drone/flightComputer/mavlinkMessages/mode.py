from pymavlink import mavutil

# --------------------------------------------------------------------------------------
# MAVLink Copter Modes
# --------------------------------------------------------------------------------------
COPTER_MODES = {
    "Stabilize": 0,
    "Acro": 1,
    "Alt Hold": 2,
    "Auto": 3,
    "Guided": 4,
    "Loiter": 5,
    "RTL": 6,
    "Land": 9,
}

# --------------------------------------------------------------------------------------
# Mode Setter
# --------------------------------------------------------------------------------------
def set_mode(vehicle_connection, mode_string):
    """
    Set the flight mode of a connected MAVLink vehicle.

    Parameters
    ----------
    vehicle_connection : mavutil.mavlink_connection
        Active MAVLink connection to the vehicle.
    mode_id : int
        Numerical mode ID (see COPTER_MODES).

    Behavior
    --------
    Sends a MAV_CMD_DO_SET_MODE command via MAVLink to the connected vehicle.
    Waits for a COMMAND_ACK response and prints it to confirm success.

    Raises
    ------
    Exception
        If MAVLink communication fails or times out.
    """
    try:
        mode_id = COPTER_MODES.get(mode_string)
        
        vehicle_connection.mav.command_long_send(
            target_system=vehicle_connection.target_system,
            target_component=vehicle_connection.target_component,
            command=mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            confirmation=0,
            param1=mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            param2=mode_id,
            param3=0,
            param4=0,
            param5=0,
            param6=0,
            param7=0,
        )

        msg = vehicle_connection.recv_match(
            type="COMMAND_ACK", blocking=True, timeout=5
        )
        print(msg)

    except Exception as e:
        print(f"[ERROR] Failed to set mode: {e}")
