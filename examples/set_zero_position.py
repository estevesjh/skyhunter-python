

from skyhunter import IoptronMount
from config import port

# load the mount
mount = IoptronMount(port)

# make sure the telescope is on the zero position
print("Set current state to zero position")
mount.set_zero_position()