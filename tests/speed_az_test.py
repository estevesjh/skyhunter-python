from skyhunter import IoptronMount
from dynamical_test import IoptronMountTest

import matplotlib.pyplot as plt
import numpy as np
import time

t0 = time.time()
name = 'test_0001'
slewTime = 3.0 # seconds
slewSteps = 15 # steps
# it goes up to 175 degrees with 14 steps of 3.4 seconds

# Initialize the mount (make sure the port is correct)
mount = IoptronMount(port='/dev/ttyUSB0')

# Create the test object
mount_test = IoptronMountTest(mount)

# Perform a basic slew test
results = mount_test.slew_fixed_duration_test(slewTime, slewSteps, direction='az')
print("Basic Slew Az Test Result:", results['slew_angle'])
print("Slew Speed Test Result:", results['slew_speed'])

print(6*"-----")
print(f"Elapsed Test time: {time.time() - t0}")
print(6*"-----")

mount_test.plot_slew_speed_row(results, direction='az', name=f'plots/speed_vs_azimuth_{name}')
np.savez(f'DATA/tests/speed_vs_azimuth_{name}', **results)