from skyhunter import IoptronMount
from config import port
import time

mount = IoptronMount(port)
az_cm = float(input("Insert the desired Azimuth: "))
mount.slew_with_speed(az_cm, name="az", speed=8, niters=5, tol=0.5)

# print("")
# print("Waiting for 5 seconds...")
# time.sleep(5)
# print("")

# az_cmd = float(input("Insert the desired Altitude: "))
# mount.slew_with_speed(az_cmd, name="alt", speed=8, niters=5, tol=0.5)
