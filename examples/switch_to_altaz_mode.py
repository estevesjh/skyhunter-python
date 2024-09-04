from skyhunter import IoptronMount
from config import port

# Mount setup
mount = IoptronMount(port)

# Get current latitude and longitude
status = mount.get_system_state()

# Switch to AltAz mode
# mount.switch_to_altaz_mode()

# Cambridge, MA
lat, lon = 90, -71.0589
mount.set_lat_long(lat, lon)

# Check if the mount is in AltAz mode
# The latitude should be 90deg (i.e. north pole)
mount.get_system_state()