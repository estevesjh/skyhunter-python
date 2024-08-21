from skyhunter import IoptronMount

# Initialize the mount
mount = IoptronMount(port='/dev/ttyUSB1')
mount.get_time_information()