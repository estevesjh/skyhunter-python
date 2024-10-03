import time
from skyhunter import IoptronMount
from config import port

# Set initial parameters
time_alt = float(input("Enter the number of seconds to slew in the altitude direction: "))
time_az = float(input("Enter the number of seconds to slew in the azimuth direction: "))
nsteps = int(input("Enter the number of snake steps: "))

# load the mount
mount = IoptronMount(port)

# set maximum speed
mount.set_max_speed()

# make sure the telescope is on the zero position
print("Moving to zero position")
mount.goto_zero_position()
mount.get_system_state(verbose=False)

# make sure the telescope is not slewing
if mount.system_status.is_sleewing:
    print("Telescope is slewing to zero position, waiting for it to stop...")
    while mount.is_slewing():
        time.sleep(1)

print("Telescope Status")
mount.get_system_state(verbose=True)

# make sure the telescope is unparked
mount.unpark()

print(5*"----")
print("Starting snake scheduler")
print(5*"----")
print("")

for i in range(nsteps):
    # make sure the telescope is not slewing
    mount.get_system_state(verbose=False)
    while mount.is_slewing():
        print("Telescope is slewing, waiting for it to stop...")
        time.sleep(0.5)
    
    print(5*"-----")
    print(f"Finish snake {i}")
    direction = "down" if i % 2 == 0 else "up"
    print(f"---- Slew to the {direction} for {time_alt} seconds: {i}")
    getattr(mount, f"slew_{direction}")(time_alt, is_freerun=True)
    time.sleep(0.5)
    mount.continous_altaz_reading(time_alt, interval=0.5, verbose=True)
    mount.stop_updown()
    print("")
    time.sleep(2)

    # make sure the telescope is not slewing
    mount.get_system_state(verbose=False)
    while mount.is_slewing():
        print("Telescope is slewing, waiting for it to stop...")
        time.sleep(0.5)

    direction = "left"
    print(f"---- Slew to the {direction} for {time_az} seconds: {i}")
    getattr(mount, f"slew_{direction}")(time_az, is_freerun=True)
    mount.continous_altaz_reading(time_az, interval=0.1, verbose=True)
    mount.stop_leftright()
    print(5*"----")
    print("")
    time.sleep(1)

# print("Stop the mount")
# mount.stop()
