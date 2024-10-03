from skyhunter import IoptronMount
from config import port
import time

# Example usage
mount = IoptronMount(port)
print("Unparking the mount...")
parked = mount.unpark()
mount.get_system_state(verbose=True)
mount.goto_zero_position()

print("Waiting for the mount to go to home position...")
while not mount.system_status.is_home:
    time.sleep(1)
    mount.get_system_state(verbose=False)
print("Mount is at zero point.")