# Here we will move the mount and record the current from the photodiode
# to determine the twilight brightness vs alt
import time
import numpy as np
import matplotlib.pyplot as plt

from photodiode import Keysight
from skyhunter import IoptronMount
from config import port

SIDERAL_RATE = 0.004178 # deg/sec

## Setup Keysight
k = Keysight()
# k.sync_tracked_properties()
k.get_params()
k.set_interval(0.1)
k.set_acquisition_time(10)
time.sleep(2)

## Setup Mount
mount = IoptronMount(port)
mount.get_current_alt_az()
az0, alt0 = mount.azimuth_deg, mount.altitude_deg
mount.unpark()

def trigger_photodiode():
    # k.reset()
    k.acquire()
    mount.stop()
    time.sleep(1)
    return k.read_data()

def trigger_mount():
    mount.set_arrow_speed(7)
    mount.slew_arrow_forever('down')

trigger_mount()
res = trigger_photodiode()

time.sleep(5)
mount.get_current_alt_az()
azEnd, altEnd = mount.azimuth_deg, mount.altitude_deg

np.save('data.npy', res)
plt.plot(res['time'],res['CURR'])
plt.xlabel('Time (s)')
plt.ylabel('Current (A)')
plt.savefig('twilight.png')