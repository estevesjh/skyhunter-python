import asyncio
import numpy as np
import matplotlib.pyplot as plt

from photodiode import Keysight
from skyhunter import IoptronMount
from twmdb import TwilightMonitorDatabase

from config import port, USBSerial, databaseRoot
from helper import slew_in_altitude, start_measurement, slew_in_azimuth

from datetime import datetime
day = datetime.now().day

# Set initial parameters
AZ_SLEW_TIME = 5
AZ_STEPS = 5
AZ_MAX = 90

# User input
NSTEPS = int(input("Enter the number of snake steps: "))
EL_SLEW_TIME = float(input("Enter the number of seconds to slew in the altitude direction: "))


# Initiate the mount, keysight and the twilight database
## Setup Keysight
k = Keysight(USBSerial)
k.sync_tracked_properties()
k.get_params()

## Setup Mount
mount = IoptronMount(port)
mount.get_current_alt_az()
az_current, alt_current = mount.azimuth_deg, mount.altitude_deg

## Setup TwilightMonitorDatabase
day = datetime.now().day
month = datetime.now().month
year = datetime.now().year
db = TwilightMonitorDatabase(day, month, year, path=databaseRoot)

## Step 1) Check mount state
mount.get_system_state(verbose=False)
if mount.system_status.is_home:
    print("Mount is not home. Go to zero-point...")
    mount.unpark()
    is_ready = bool(input("Is the mount ready to move? (y/n)"))
    if is_ready:
        pass
    else:
        raise ValueError("Mount is not ready to move. Run goto_home. Aborting...")
else:
    raise ValueError("Mount is not ready to move. Run goto_zero_position. Aborting...")

def snake():
    direction = 'up' if alt_current < 85 else 'down'
    toto = [alt_current]
    
    start_measurement(mount, k, db, EL_SLEW_TIME)
    for i in range(NSTEPS):
        print("snake step", i+1)
        # Slew in altitude direction and measure
        slew_in_altitude(mount, EL_SLEW_TIME, direction)
        start_measurement(mount, k, db, EL_SLEW_TIME)
        el_current = mount.altitude_deg
        toto.append(el_current)
    print("End of snake step")
    return toto


## Step 2) Start the snake

az_vec = [az_current]
el_vec = []
# Loop through azimuth and altitude slews
for az_step in range(AZ_STEPS):
    # go down/up on altitude
    els = snake()

    # After altitude steps, slew in azimuth direction
    slew_in_azimuth(mount, AZ_SLEW_TIME)

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