from skyhunter import IoptronMount
from config import port
import time


mount = IoptronMount(port)
print("------------------------------------")
print("Set the park position to a given alt/az")
alt_cmd = float(input("Insert the desired Altitude: "))
az_cmd  = float(input("Insert the desired Azimuth : "))
mount.set_park_position(alt_cmd, az_cmd)
mount.unpark()

print("Parking the mount...")
parked = mount.park()
mount.get_system_state(verbose=True)

print("Waiting for the mount to park...")
while not mount.system_status.is_parked:
    time.sleep(1)
    mount.get_system_state(verbose=False)

mount.get_current_alt_az()
print("Mount is parked.")