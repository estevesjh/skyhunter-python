# Here we will acquire the photodiode data for a fixed mount postion
import asyncio
import numpy as np
import matplotlib.pyplot as plt

from photodiode import Keysight
from skyhunter import IoptronMount
from config import port, USBSerial

SIDERAL_RATE = 0.004178 # deg/sec
Buffer = 2 # seconds

EXPTIME = float(input("Enter the exposure time in seconds: "))
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


async def mount_continous_altaz_readout(mount, EXPTIME):
    # Set the speed and start continuous altaz reading
    mount.set_arrow_speed(9)
    altaz_task = asyncio.create_task(mount.continous_altaz_reading(EXPTIME + Buffer))

    # Wait for altaz reading task to complete
    await altaz_task

    # Save the data after the task is done
    np.savez('mount_altaz_data.npz', alt=mount.altaz['alt'], az=mount.altaz['az'], time=mount.altaz['time'])
    

async def main(k, mount, EXPTIME):
    await asyncio.gather(
        mount_continous_altaz_readout(mount, EXPTIME),
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

asyncio.run(main(k, mount, EXPTIME))