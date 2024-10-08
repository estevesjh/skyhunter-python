from skyhunter import IoptronMount
from config import port
import time

# Example usage
mount = IoptronMount(port)
print("Parking the mount...")
parked = mount.park()
mount.get_system_state(verbose=True)

print("Waiting for the mount to park...")
while not mount.system_status.is_parked:
    time.sleep(1)
    mount.get_system_state(verbose=False)
print("Mount is parked.")