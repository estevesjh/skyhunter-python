from skyhunter import IoptronMount
import time

# Initialize the mount
mount = IoptronMount(port='/dev/ttyUSB1')

print("Parking the mount...")
parked = mount.park()
mount.get_system_state(verbose=True)

print("Waiting for the mount to park...")
while not mount.system_status.is_parked:
    time.sleep(1)
    mount.get_system_state(verbose=False)
print("Mount is parked.")