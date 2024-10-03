# Here we will move the mount and record the current from the photodiode continously at the same time
# to determine the twilight brightness vs alt
import asyncio
import numpy as np
import matplotlib.pyplot as plt

from photodiode import Keysight
from skyhunter import IoptronMount
from config import port, USBSerial

SIDERAL_RATE = 0.004178 # deg/sec
Buffer = 2 # seconds

EXPTIME = float(input("Enter the exposure time in seconds: "))
DIRECTION = str(input("Enter the slew direction of the mount (up/down): "))

print(f"Exposure time is set to {EXPTIME} seconds")


async def trigger_photodiode(k):
    t_acq = k.params['nsamples'] * k.params['interval']
    
    k.acquire()  # Start acquisition
    for t in range(int(t_acq * 100) + 1):
        print(f'Photodiode Acquisition {t/100:.2f}/{t_acq:.2f} s', end='\r')
        await asyncio.sleep(k.params['interval'] / 100)  # Sleep for the interval

    print('\nAcquisition finished')

    res = k.read_data()
    np.save('data.npy', res)
    plt.plot(res['time'], res['CURR'])
    plt.xlabel('Time (s)')
    plt.ylabel('Current (A)')
    plt.savefig('twilight.png')


async def mount_continous_acquisition(mount, EXPTIME, DIRECTION):
    # Set the speed and start continuous altaz reading
    mount.set_arrow_speed(9)
    asyncio.create_task(mount.continous_altaz_reading(EXPTIME + Buffer))

    # Slew in the given direction indefinitely
    mount.slew_arrow_forever(DIRECTION.lower())
    
    # Wait for the exposure time (plus some buffer)
    await asyncio.sleep(EXPTIME)

    # Stop slewing and wait for Buffer seconds before proceeding
    mount.stop_updown()
    await asyncio.sleep(Buffer)
    
    # Save the data after the task is done
    np.savez('mount_altaz_data.npz', alt=mount.altaz['alt'], az=mount.altaz['az'], time=mount.altaz['time'])
    
    print("Mount stopped")

async def main(k, mount, EXPTIME, DIRECTION):
    await asyncio.gather(
        mount_continous_acquisition(mount, EXPTIME, DIRECTION),
        trigger_photodiode(k)
    )

## Setup Keysight
k = Keysight(USBSerial)
k.sync_tracked_properties()
k.get_params()
k.set_interval(0.1)
k.set_acquisition_time(EXPTIME+Buffer)

## Setup Mount
mount = IoptronMount(port)
mount.get_current_alt_az()
az0, alt0 = mount.azimuth_deg, mount.altitude_deg
mount.unpark()

asyncio.run(main(k, mount, EXPTIME, DIRECTION))