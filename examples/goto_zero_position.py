

from skyhunter import IoptronMount
from config import port

# load the mount
mount = IoptronMount(port)

# make sure the telescope is on the zero position
print("Go to zero position")
mount.goto_zero_position()