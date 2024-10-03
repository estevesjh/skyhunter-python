from skyhunter import IoptronMount
from dynamical_test import IoptronMountTest

import matplotlib.pyplot as plt
import numpy as np
import time

t0 = time.time()

AZ_STEPS = 7
AZ_SLEW_TIME = 7.52 # seconds
# AZ = [0, 15.57121,30.89845,46.44381,61.94442,77.22729]
AZ_PRED = np.linspace(0, 180, AZ_STEPS)
EL_STEPS = 6 # steps
EL_SLEW_TIME = 2.5 # seconds

run_test = True
plot_curve = False
testName ='at_dome_test_0001'

# Initialize the mount (make sure the port is correct)
mount = IoptronMount(port='/dev/ttyUSB0')

# Create the test object
mount_test = IoptronMountTest(mount)

if run_test:
    # Perform a basic slew test to inital position
    mount.slew_down(3.0)

    for i in range(AZ_STEPS):
        print(6*"-------")
        print("Cycle:", i+1)
        print(6*"-------")

        name = f'{testName}_cycle_{(i+1):04d}'
    
        # Perform a basic slew test
        results = mount_test.slew_fixed_duration_test(EL_SLEW_TIME, EL_STEPS, direction='alt')
        print("Basic Slew Alt Test Result:", results['slew_angle'])
        print("Slew Speed Test Result:", results['slew_speed'])
        results['AZ'] = mount.azimuth_deg

        slew_up_time = (90-results['slew_angle'][-1])/4.0#np.median(np.abs(results['slew_speed']))
        mount.slew_up(slew_up_time)
        time.sleep(mount.slew_pause)
        mount.get_current_alt_az()

        cTime = time.time() - t0
        print(6*"-----")
        print(f"Elapsed Cycle time: {cTime}")
        print(6*"-----")
        mount_test.plot_slew_speed_row(results, name=f'plots/speed_vs_altitude_{name}')
        np.savez(f'DATA/tests/speed_vs_altitude_{name}', **results)

        print("Go to next az position")
        try:
            mount.slew_right(AZ_SLEW_TIME)
        except:
            mount.goto_azimuth(AZ_PRED[i], tol=1, speed=9, niters=5)

        print("Go to initial el position")
        mount.slew_down(2.0)

        # mount.goto_elevation(results['slew_angle'][0], tol=0.5, speed=9, niters=5)

if plot_curve:
    figs = [None,None]
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink']
    AZ = []
    for i in range(AZ_STEPS):
        print(6*"-------")
        print("Cycle:", i+1)
        print(6*"-------")

        name = f'cycle_{(i+1):04d}'
        results = np.load(f'DATA/tests/speed_vs_altitude_{name}.npz')
        AZ.append(np.where(results['AZ']<0, 180, results['AZ']))
        figs = mount_test.plot_slew_speed_row(results, figs=figs, color1=colors[i], color2=colors[i],
                                       name=f'plots/speed_vs_altitude_map')

    figs[1][0].get_legend().remove()
    figs[1][1].legend([f'Cycle {i+1}: Az={AZ[i]:0.1f} deg' for i in range(AZ_STEPS)], loc='upper right')

    figs[0].tight_layout()
    figs[0].savefig(f'plots/speed_vs_altitude_map.png',dpi=120)

        

