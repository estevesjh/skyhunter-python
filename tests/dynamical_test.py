from skyhunter import IoptronMount
from matplotlib import pyplot as plt
import numpy as np
import time

class IoptronMountTest:
    def __init__(self, mount):
        """
        Initialize the mount test class with the existing IoptronMount class.
        
        Args:
            mount: An instance of IoptronMount that controls the mount movement.
        """
        self.mount = mount
        self.timePause = 0.1

    def target_slew_altaz_test(self, alt, az, tol=1, speed=9, niters=10):
        """
        Perform a basic slew test to a specified Alt/Az position and measure the time.
        
        Args:
            alt (float): Altitude target in degrees.
            az (float): Azimuth target in degrees.
        
        Returns:
            dict: Results with slew time and final position.
        """
        print(f"Starting Basic Slew Test to Alt: {alt}°, Az: {az}°")
        start_time = time.time()

        # Command the mount to slew to the given azimuth
        self.mount.goto_azimuth(az, speed, tol, niters)
        
        # command the mount to slew to the given altitude
        self.mount.goto_elevation(alt, speed, tol, niters)

        # Wait for the mount to complete the slew
        while self.mount.is_slewing():
            time.sleep(self.timePause)
        
        end_time = time.time()
        slew_duration = end_time - start_time

        # Get the final position after the slew
        self.mount.get_current_alt_az()

        print(f"Slew completed in {slew_duration:.2f} seconds.")
        print(f"Final Position: Alt: {self.mount.altitude_deg:.2f}°, Az: {self.mount.azimuth_deg:.2f}°")

        return {
            'slew_duration': slew_duration,
            'final_alt': self.mount.altitude_deg,
            'final_az': self.mount.azimuth_deg
        }

    def target_slew_alt_test(self, alt, tol=1, speed=9, niters=10):
        """
        Perform a basic slew test to a specified Alt position and measure the time.
        
        Args:
            alt (float): Altitude target in degrees.
        
        Returns:
            dict: Results with slew time and final position.
        """
        print(f"Starting Basic Slew Test to Alt: {alt}°")
        start_time = time.time()
        
        # command the mount to slew to the given altitude
        self.mount.goto_elevation(alt, speed, tol, niters)

        # Wait for the mount to complete the slew
        while self.mount.is_slewing():
            time.sleep(self.timePause)
        
        end_time = time.time()
        slew_duration = end_time - start_time

        # Get the final position after the slew
        self.mount.get_current_alt_az()

        print(f"Slew completed in {slew_duration:.2f} seconds.")
        print(f"Final Position: Alt: {self.mount.altitude_deg:.2f}°, Az: {self.mount.azimuth_deg:.2f}°")

        return {
            'slew_duration': slew_duration,
            'final_alt': self.mount.altitude_deg,
            'final_az': self.mount.azimuth_deg
        }

    
    def target_slew_az_test(self, az, tol=1, speed=9, niters=10):
        """
        Perform a basic slew test to a specified Az position and measure the time.
        
        Args:
            az (float): Azimuth target in degrees.
        
        Returns:
            dict: Results with slew time and final position.
        """
        print(f"Starting Basic Slew Test to Az: {az}°")
        start_time = time.time()
        
        # command the mount to slew to the given altitude
        self.mount.goto_azimuth(az, speed, tol, niters)

        # Wait for the mount to complete the slew
        while self.mount.is_slewing():
            time.sleep(self.timePause)
        
        end_time = time.time()
        slew_duration = end_time - start_time

        # Get the final position after the slew
        self.mount.get_current_alt_az()

        print(f"Slew completed in {slew_duration:.2f} seconds.")
        print(f"Final Position: Alt: {self.mount.altitude_deg:.2f}°, Az: {self.mount.azimuth_deg:.2f}°")

        return {
            'slew_duration': slew_duration,
            'final_alt': self.mount.altitude_deg,
            'final_az': self.mount.azimuth_deg
        }
    
    def slew_fixed_duration_test(self, SlewTime, nsteps, direction='alt', pauseTime=1):
        """Test the mount slewing for a fixed duration with a number of steps.

        Args:
            time (float): slew time for each step in seconds.
            nsteps (int): number of steps to perform.
            direction (str, optional): alt or az. Defaults to 'alt'.
        """
        self.mount.set_arrow_speed(9)
        self.mount.get_current_alt_az()
        posInitial = {'alt':self.mount.altitude_deg, 'az':self.mount.azimuth_deg}

        results = []
        positions = [posInitial[direction]]
        test_start_time = time.time()
        for i in range(nsteps):
            print(6*"-------")
            print(f"Step {i+1}/{nsteps}")
            start_time = time.time()
            if direction == 'alt':
                self.mount.slew_down(SlewTime)
            elif direction == 'az':
                self.mount.slew_right(SlewTime)
            else:
                raise ValueError("Invalid direction. Use 'alt' or 'az'.")
                        
            end_time = time.time()
            duration = end_time - start_time
            self.mount.get_current_alt_az()
            posEnd = {'alt':self.mount.altitude_deg, 'az':self.mount.azimuth_deg}
            positions.append(posEnd[direction])
            results.append(duration)
            print(f"Step completed in {duration:.2f} seconds.")
            time.sleep(pauseTime)
        test_end_time = time.time()-test_start_time
        print(f"Test completed in {test_end_time:.2f} seconds.")

        out = {}
        out['slew_duration'] = np.array(results)
        out['slew_angle'] = np.array(positions)
        # the speed takes into account the time taken to stop the mount
        out['slew_speed'] = np.diff(np.array(positions))/(np.array(results)-self.mount.slew_pause)
        out['test_duration'] = test_end_time
        out['test_slew_time'] = SlewTime
        out['direction'] = direction
        return out
    
    def speed_test(self, time, nsteps, direction='alt', speed=9):
        """
        Test the mount slewing at different speeds to a target Alt/Az position.
        
        Args:
            alt (float): Altitude target in degrees.
            az (float): Azimuth target in degrees.
            speed (int): Slew speed to test, e.g., 2, 4, 6, 9.
        
        Returns:
            dict: Results for the speed test, including slew time.
        """
        print(f"Testing slew speed: {speed}x")
        self.mount.set_arrow_speed(speed)

        # Perform the basic slew test at the specified speed
        result = self.slew_fixed_duration_test(time, nsteps, direction)

        return result
    
    def backlash_test(self, alt_start, az_start, alt_step, az_step,
                      speed=9, tol=1, niters=5):
        """
        Test the backlash by moving the mount back and forth in small steps and measuring the delay.
        
        Args:
            alt_start (float): Starting Altitude in degrees.
            az_start (float): Starting Azimuth in degrees.
            alt_step (float): Altitude step size in degrees for the test.
            az_step (float): Azimuth step size in degrees for the test.
        
        Returns:
            dict: Backlash test results, including step delays and final positions.
        """
        print(f"Starting Backlash Test at Alt: {alt_start}°, Az: {az_start}° with steps of Alt {alt_step}° and Az {az_step}°")
        results = []

        # Move to starting position
        self.mount.goto_elevation(alt_start, speed, tol, niters)
        self.mount.goto_azimuth(az_start, speed, tol, niters)

        while self.mount.is_slewing():
            time.sleep(self.timePause)

        # Backlash test in Altitude
        for direction in [-1, 1]:  # Test in both directions
            alt_target = alt_start + direction * alt_step
            print(f"Moving Alt by {direction * alt_step}°")
            start_time = time.time()
            self.mount.goto_elevation(alt_target, speed, tol, niters)
            while self.mount.is_slewing():
                time.sleep(self.timePause)
            end_time = time.time()
            
            self.mount.get_current_alt_az()
            final_alt = self.mount.altitude_deg
            final_az = self.mount.azimuth_deg

            delay = end_time - start_time

            print(f"Alt step delay: {delay:.2f} seconds. Final Position: Alt: {final_alt:.2f}°, Az: {final_az:.2f}°")
            results.append({
                'axis': 'Altitude',
                'direction': 'Positive' if direction == 1 else 'Negative',
                'delay': delay,
                'final_position': {'alt': final_alt, 'az': final_az}
            })

        # Backlash test in Azimuth
        for direction in [-1, 1]:  # Test in both directions
            az_target = az_start + direction * az_step
            print(f"Moving Az by {direction * az_step}°")
            start_time = time.time()
            # self.mount.slew_to_alt_az(alt_start, az_target)
            self.mount.goto_azimuth(az_target, speed, tol, niters)
            while self.mount.is_slewing():
                time.sleep(0.5)
            end_time = time.time()
            
            final_alt, final_az = self.mount.get_current_alt_az()
            delay = end_time - start_time

            print(f"Az step delay: {delay:.2f} seconds. Final Position: Alt: {final_alt:.2f}°, Az: {final_az:.2f}°")
            results.append({
                'axis': 'Azimuth',
                'direction': 'Positive' if direction == 1 else 'Negative',
                'delay': delay,
                'final_position': {'alt': final_alt, 'az': final_az}
            })

        return results
    
    def plot_slew_speed_row(self, results, figs=[None, None],
                            direction='alt', name="speed_vs_altitude", 
                            color1='k', color2='r'): 
        """
        Plot the slew speed vs altitude and cumulative (duration - 4) vs altitude in a two-row plot.

        Args:
            results (dict): The results of the slew test, containing 'slew_angle', 'slew_speed', and 'slew_duration'.
            name (str): The name to save the plot file. Default is 'speed_vs_altitude'.
        """
        axis = 'Altitude' if direction == 'alt' else 'Azimuth'
        print(f"Plotting {axis} Slew Speed vs {axis} and Cumulative Slew Duration vs {axis}")
        # Calculate cumulative sum of (duration - 4)
        cum_duration_diff = np.cumsum(results['slew_duration'] - self.mount.slew_pause)
        # Perform linear fit using np.polyfit (1st degree polynomial)
        coefficients = np.polyfit(cum_duration_diff, results['slew_angle'][1:], 1)
        slope = coefficients[0]        
        # Create the polynomial function based on the coefficients
        fit_line = np.poly1d(coefficients)

        if figs[0] is None:
            # Create a two-row plot
            fig, axs = plt.subplots(1, 2, figsize=(8, 5))
        else:
            fig, axs = figs

        # First plot: Speed vs Altitude
        axs[1].plot(results['slew_angle'][1:], results['slew_speed'], 'o-', color=color1)
        axs[1].axhline(slope, color=color2, linestyle='--', label='_nolegend_')
        axs[1].set_xlabel(f'{axis} [deg]')
        axs[1].set_ylabel('Speed [deg/s]')
        axs[1].set_title(f'Speed vs {axis}')

        # Second plot: Cumulative (Duration - 4) vs Altitude
        axs[0].plot(cum_duration_diff, results['slew_angle'][1:], 'o-', color=color1, label=f'Duration steps: {np.mean(results["slew_duration"]-self.mount.slew_pause):.2f} s')
        # Plot the regression line (fit line)
        axs[0].plot(cum_duration_diff, fit_line(cum_duration_diff), '--', color=color2, label=f"Slope: {slope:.4f} (deg/s)")
        axs[0].set_ylabel(f'{axis} [deg]')
        axs[0].set_xlabel('Cumulative Slew Duration [s]')
        axs[0].set_title(f'Cumulative Slew Duration vs {axis}')
        axs[0].legend()

        # Adjust layout and save the figure
        plt.tight_layout()
        plt.savefig(f'{name}.png', dpi=120)
        return fig, axs

if __name__ == "__main__":
    name = '0001'
    slewTime = 1.4 # seconds
    slewSteps = 30

    # Initialize the mount (make sure the port is correct)
    mount = IoptronMount(port='/dev/ttyUSB0')

    # Create the test object
    mount_test = IoptronMountTest(mount)

    # Perform a basic slew test
    results = mount_test.slew_fixed_duration_test(slewTime, slewSteps, direction='alt')
    print("Basic Slew Alt Test Result:", results['slew_angle'])
    print("Slew Speed Test Result:", results['slew_speed'])

    import matplotlib.pyplot as plt
    plt.plot(results['slew_angle'][1:], results['slew_speed'], 'o-')
    # plt.scatter(0.5*(pos0[1:]+pos0[:-1]), speed0)
    plt.xlabel('Altitude [deg]')
    plt.ylabel('Speed [deg/s]')
    plt.title('Speed vs Altitude')
    plt.savefig('speed_vs_altitude.png', dpi=120)
    np.savez(f'speed_vs_altitude_{name}', **results)

    slew1 = mount_test.slew_fixed_duration_test(slewTime, 5, direction='az')
    print("Basic Slew Az Test Result:", slew1)
    
    # # Speed test
    # speed_test = mount_test.speed_test(5, 3, direction='alt', speed=9)
    # print("Speed Test Result:", speed_test)

    # # # Perform a basic slew test
    # # slew_alt_result = mount_test.target_slew_alt_test(60.0)
    # # print("Target Slew Alt Test Result:", slew_alt_result)

    # slew_az_result = mount_test.target_slew_az_test(-35.0)
    # print("Target Slew Az Test Result:", slew_az_result)

    # # Perform a variable slew speed test with speeds 2x, 4x, 6x, 9x
    # speed_results = mount_test.variable_slew_speed_test(alt=30.0, az=45.0, speeds=[2, 4, 6, 9])
    # print("Variable Slew Speed Test Results:", speed_results)

    # # Perform a backlash test with small steps
    # backlash_results = mount_test.backlash_test(alt_start=30.0, az_start=45.0, alt_step=0.5, az_step=0.5)
    # print("Backlash Test Results:", backlash_results)
