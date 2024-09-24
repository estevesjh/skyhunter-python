import asyncio
import numpy as np
import matplotlib.pyplot as plt
import time

from photodiode import Keysight
from skyhunter import IoptronMount
from twmdb import TwilightMonitorDatabase

from config import port, USBSerial, databaseRoot
from helper import slew_in_altitude, start_measurement, slew_in_azimuth

from datetime import datetime
day = datetime.now().day

# Set initial parameters
AZ_STEPS = 5
AZ_MAX = 180
AZ_MIN = 0

ZP_ELEVATION = 80 # degrees
ZP_MIN = 20 # degrees
NSTEPS = 5
EL_SLEW_TIME = 3.5 # sec; slew time in altitude direction

DEAD_TIME = 0.5 # sec; wait after a slew
tol = 0.5 # deg; pointing precision

def section(str):
    print(2*"--------------------")
    print("Section: ", str)
    print(2*"--------------------")

# Initiate the mount, keysight and the twilight database
section("setup mount and electrometer")
## Setup Keysight
k = Keysight(USBSerial)
k.sync_tracked_properties()

## Setup Mount
mount = IoptronMount(port)
mount.set_arrow_speed(9)
mount.get_current_alt_az()
print("")

az_current, alt_current = mount.azimuth_deg, mount.altitude_deg

## Setup TwilightMonitorDatabase
day = datetime.now().day
month = datetime.now().month
year = datetime.now().year
db = TwilightMonitorDatabase(day, month, year, path=databaseRoot)

## Step 1) Check mount state
section("Check the mount state")
mount.get_system_state(verbose=False)
if mount.system_status.is_home:
    print("Mount is not home. Go to zero-point...")
    mount.unpark()
    is_ready = bool(input("Is the mount ready to move? (y/n)")=='y')
    if is_ready:
        pass
    else:
        raise ValueError("Mount is not ready to move. Run goto_home. Aborting...")
else:
    raise ValueError("Mount is not ready to move. Run goto_zero_position. Aborting...")

## Step 2) Move to reference position
section("Move to zero position")
t0 = time.time()
mount.goto_elevation(ZP_ELEVATION, tol=tol, speed=9, niters=5)
time.sleep(DEAD_TIME)

## Step 3) Start the snake
def snake(speed=9, tol=3, niters=3):
    # elevetations = np.linspace(ZP_ELEVATION, ZP_MIN, NSTEPS)
    direction = 'up'
    toto = [alt_current]
    start_measurement(mount, k, db)

    for i in range(NSTEPS):
        print("--------------------")
        print("snake step", i+1)
        # Slew in altitude direction and measure
        mount.set_arrow_speed(speed)
        slew_in_altitude(mount, EL_SLEW_TIME, direction)
        # mount.goto_elevation(elevetations[i], speed, tol, niters)
        start_measurement(mount, k, db)
        el_current = mount.altitude_deg
        toto.append(el_current)
    print("End of snake step")
    return toto

cmd_az_vec = np.linspace(AZ_MIN, AZ_MAX, AZ_STEPS)
az_vec = [az_current]
el_vec = []
# Loop through azimuth and altitude slews
for az_step in range(1,AZ_STEPS):
    section(f"Azimuth step {az_step+1}")
    # go down/up on altitude
    els = snake()

    print("")
    section(f"Moving in Azimuth direction")
    # After altitude steps, slew in azimuth direction
    # slew_in_azimuth(mount, AZ_SLEW_TIME)
    time.sleep(DEAD_TIME)
    mount.goto_azimuth(cmd_az_vec[az_step], speed=9, tol=tol, niters=5)

    # Move to ZP elevation
    mount.goto_elevation(ZP_ELEVATION, tol=tol)
    time.sleep(DEAD_TIME)

    mount.get_current_alt_az()
    # Get the current azimuth
    az_current, alt_current = mount.azimuth_deg, mount.altitude_deg
    az_vec.append(az_current)
    el_vec.append(els)

    # Check if the azimuth is within limits
    if az_current >= AZ_MAX:
        print("Reached maximum azimuth limit. Stopping acquisition.")
        break

print("Acquisition completed.")
db.close()

# Save the data
np.savez('snake_data.npz', az=az_vec, el=el_vec)
print("Data saved to snake_data.npz")

total_time = time.time() - t0
print(f"Total time: {total_time} seconds")