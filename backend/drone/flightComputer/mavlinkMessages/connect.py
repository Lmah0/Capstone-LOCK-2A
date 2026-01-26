from pymavlink import mavutil

def verify_connection(connection):
    try:
        connection.wait_heartbeat()
        print("Heartbeat from system (system %u component %u)" % (connection.target_system, connection.target_component))
        return True

    except Exception as e:
        print(f"Error: Unable to connect to the vehicle. See error info: {e}")
    
    return False

def connect_to_vehicle(ip_and_port='udp:127.0.0.1:14550'):
    try:
        print(f"attempting to connect with ip/port: {ip_and_port}")
        connection = mavutil.mavlink_connection(ip_and_port)
        print("got connection")
        if verify_connection(connection):
            return connection
        else:
            print("Not a valid connection. Exiting.")
            exit(1)
    except Exception as e:
        print(f"Error: Unable to connect to the vehicle at {ip_and_port}. See error info: {e}")
    
    return None