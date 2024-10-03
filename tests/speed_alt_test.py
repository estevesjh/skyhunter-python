from skyhunter import IoptronMount
from dynamical_test import IoptronMountTest

import matplotlib.pyplot as plt
import numpy as np
import time

t0 = time.time()

name = 'at_dome_test_0001'
slewTime = 2.5 # seconds
slewSteps = 6 # steps

# Initialize the mount (make sure the port is correct)
mount = IoptronMount(port='/dev/ttyUSB0')

# Create the test object
mount_test = IoptronMountTest(mount)

# Perform a basic slew test to inital position
mount.slew_down(3.0)
# results = mount_test.target_slew_alt_test(80, tol=0.5, speed=9, niters=5)

# Perform a basic slew test
results = mount_test.slew_fixed_duration_test(slewTime, slewSteps, direction='alt')
print("Basic Slew Alt Test Result:", results['slew_angle'])
print("Slew Speed Test Result:", results['slew_speed'])

slew_up_time = (80-results['slew_angle'][-1])/np.median(np.abs(results['slew_speed']))
mount.slew_up(slew_up_time)
time.sleep(mount.slew_pause)
mount.get_current_alt_az()

print(6*"-----")
print(f"Elapsed Test time: {time.time() - t0}")
print(6*"-----")

mount_test.plot_slew_speed_row(results, name=f'plots/speed_vs_altitude_{name}')
np.savez(f'DATA/tests/speed_vs_altitude_{name}', **results)