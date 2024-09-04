import time
import sys
import numpy as np
from dataclasses import dataclass, field
from astropy.time import Time, TimeDelta
import astropy.units as u

from .usb_serial import USBSerial
from . import utils

# TODO: Add arrows, stop, and fine-tunning method

class IoptronMount:
    def __init__(self, port, baudrate=115200):
        print("Welcome to the iOptron Mount controller.")
        self.scope = USBSerial(port=port, baud=baudrate, log_level = 'DEBUG')
        self.scope.open()

        if self.check_connection():
            print("Connection established.")
        else:
            print("Connection failed.")
            sys.exit(1)

        self.OFFSET_ALT = 0
        self.OFFSET_AZ = 0

        # Time information
        self.time = TimeInfo()
        self.set_current_time()
        
        # System status
        self.system_status = SystemStatus()
        self.get_system_state(verbose=False)

        # Mount version
        self.mount = self.get_mount_version()

        # Set the altitude limit to -89 deg (the range is -89 to 89)
        self.set_alt_limit(-89)

    # Destructor that gets called when the object is destroyed
    def __del__(self):
        # Close the serial connection
        try:
            self.scope.close()
        except:
            print("CLEANUP: not needed or was unclean")

    def get_system_state(self, verbose=True):
        """Get (a lot) of status from the mount. Get movement
        and tracking information."""
        self.scope.send(":GLS#")
        response_data = self.scope.recv()
        status_code = response_data[18:19]

        # get latitude and longitude
        pos = utils.parse_alt_az(response_data[:18], is_latlong=True)
        self.latitude_deg = pos[1]-90
        self.longitude_deg = pos[0]

        # get sysetm status
        self.system_status.update_status(status_code)
        if verbose:
            print(self.system_status)
            print(f"Latitude: {self.latitude_deg:0.5f} deg, Longitude: {self.longitude_deg:0.5f} deg")

        self.last_update = time.time()

    def set_alt(self, alt):
        alt = self.offset_alt(alt)
        sign = '+' if alt >= 0 else '-'
        alt_str = f"{sign}{int(abs(alt) * 360000):08d}#"  # Convert Az to 0.01 arc-seconds
        command = f":Sa{alt_str}"
        self.scope.send(command)
        response = self.scope.recv()
        self.print_received(command, response)
        return response == "1"

    def set_az(self, az):
        az = self.offset_az(az)
        sign = '+' if az >= 0 else '-'
        az_str = f"{int(abs(az) * 360000):09d}#"  # Convert Az to 0.01 arc-seconds
        command = f":SZ{az_str}"
        self.scope.send(command)
        response = self.scope.recv()
        self.print_received(command, response)
        return 

    def slew_to_alt_az(self, alt, az):
        """ slew to a specific altitude and azimuth. """
        print('Setting the altitude and azimuth...')
        self.set_az(az)
        self.set_alt(alt)

        print('Slewing to the altitude and azimuth...')
        self.slew_to_defined_position()
        # print('if you need to stop the mount, use the stop() method.')
    
    def slew_to_defined_position(self):
        """Slew to the most recently defined position."""
        if self.system_status.is_parked:
            print("Mount is parked. Unparking...")
            self.unpark()
        
        self.scope.send(":MSS#")
        response = self.scope.recv()
        self.last_slew = time.time()
        return response == "1"
    
    def slew_with_speed(self, pos, name='alt', speed=9, tol=5, niters=100):
        """Slew to the given position with the given speed."""
        self.set_arrow_speed(speed)

        SIDREAL_RATE = 15.041 / 3600  # deg/sec
        vel_book = {2:2, 3:8, 4:16, 5:64, 6:128, 7:256, 8:512, 9:900}
        vel = vel_book[speed] * SIDREAL_RATE / 1.25 # deg/sec
        
        if self.system_status.is_parked:
            print("Mount is parked. Unparking...")
            self.unpark()
        

        diff = 180
        count = 0
        # NEEDS DEBUGGING
        if name == 'alt':
            while abs(diff) > tol:
                self.get_current_alt_az()
                alt = self.altitude_deg
                diff = alt-pos
                print(f"The position difference is: {diff:0.5f} deg")
                if diff > 0:
                    # print("Slewing down...")
                    self.slew_down(abs(diff)/vel)
                else:
                    # print("Slewing up...")
                    self.slew_up(abs(diff)/vel)
                # time.sleep(1)
                count+=1
                if count > niters:
                    print("The mount achieved the maximum number of iterations.")
                    break
        
        # WORKING WELL
        elif name == 'az':
            while abs(diff) > tol:
                self.get_current_alt_az()
                az = self.azimuth_deg
                diff = utils.angular_difference(az, pos)
                print(f"The position difference is: {diff:0.5f} deg")
                if diff > 0:
                    print("Slewing right...")
                    self.slew_right(abs(diff)/vel)
                else:
                    print("Slewing left...")
                    self.slew_left(abs(diff)/vel)
                # time.sleep(1)
                count+=1
                if count > niters:
                    print("The mount achieved the maximum number of iterations.")
                    break

    def slew_right(self, moving_time=2, is_freerun=False):
        """Slew the mount to the right for a given time."""
        print(f"Slewing right for {moving_time} seconds...")
        self.slew_arrow_forever('right')
        if not is_freerun:
            time.sleep(moving_time)
            self.stop()
    
    def slew_left(self, moving_time=2, is_freerun=False):
        """Slew the mount to the left for a given time."""
        print(f"Slewing left for {moving_time} seconds...")
        self.slew_arrow_forever('left')
        if not is_freerun:
            time.sleep(moving_time)
            self.stop()

    def slew_up(self, moving_time=2, is_freerun=False):
        """Slew the mount to the up for a given time."""
        print(f"Slewing up for {moving_time} seconds...")
        self.slew_arrow_forever('up')
        if not is_freerun:
            time.sleep(moving_time)
            self.stop()
    
    def slew_down(self, moving_time=2, is_freerun=True):
        """Slew the mount to the down for a given time."""
        print(f"Slewing down for {moving_time} seconds...")
        self.slew_arrow_forever('down')
        if not is_freerun:
            time.sleep(moving_time)
            self.stop()

    def slew_arrow_forever(self, direction: str):
        """method to move the mount in the supplied cardinal direction.
        Returns True when command is sent and response received, otherwise will
        return False.
        
        To stop the mount, use the stop() method.
        """
        if self.system_status.is_parked:
            print("Mount is parked. Unparking...")
            self.unpark()

        directions = {'up': "mn", 'right': 'me', 'down': 'ms', 'left': 'mw'}
        assert direction.lower() in directions
        move_command = ":" + directions[direction.lower()] + "#"
        self.scope.send(move_command)
        # if self.scope.recv() == '1':
        #     return True
        # return False
    
    def set_arrow_speed(self, speed: int):
        """Slew the mount in the specified direction at the given speed. The speed
        must be between 0 and 9. Returns True when command is sent and response received,
        otherwise will return False.
        
        To stop the mount, use the stop() method.
        """
        assert speed >= 0 and speed <= 9
        speed_command = ":SR" + str(speed) + "#"
        self.scope.send(speed_command)
        if self.scope.recv() == '1':
            return True
        
    def set_alt_limit(self, alt_limit):
        """Set the altitude limit of the mount. Returns True after command is sent."""
        alt_limit_str = f"{int(alt_limit):02d}"
        command = f":SAL{alt_limit_str}#"
        self.scope.send(command)
        return self.scope.recv() == '1'
    
    def goto_zero_position(self):
        """Go to the zero position (home position)."""
        command = ":MH#"
        response = self.scope.send(command)
        self.print_received(command, response)
        return response == "1"
    
    def park(self):
        """Park the mount at the most recently defined parking position."""
        self.scope.send(":MP1#")
        response = self.scope.recv()
        self.system_status.is_parked = response == "1"
        return response == "1"

    def unpark(self):
        """Unpark the mount from its parking position."""
        command = ":MP0#"
        response = self.scope.send(command)
        self.print_received(command, response)
        self.system_status.is_parked = response == "1"
        return response == "1"

    def get_park_position(self):
        """Get the current parking position of the mount. """
        self.scope.send(':GPC#')
        returned_data = self.scope.recv()
        alt, az = utils.parse_alt_az("+"+returned_data)
        self.altitude_park = self.offset_alt(alt)
        self.azimuth_park = self.offset_az(az)
        print("Park position:")
        print(f'Altitude: {self.altitude_park:0.5f} deg, Azimuth: {self.azimuth_park:0.5f} deg')
    
    def print_park_position(self):
        """Print the current parking position of the mount. """
        self.get_park_position()
        print(f'Altitude: {self.altitude} deg, Azimuth: {self.azimuth} deg')
    
    def set_hemisphere(self, direction: str):
        """Set the mount's hemisphere. Supplied argument must be 'north', 'south', or
        'n' or 's'. Returns True after command is sent."""
        assert direction.lower() in ['north', 'south', 'n', 's']
        hemisphere = 0 if direction[0:1] == 's' else 1
        command = ":SHE" + str(hemisphere) + "#"
        self.scope.send(command)
        self.scope.recv()
        return True
    
    def stop(self):
        """Stop all slewing no matter the source of slewing or the direction(s)."""
        self.scope.send(':Q#')

    def stop_updown(self):
        """Stop the mount from moving up or down."""
        self.scope.send(':qD#')
        response = self.scope.recv()
        return response == "1"
    
    def stop_leftright(self):
        """Stop the mount from moving left or right."""
        self.scope.send(':qR#')
        response = self.scope.recv()
        return response == "1"

    def print_received(self, command, response):
        print(f"Command {command} accepted {bool(response)}")

    def get_current_alt_az(self):
        """Get the current altitude and azimuth from the mount."""
        self.scope.send(":GAC#")
        response = self.scope.recv()
        # print(f"Raw response: {response}")  # Print the raw response
        pos = utils.parse_alt_az(response)
        self.altitude_deg = self.offset_alt(pos[0]) 
        self.azimuth_deg =self.offset_az(pos[1])
        print(f"Alt, Az [deg]: {self.altitude_deg:0.5f}, {self.azimuth_deg:0.5f}")

    def get_current_ra_dec(self):
        """Get the current RA and DEC from the mount."""
        self.scope.send(":GEP#")
        response = self.scope.recv()
        # print(f"Raw response: {response}")  # Print the raw response
        pos = utils.parse_alt_az(response)
        self.dec_deg = self.offset_alt(pos[0]) 
        self.ra_deg =self.offset_az(pos[1])
        print(f"Ra, Dec [deg]: {self.ra_deg:0.5f}, {self.dec_deg:0.5f}")

    def get_mount_version(self):
        """Get the mount version."""
        self.scope.send(':MountInfo#')
        response = self.scope.recv()
        print(f"Mount version: {response}")
        return response
    
    # def switch_to_altaz_mode(self, north_pole=90):
    #     """Switch the mount to AltAz mode. 
        
    #     The latitude is se to 90deg (i.e. the North Pole) by default.
    #     """
    #     latitude_str = f"{int( (north_pole-90) * 360000):08d}"
    #     longitude_str = f"{int((118.79722) * 360000):08d}"
    #     self.scope.send(f":SLA+{latitude_str}#")
    #     response = self.scope.recv()
    #     self.print_received(f":SLA+{latitude_str}#", response)

    #     # set longitude
    #     self.scope.send(f":SLO+{longitude_str}#")
    #     response = self.scope.recv()
    #     self.print_received(f":SLO+{longitude_str}#", response)
    #     return response == "1"
    
    def set_lat_long(self, lat, long):
        """Set the latitude and longitude of the mount.
        
        Args:
            lat (float): latitude in degrees (range: -90 to 90)
            long (float): longitude in degrees (range: -180 to 180)

        """
        sign = '+' if lat >= 0 else '-'
        latitude_str = f"{sign}{int( abs(lat) * 360000):08d}"

        sign = '+' if long >= 0 else '-'
        longitude_str = f"{sign}{int( abs(long) * 360000):08d}"
        self.scope.send(f":SLA{latitude_str}#")
        response = self.scope.recv()
        self.print_received(f":SLA{latitude_str}#", response)

        # set longitude
        self.scope.send(f":SLO{longitude_str}#")
        response = self.scope.recv()
        self.print_received(f":SLO{longitude_str}#", response)
        return response == "1"
    
    def set_zero_position(self):
        """This command will set current position as zero position."""
        self.scope.send(":SZP#")
        response = self.scope.recv()
        return response == "1"
    
    def set_park_position(self, alt=90, az=0):
        """Set the parking position of the mount."""
        alt_str = f"{int(self.offset_alt(alt) * 360000):08d}"
        az_str = f"{int(self.offset_az(az) * 360000):08d}"

        # set azimuth
        self.scope.send(f":SPA+{az_str}#")
        response = self.scope.recv()
        self.print_received(f":SPA+{az_str}#", response)

        # set altitude 
        self.scope.send(f":SPH+{alt_str}#")
        response = self.scope.recv()
        self.print_received(f":SPH+{alt_str}#", response)

        return response == "1"
    
    def set_time(self):
        """Set the current time on the moint to the current computer's time. Sets to UTC."""
        j2k_time = str(utils.get_utc_time_in_j2k()).zfill(13)
        time_command = ":SUT" + j2k_time + "#"
        self.scope.send(time_command)

    def set_max_speed(self):
        """Set the mount to the maximum speed."""
        self.set_arrow_speed(9)
        # self.scope.send(":MSR#")
        # response = self.scope.recv()
        # return response == "1"

    def set_current_time(self):
        """Set the current UTC time on the mount."""
        current_time = Time.now()
        
        # Convert current UTC time to JD since J2000
        jd_value = current_time.jd
        jd_j2000 = jd_value - 2451545.0  # J2000 is 2451545.0
        utc_millis = int(jd_j2000 * 8.64e7)  # Convert to milliseconds
        # Send the time to the mount
        self.scope.send(f":SUT{utc_millis:013d}#")

    def set_timezone_offset(self, offset = utils.get_utc_offset_min()):
        """Sets the time zone offset on the mount to the computer's TZ offset."""
        tz_offset = str(offset).zfill(3)
        tz_command = ":SG" + tz_offset + "#" if offset < 0 else ":SG+" + tz_offset + "#"
        self.scope.send(tz_command)
        # Get the response; do nothing with it
        self.scope.recv()

    def get_time_information(self):
        """Get all time information from the mount."""
        self.scope.send(':GUT#')
        response_data = self.scope.recv()
        if response_data[0] == '1':
            self.scope.send(':GUT#')
            response_data = self.scope.recv()

        # Extract UTC offset, DST, and the time value
        utc_offset_minutes = int(response_data[0:4])
        self.time.utc_offset = utc_offset_minutes / 60.0  # Convert minutes to hours
        self.time.dst = response_data[4:5] == '1'

        if self.time.dst:
            self.time.utc_offset += 1
        
        # Extract and convert the time value
        utc_millis = int(response_data[5:18])
        jd_value = utc_millis / 8.64e7 + 2451545.0  # Convert to JD by reversing the formula
        self.time.julian_date = Time(jd_value, format='jd')
        
        self.time.unix_utc = self.time.julian_date.unix
        
        # Calculate local time using the UTC offset
        self.time.local_time = self.time.julian_date + TimeDelta(self.time.utc_offset * 3600, format='sec')
        self.time.formatted = self.time.local_time.iso
        print(self.time)

    def check_connection(self):
        """Check if the mount is connected."""
        self.scope.send(':GLS#')
        response = self.scope.recv()
        return len(response) > 0
    
    def _continous_altaz_reading(self,i):
        """Continously read the altitude and azimuth."""
        self.scope.send(":GAC#")
        response, timestamp = self.scope.recv_timestamp()
        pos = utils.parse_alt_az(response)
        self.altaz['alt'][i] = self.offset_alt(pos[0])
        self.altaz['az'][i] = self.offset_az(pos[1])
        self.altaz['time'][i] = timestamp

    def continous_altaz_reading(self, timeout, interval=0.1, verbose=True):
        """Continously read the altitude and azimuth."""
        nsamples = int(timeout / interval)

        alt_vec = np.zeros(nsamples)
        az_vec = np.zeros(nsamples)
        t_vec = np.full(nsamples, np.datetime64('1970-01-01T00:00:00', 'ns'), dtype='datetime64[ns]')
        self.altaz = {'alt': alt_vec, 'az':az_vec, 'time':t_vec}
        for i in range(nsamples):
            self._continous_altaz_reading(i)
            if verbose:
                alt, az = self.altaz['alt'][i], self.altaz['az'][i]
                print(f"Altitude: {alt:0.5f}, Azimuth: {az:0.5f}")
            time.sleep(interval)
    
    def offset_alt(self, alt):
        return (alt - self.OFFSET_ALT) #% 90
    
    def offset_az(self, az):
        return (az - self.OFFSET_AZ) % 360
    
    def is_slewing(self):
        """Check if the mount is slewing."""
        time.sleep(1)
        self.get_system_state(verbose=False)
        return self.system_status.is_sleewing
    
    

@dataclass
class SystemStatus:
    code: str = ''
    description: str = ''
    is_sleewing: bool = False
    is_tracking: bool = False
    is_parked: bool = False

    status_actions =  {
            '0': {"description": "stopped at non-zero position", "is_sleewing": False, "is_tracking": False},
            '1': {"description": "tracking with periodic error correction disabled", "is_sleewing": False, "is_tracking": True, "pec_enabled": False},
            '2': {"description": "slewing", "is_sleewing": True, "is_tracking": False},
            '3': {"description": "auto-guiding", "is_sleewing": False, "is_tracking": True},
            '4': {"description": "meridian flipping", "is_sleewing": True},
            '5': {"description": "tracking with periodic error correction enabled", "is_sleewing": False, "is_tracking": True, "pec_enabled": True},
            '6': {"description": "parked", "is_sleewing": False, "is_tracking": False, "is_parked": True},
            '7': {"description": "stopped at zero position (home position)", "is_sleewing": False, "is_tracking": False},
        }
    
    def __str__(self):
        return (f"SystemStatus: {self.code}\n"
                f"  Description: {self.description}\n"
                f"  Is Sleewing: {self.is_sleewing}\n"
                f"  Is Tracking: {self.is_tracking}\n"
                f"  Is Parked: {self.is_parked}\n")
        
    def update_status(self, status_code):
        action = self.status_actions.get(status_code, {})
        self.code = status_code
        self.description = action.get("description", "Unknown status")
        self.is_sleewing = action.get("is_sleewing", False)
        self.is_tracking = action.get("is_tracking", False)
        self.is_parked = action.get("is_parked", False)

@dataclass
class TimeInfo:
    """Time related information."""
    utc_offset: int = None
    dst: bool = None
    julian_date: int = None
    unix_utc: float = None
    unix_offset: float = None
    formatted: str = None
    local_time: float = None

    def __str__(self) -> str:
        return (
            '------ Time Information ------\n'
            f"UTC Offset: {self.utc_offset}\n"
            f"DST: {self.dst}\n"
            f"Julian Date: {self.julian_date}\n"
            f"Unix UTC: {self.unix_utc}\n"
            f"Local Time: {self.formatted}\n"
            '-------------------------------'
        )

if __name__ == "__main__":
    # Example usage:
    is_park = False

    # Initialize the mount
    mount = IoptronMount(port='/dev/ttyUSB0')

    # Get the system state
    mount.get_system_state(verbose=False)

    # Park and Unpark
    if is_park:
        print("Parking the mount...")
        parked = mount.park()
        mount.get_system_state(verbose=True)

        print("Waiting for the mount to park...")
        while not mount.system_status.is_parked:
            time.sleep(1)
            mount.get_system_state(verbose=False)
        print("Mount is parked.")
    else:
        unparked = mount.unpark()

    mount.get_system_state(verbose=False)
    print(f"Mount park state: {mount.system_status.is_parked}")

    # print the current alt,az
    print("-------------------------------")
    print("Current Cordinates:")
    mount.get_current_alt_az()
    
    # Slew to Alt, Az
    mount.slew_to_alt_az(30, 0)
    mount.get_system_state(verbose=False)

    print("Waiting mount to slew...")
    while mount.system_status.is_sleewing:
        time.sleep(5)
        mount.get_system_state(verbose=False)
        print(f"elapsed time: {round(mount.last_update - mount.last_slew, 2)} sec")

    print("Mount is done slewing.")
    print("Mount moved to:")
    mount.get_current_alt_az()
    print("-------------------------------")

    # Slew to a direction for 2 seconds
    mount.set_arrow_speed(9)
    print("---- Start a series of slews...")
    # move to the right
    mount.slew_right()
    # move to the left
    mount.slew_left()
    # move up
    mount.slew_up()
    # move down
    mount.slew_down()
    print("-------------------------------")

    # print time information
    mount.get_time_information()
