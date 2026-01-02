from pymavlink import mavutil

# --------------------------------------------------------------------------------------
# MAVLink Copter Modes
# --------------------------------------------------------------------------------------
COPTER_MODES = {
    "STABILIZE": 0,
    "ACRO": 1,
    "ALTHOLD": 2,
    "AUTO": 3,
    "GUIDED": 4,
    "LOITER": 5,
    "RTL": 6,
    "CIRCLE": 7,
    "LAND": 9,
    "DRIFT": 11,
    "SPORT": 13,
    "FLIP": 14,
    "AUTOTUNE": 15,
    "POSHOLD": 16,
    "BRAKE": 17,
    "THROW": 18,
    "AVOID_ADSB": 19,
    "GUIDED_NOGPS": 20,
    "SMART_RTL": 21,
    "FLOWHOLD": 22,
    "FOLLOW": 23,
    "ZIGZAG": 24,
    "SYSTEMID": 25,
    "HELI_AUTOROTATE": 26,
    "AUTO_RTL": 27,
}

# --------------------------------------------------------------------------------------
# Mode Setter
# --------------------------------------------------------------------------------------
def set_mode(vehicle_connection, mode):
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
        mode_id = COPTER_MODES['mode']
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
