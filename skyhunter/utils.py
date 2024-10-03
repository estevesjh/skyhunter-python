"""
    Parse the response from the iOptron telescope mount.
    
    Example alt az response

    Command: “:GAC#”
    Response: “sTTTTTTTTTTTTTTTTT#”

    This command gets altitude and azimuth, the response includes a sign and 17 digits.
    The sign and first 8 digits indicate current altitude. Valid data range is [-32,400,000, +32,400,000].
    Note: The resolution is 0.01 arc-second.
    The last 9 digits indicate current azimuth. Valid data range is [0, 129,600,000]. Note: The resolution
    is 0.01 arc-second.
"""
import numpy as np

def parse_alt_az(response, is_latlong=False):
    """Parse the altitude and azimuth from the iOptron response.

    Args:
        response (str): command response from the iOptron telescope mount

    Returns:
        alt (float): the altitude in degree
        az (float): the azimuth in degree
    """
    if len(response) > 19:
        comp = int(len(response) - 19)
        response = response[comp:]

    # Extract altitude and azimuth parts
    sign = response[0]
    altitude_str = response[1:9]
    azimuth_str = response[9:18]
    if is_latlong:
        azimuth_str = response[9:17]

    # Convert to integers
    altitude = int(altitude_str) * (1 if sign == '+' else -1)
    azimuth = int(azimuth_str)

    # Convert to degrees
    altitude_deg = altitude / 360000.0
    azimuth_deg = azimuth / 360000.0
    azimuth_deg = np.where(azimuth_deg > 360, azimuth_deg - 360, azimuth_deg)

    return np.round(altitude_deg,5), np.round(azimuth_deg,5)

def angular_difference(target_angle, current_angle):
    diff = (target_angle - current_angle + 180) % 360 - 180
    return diff
# # Example usage:
# response = "+01234567012345678#"
# altitude, azimuth = parse_ioptron_response(response)
# print(f"Altitude: {altitude} degrees, Azimuth: {azimuth} degrees")

""" 
Time Information helper functions
"""
from datetime import datetime, timedelta
import time

def get_utc_offset_min():
    """Get the UTC offset of this computer in minutes."""
    offset = int(time.timezone/60)
    # TODO: Figure out why Python uses the oppposite sign I'd expect
    # I am in PST and the number is positive; it's negative ahead of UTC. /shrug
    return offset * -1


def convert_j2k_to_unix_utc(sec, offset = 0):
    """Convert J2000 in 0.01 seconds to formatted UNIX in ms with offset if needed."""
    converted = datetime(2000,1,1,12,0) + timedelta(milliseconds=sec) + timedelta(minutes=offset)
    return time.mktime(converted.timetuple())


def convert_unix_to_formatted(unix_ms):
    """Convert a unix timestamp to HH:MM:SS.ss."""
    return datetime.utcfromtimestamp(int(unix_ms)).strftime("%m/%d/%Y, %H:%M:%S.%f")[:-3]


def get_utc_time_in_j2k():
    """Get the UTC time expressed in J2000 format (seconds since 12 on 1/1/2000.)"""
    j2k_time = datetime(2000, 1, 1, 12, 00)
    utc = datetime.utcnow()
    difference = utc - j2k_time
    return(int(difference.total_seconds() * 1000))

def offset_utc_time(unix, offset):
    """Convert utc time into a time with the supplied timezone offset."""
    offset_sec = timedelta(minutes=abs(int(offset))).seconds
    if offset < 1:
        return unix - offset_sec
    if offset > 0:
        return unix + offset_sec
    if offset == 0:
        return unix + 0 # No changes