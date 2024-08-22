from skyhunter import IoptronMount
from config import port

mount = IoptronMount(port)
mount.get_time_information()