from lib.mpu6050 import MPU6050
from lib.micropyGPS import MicropyGPS
from time import sleep
from umqtt.robust import MQTTClient
import boot
import ujson
from lib.micropyGPS import MicropyGPS
import machine as m


networkPPP = None
# def check_modem():
#     while not boot.ppp.isconnected() or not boot.networkPPP.isconnected() or not networkPPP.isconnected():
#         print("Waiting for modem to connect...")
#         networkPPP = boot.ppp_connect()
#         sleep(10)
clientID = "esp32wroom32"
client = MQTTClient("clientID", "broker.emqx.io", 1883, user = "", password = "")
my_gps = MicropyGPS()
gps_serial = m.UART(1, baudrate=9600, tx=13, rx=12)

def convert_to_decimal(degrees, direction):
    decimal = degrees[0] + (degrees[1] / 60)
    if direction in ('S', 'W'):
        decimal = -decimal
    return decimal


def tes_cb(topic, msg):
    print("Received message: ", topic, msg)
    
def convert_to_decimal(degrees, direction):
    decimal = degrees[0] + (degrees[1] / 60)
    if direction in ('S', 'W'):
        decimal = -decimal
    return decimal

try:
    client.connect()
    print("Connected to MQTT broker")
except Exception as e:
    print("Error: ", e)

try:
    client.set_callback(tes_cb)
    client.subscribe(b"/tes")
except Exception as e:
    print("Error: ", e)



def main():
    # Initialize the MPU6050 sensor
    mpu = MPU6050()

    # Read and print the accelerometer and gyroscope data
    while True:
        if gps_serial.any():
            data = gps_serial.read()
            for byte in data:
                status = my_gps.update(chr(byte))
                if status is not None:
                    lat = convert_to_decimal(my_gps.latitude, my_gps.latitude[2])
                    lon = convert_to_decimal(my_gps.longitude, my_gps.longitude[2])
                    sat = my_gps.satellites_in_use
                    alt = my_gps.altitude
                    print('---------------------------------')
                    print('UTC Timestamp:', my_gps.timestamp)
                    print('Date:', my_gps.date_string('long'))
                    print(f"Latitude: {lat:.6f}, Longitude: {lon:.6f}")
                    print('Altitude:', my_gps.altitude)
                    print('Satellites in use:', my_gps.satellites_in_use)
                    print('HDOP:', my_gps.hdop)
                
           
            
        accel = mpu.read_accel_data() # read the accelerometer [ms^-2]
        aX = accel["x"]
        aY = accel["y"]
        aZ = accel["z"]
        print("x: " + str(aX) + " y: " + str(aY) + " z: " + str(aZ))
        client.check_msg()
        sleep(0.5)
        # check_modem()
        
if __name__ == "__main__":
    main()