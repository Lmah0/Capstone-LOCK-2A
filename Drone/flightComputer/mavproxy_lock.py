import socket
import time

from MAVProxy.modules.lib import mp_module

class lock(mp_module.MPModule):
    def __init__(self, mpstate):
        """Initialise module"""
        super(lock, self).__init__(mpstate, "lock", "Capstone location information extraction")
        self.emit_interval = 0.1
        self.last_emitted = time.time()
        self.sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

        self.lat = 0
        self.lon = 0
        self.rel_alt = 0
        self.alt = 0

        self.roll = 0
        self.pitch = 0
        self.yaw = 0

        self.dlat = 0
        self.dlon = 0
        self.dalt = 0
        self.heading = 0

        self.flight_mode = 0

    def idle_task(self):
        '''called rapidly by mavproxy'''
        now = time.time()
        if now-self.last_emitted > self.emit_interval:
            self.last_emitted = now

            if self.lat != 0:
                self.send_data()

    def mavlink_packet(self, m):
        '''handle mavlink packets'''
        if self.settings.target_system == 0 or self.settings.target_system == m.get_srcSystem():
            if m.get_type() == 'GLOBAL_POSITION_INT':
                (lat, lon, alt, relative_alt, dlat, dlon, dalt, heading) = (m.lat*1.0e-7, m.lon*1.0e-7, m.alt/1000,
                                                                                    m.relative_alt/1000, m.vx/100, m.vy/100, m.vz/100, m.hdg/100)
                self.lat = lat # Latitude
                self.lon = lon # Longitude
                self.alt = alt # Altitude (MSL)
                self.rel_alt = relative_alt # Altitude above home
                self.dlat = dlat # Ground X speed (Latitude, positive north)
                self.dlon = dlon # Ground y Speed (Longitude, positive east)
                self.dalt = dalt # Ground Z speed (Altitude, postive down)
                self.heading = heading # Vehicle heading, yaw angle
            
            elif m.get_type() == 'ATTITUDE':
                (roll, pitch, yaw) = (m.roll, m.pitch, m.yaw)
                self.roll = roll # Roll in rads (-pi, pi)
                self.pitch = pitch # Pitch in rads (-pi, pi)
                self.yaw = yaw # Yaw in rads (-pi, pi)
            
            elif m.get_type() == 'HEARTBEAT':
                self.flight_mode = m.custom_mode
            
    def send_data(self):
        t = time.time()
        heartbeat_data = (t, self.lat, self.lon, self.rel_alt, self.alt, self.roll, self.pitch, self.yaw, 
                          self.dlat, self.dlon, self.dalt, self.heading, self.flight_mode)

        heartbeat_message = f"{heartbeat_data}".encode()
        self.sock.sendto(heartbeat_message, ("127.0.0.1", 5005))

    def encode_message(self, items):
        message = ""
        for index, item in enumerate(items):
            message += str(item)
            if index != len(items) - 1:
                message += ","
        return message.encode()

def init(mpstate):
    '''initialise module'''
    return lock(mpstate)
