import math
from geographiclib.geodesic import Geodesic

# Parameters:
# uav_longitude - longitude of the center of the image in degrees
# uav_latitude - latitude of the center of the image in degrees
# uav_altitude - altitude of the uav in meters
# bearing - azimuth angle measured from North clockwise
# cam_fov - field of view of the camera in degrees
# img_width_px - width of the image in pixels
# img_height_px - height of the image in pixels
# obj_x_px - x coordinate of the target object in pixels where (0,0) is the center of the image
# obj_y_px - y coordinate of the target object in pixels
# Returns:
# (obj_longitude, obj_latitude) - the estimated longitude and latitude of the object

CAM_FOV = 73.7 
IMG_WIDTH_PX = 1456
IMG_HEIGHT_PX = 1088

def locate(uav_latitude: float, uav_longitude: float, uav_altitude:float, bearing:float, obj_x_px:float, obj_y_px:float):
    cam_fov_rad = math.radians(CAM_FOV)
    diagonal_dist = math.tan(cam_fov_rad/2) * uav_altitude * 2
    img_width = math.sqrt(diagonal_dist**2 / (1 + IMG_HEIGHT_PX / IMG_WIDTH_PX)) # w^2 + (h/w)*w^2 = diag^2
    img_height = IMG_HEIGHT_PX / IMG_WIDTH_PX * img_width
    length_per_px = img_width / IMG_WIDTH_PX
    obj_x = obj_x_px * length_per_px
    obj_y = obj_y_px * length_per_px
    dist = math.sqrt(obj_x**2 + obj_y**2)
    # print("LOCATE\n ", cam_fov_rad, diagonal_dist, img_width, img_height, length_per_px, obj_x, obj_y, dist)
    angle = math.atan2(obj_y_px, obj_x_px) # Polar angle of the object point P
    true_bearing = (bearing + 90 - math.degrees(angle)) % 360
    geod = Geodesic.WGS84
    azil = true_bearing # Angle from North CW of the object point P
    g = geod.Direct(uav_latitude, uav_longitude, azil, dist)
    (obj_latitude, obj_longitude) = (g['lat2'], g['lon2'])
    return (obj_latitude, obj_longitude)

if __name__ == "__main__":
    uav_latitude = 51.1656129
    uav_longitude = -114.1054339
    uav_altitude = 680.84
    bearing = 2.3774502277374268
    obj_x_px = 0.77
    obj_y_px = 0.58
    (obj_latitude, obj_longitude) = locate(uav_latitude=uav_latitude, uav_longitude= uav_longitude, uav_altitude=uav_altitude, bearing=bearing, 
        obj_x_px=obj_x_px, obj_y_px=obj_y_px)
    print("obj_latitude={}, obj_longitude={}".format(obj_latitude, obj_longitude))