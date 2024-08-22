from skyhunter import IoptronMount
from config import port

mount = IoptronMount(port)
mount.stop()