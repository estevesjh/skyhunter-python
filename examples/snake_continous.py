import asyncio
import datetime
import numpy as np
import matplotlib.pyplot as plt

from photodiode import Keysight
from skyhunter import IoptronMount
from twmdb import TwilightMonitorDatabase

from config import port, USBSerial, databaseRoot

# Set initial parameters
AZ_SLEW_TIME = 5
AZ_MAX = 180

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
az0, alt0 = mount.azimuth_deg, mount.altitude_deg

## Setup TwilightMonitorDatabase
day = datetime.now().day
month = datetime.now().month
year = datetime.now().year
db = TwilightMonitorDatabase(day, month, year, path=databaseRoot)

## Start the main loop

## Step 1) check_mount_state
mount.get_system_state(verbose=False)
if mount.system_status.is_parked:
    print("Mount is parked. Unparking...")
    mount.unpark()
    is_ready = bool(input("Is the mount ready to move? (y/n)"))
    if is_ready:
        pass
    else:
        raise ValueError("Mount is not ready to move. Please check the mount status.")
        exit()
else:
    raise ValueError("Mount is not parked. You should park it first")
    exit()

## Step 2) Move up or down for EL_SLEW_TIME
## Function to slew in altitude direction (up/down)
async def slew_in_altitude(mount, el_slew_time):
    print(f"Moving altitude for {el_slew_time} seconds.")
    mount.move_altitude(el_slew_time)
    
    # Wait for the mount to move
    await asyncio.sleep(el_slew_time)

    # Check if the mount is settled
    if not mount.is_settled():
        print("Mount is not settled. Waiting for it to settle...")
        await asyncio.sleep(2)  # Additional wait for settlement
    else:
        print("Mount is settled.")

## Function to start electrometer and measure alt/az
async def start_measurement(mount, keysight, db, el_slew_time):
    # Start electrometer measurements
    print("Starting electrometer measurement...")
    keysight_data = keysight.start_measurement()

    # Get current mount position
    mount.get_current_alt_az()
    alt_current, az_current = mount.altitude_deg, mount.azimuth_deg

    # Add exposure to the database
    timestamp = datetime.datetime.utcnow()
    db.add_exposure(
        timestamp=timestamp,
        alt=alt_current,
        az=az_current,
        exp_time_cmd=el_slew_time,
        filter_type='Empty',  # Assuming filter is Empty
        current_mean=keysight_data['mean'],
        current_std=keysight_data['std']
    )
    print(f"Exposure added to the database at {timestamp}.")
    
    # Wait before proceeding to the next step
    await asyncio.sleep(1)
    pass

## Function to slew in azimuth direction
async def slew_in_azimuth(mount, az_slew_time):
    print(f"Moving azimuth for {az_slew_time} seconds.")
    mount.move_azimuth(az_slew_time)
    await asyncio.sleep(az_slew_time)
    mount.get_current_alt_az()

## Main loop for snake acquisition
az_current = mount.azimuth_deg
# Loop through azimuth and altitude slews
while az_current < AZ_MAX:
    for i in range(NSTEPS):
        print("Starting snake step", i)
        # Slew in altitude direction and measure
        slew_in_altitude(mount, EL_SLEW_TIME)
        start_measurement(mount, k, db, EL_SLEW_TIME)
    print("End of snake step")
    
    # After altitude steps, slew in azimuth direction
    slew_in_azimuth(mount, AZ_SLEW_TIME)
    az_current = mount.azimuth_deg

    # Check if the azimuth is within limits
    if az_current >= AZ_MAX:
        print("Reached maximum azimuth limit. Stopping acquisition.")
        break

print("Acquisition completed.")
k.stop_measurement()

