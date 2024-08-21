from skyhunter import IoptronMount
import time

# Initialize the mount
mount = IoptronMount(port='/dev/ttyUSB1')

# print the current alt,az
print("-------------------------------")
print("Current Cordinates:")
mount.get_current_alt_az()

# Slew to Alt, Az
mount.slew_to_alt_az(30, 0)
mount.get_system_state(verbose=False)

print("Waiting mount to slew...")
while mount.system_status.is_sleewing:
    time.sleep(5)
    mount.get_system_state(verbose=False)
    print(f"elapsed time: {round(mount.last_update - mount.last_slew, 2)} sec")

print("Mount is done slewing.")
print("Mount moved to:")
mount.get_current_alt_az()
print("-------------------------------")