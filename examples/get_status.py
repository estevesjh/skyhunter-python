from skyhunter import IoptronMount

# Example usage
mount = IoptronMount(port='/dev/ttyUSB1')
status = mount.get_system_state()
