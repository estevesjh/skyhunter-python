from skyhunter import IoptronMount
from config import port
import time

mount = IoptronMount(port)

# print the current alt,az
print("-------------------------------")
print("Current Cordinates:")
mount.get_current_alt_az()
alt_cmd = float(input("Insert the desired Altitude: "))
az_cmd  = float(input("Insert the desired Azimuth : "))

# Slew to Alt, Az
mount.unpark()
mount.slew_to_alt_az(alt_cmd, az_cmd)
mount.get_system_state(verbose=False)

print("Waiting mount to slew...")
# while mount.system_status.is_sleewing:
for i in range(5):
    time.sleep(5)
    #mount.get_system_state(verbose=False)
    mount.get_current_alt_az()
print(f"elapsed time: {round(mount.last_update - mount.last_slew, 2)} sec")

print("Mount is done slewing.")
print("Mount moved to:")
mount.get_current_alt_az()
print("-------------------------------")