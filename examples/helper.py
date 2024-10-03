import asyncio
import datetime
import numpy as np
import matplotlib.pyplot as plt

from photodiode import Keysight
from skyhunter import IoptronMount
from twmdb import TwilightMonitorDatabase

from config import port, USBSerial, databaseRoot

## Check the mount state
def check_mount_state(mount):
    mount.get_system_state(verbose=False)

    if mount.system_status.is_parked:
        print("Mount is parked. Unparking...")
        mount.unpark()
        is_ready = input("Is the mount ready to move? (y/n)").lower() == 'y'
        if is_ready:
            return True
        else:
            raise ValueError("Mount is not ready to move. Please check the mount status.")
    elif not mount.system_status.is_ready:
        raise ValueError("Mount is not ready. Please check the mount status.")
    return True

## Function to slew in altitude direction (up/down)
def slew_in_altitude(mount, el_slew_time, direction, dead_time=0.5):
    print(f"Moving altitude for {el_slew_time} seconds.")
    # mount.slew_up(el_slew_time)
    getattr(mount, f"slew_{direction}")(el_slew_time, is_freerun=False)
    
    # Wait for the mount to move
    # await asyncio.sleep(el_slew_time)

    # # Check if the mount is settled
    # if not mount.is_slewing():
    #     print("Mount is not settled. Waiting for it to settle...")
    #     await asyncio.sleep(dead_time)  # Additional wait for settlement
    # else:
    #     print("Mount is settled.")

## Function to start electrometer and measure alt/az
def start_measurement(mount, keysight, db):
    # Start electrometer measurements
    print("Starting electrometer measurement...")
    keysight_data = keysight.start_measurement()
    acq_time = keysight.t_acq
    
    # Get current mount position
    try:
        mount.get_current_alt_az()
        alt_current, az_current = mount.altitude_deg, mount.azimuth_deg

    except:
        print("error reading position")
        alt_current, az_current = mount.altitude_deg, mount.azimuth_deg
        # mount.get_current_alt_az()

    # Add exposure to the database
    timestamp = datetime.datetime.utcnow()
    db.add_exposure(
        timestamp=timestamp,
        alt=np.round(alt_current,5),
        az=np.round(az_current,5),
        exp_time_cmd = acq_time,
        exp_time = keysight_data['teff'],
        filter_type='Empty',  # Assuming filter is Empty
        current_mean=keysight_data['mean'],
        current_std=keysight_data['std']
    )
    db.save()
    print(f"Exposure added to the database at {timestamp}.")
    
    # Wait before proceeding to the next step
    # await asyncio.sleep(1)

## Function to slew in azimuth direction
def slew_in_azimuth(mount, az_slew_time, direction='right'):
    print(f"Moving azimuth for {az_slew_time} seconds.")
    getattr(mount, f"slew_{direction}")(az_slew_time, is_freerun=False)
    mount.get_current_alt_az()

## Main loop for snake acquisition
async def run_acquisition(mount, keysight, db, n_steps, el_slew_time, az_slew_time, az_max):
    az_current = mount.azimuth_deg

    # Loop through azimuth and altitude slews
    while az_current < az_max:
        for _ in range(n_steps):
            # Slew in altitude direction and measure
            await slew_in_altitude(mount, el_slew_time)
            await start_measurement(mount, keysight, db, el_slew_time)

        # After altitude steps, slew in azimuth direction
        await slew_in_azimuth(mount, az_slew_time)
        az_current = mount.azimuth_deg

        # Check if the azimuth is within limits
        if az_current >= az_max:
            print("Reached maximum azimuth limit. Stopping acquisition.")
            break

    print("Acquisition completed.")
    keysight.stop_measurement()


## Running the acquisition process
# async def main():
#     if check_mount_state(mount):
#         print("Mount is ready to move. Starting acquisition.")
#         await run_acquisition(mount, k, db, NSTEPS, EL_SLEW_TIME, AZ_SLEW_TIME, AZ_MAX)
#     else:
#         print("Mount is not ready. Please check and try again.")


# # Run the asyncio loop
# if __name__ == "__main__":
#     asyncio.run(main())
