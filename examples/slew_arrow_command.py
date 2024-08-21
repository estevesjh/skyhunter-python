from skyhunter import IoptronMount

# Initialize the mount
mount = IoptronMount(port='/dev/ttyUSB1')

# make sure the telescope is unparked
mount.unpark()

# Slew to a direction for 2 seconds
mount.set_arrow_speed(9)
print("---- Start a series of slews...")
# move to the right
mount.slew_right()
# move to the left
mount.slew_left()
# move up
mount.slew_up()
# move down
mount.slew_down()
print("-------------------------------")