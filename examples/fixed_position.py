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
path = '/home/estevesjh/Documents/github/skyhunter-python/DATA/keysight/'
# Set initial parameters
AZ_SLEW_TIME = 5
AZ_STEPS = 5
AZ_MAX = 90

# User input
NSTEPS = int(input("Enter the number of snake steps: "))
NSAMPLES = input("Enter the number of samples")
name = str(input("Enter the name of the file"))

# Initiate the mount, keysight and the twilight database
## Setup Keysight
k = Keysight(USBSerial)
k.sync_tracked_properties()
k.get_params()
k.set_nsamples(NSAMPLES)

## Setup Mount
mount = IoptronMount(port)
mount.get_current_alt_az()
az_current, alt_current = mount.azimuth_deg, mount.altitude_deg

## Setup TwilightMonitorDatabase
day = datetime.now().day
month = datetime.now().month
year = datetime.now().year
db = TwilightMonitorDatabase(day, month, year, path=databaseRoot)

## Step 1) 
for i in range(NSTEPS):
    print(f"Taking data for step {i+1}/{NSTEPS}")
    k.start_measurement()
    out = k.datavector
    
    time.sleep(0.5)
    # Save the datavector for each step
    np.save(f'{path}/{name}_snake_data_{i:05d}.npz',out)
    print(f"Data saved to {name}_snake_data_{i:05d}.npz")
