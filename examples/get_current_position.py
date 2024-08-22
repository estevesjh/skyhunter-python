from skyhunter import IoptronMount
from config import port

# Example usage
mount = IoptronMount(port)
mount.get_current_alt_az()