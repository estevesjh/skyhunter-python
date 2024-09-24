# import telnetlib
import pyvisa as visa
import struct
import time
import numpy as np

"""Command Keysight Electrometer (B2983B)

This module is used to control the Keysight Electrometer B2983B. 
The connection is trough USB Type B. 
To find `electrometer_id` you can use the command `Config().rm.list_resources()` 


In case you need to install pyvisa
>> pip install zeroconf
>> pip install pyvisa-py

This code was originally written to work with telnetlib, but it was modified to work with pyvisa

Date: Aug 13, 2024
Autor: Elana Urbarch
Modiefied by: Johnny Esteves
"""

class Config():
    def __init__(self) -> None:
        # initialize the resource manager (USB connection)
        self.rm = visa.ResourceManager()
    pass

class Keysight():
    """
    A class to interface with the Keysight Electrometer B2983B via USB.

    Attributes:
        electrometer_id (str): The resource identifier for the electrometer.
        keysight_addr (str): The IP address for remote connections (if applicable).
        keysight_port (int): The port number for remote connections (if applicable).

    Methods:
        _config(): Configures the VISA resource manager and connects to the electrometer.
        find_instrument(): Finds the instrument.
        on(): Turns the instrument input ON.
        off(): Turns the instrument input OFF.
        acquire(): Starts the data acquisition process.
        read_data(): Reads the acquired data in ASCII format.
        reset(): Resets the instrument's settings.
        set_trigger_out(): Sets up the trigger output configuration.
        set_mode(mode): Set the measurement mode of the electrometer.
        set_rang(charge_range): Set the measurement range for the selected mode.
        set_nplc(nplc): Set the number of power line cycles (NPLC) for measurement integration time.
        set_nsamples(nsamples): Set the number of samples to be acquired during a measurement.
        set_delay(delay): Set the delay time before starting the measurement.
        set_interval(interval): Set the time interval between consecutive samples.
        get_params(): Get the current state parameters by calling each get function and storing the output in a dictionary.
        set_acquisition_time(time): Set the acquisition time for the measurement.
        get_power(): Get the power reading from the instrument.
        get_mode(): Get the current mode of the instrument.
        get_aper(): Get the aperture setting of the instrument.
        get_nplc(): Get the number of power line cycles (NPLC) setting.
        get_rang(): Get the range setting of the instrument.
        get_delay(): Get the delay setting of the instrument.
        get_interval(): Get the interval setting between consecutive samples.
        get_nsamples(): Get the number of samples setting.
        get_powerline_freq(): Get the power line frequency setting.
        get_default_params(): Get the current default configuration parameters.
        explain_params(): Print an explanation of each parameter.
        sync_tracked_properties(): Synchronizes the instrument's settings with the expected parameters.

    """
    # tracked_properties = ["mode", 'rang', 'nplc', 'nsamples', 'interval', 'delay']

    def __init__(self, electrometer_id='USB0::2391::54808::MY54321262::0::INSTR'):
        """
        Initializes the Keysight object with the specified resource identifiers.

        Args:
            electrometer_id (str): The resource identifier for the electrometer.
        """
        self.config = Config()
        self.config.electrometer_id = electrometer_id
        self.default_params = {
                        "mode": 'CHAR',
                        'rang': 'AUTO',
                        'nplc': 0.1,
                        'nsamples': 10,
                        'delay': 0,
                        'interval': 2e-3,
                        # 'aper': 'AUTO',  # Uncomment if aperture is used
                    }
        self.tracked_properties = list(self.default_params.keys())
        self.params = self.default_params.copy()
        self.client = None

        # # check instrument connection
        # try:
        #     self.get_params()
        # except:
        #     print('Could not connect to the electrometer. Please check the instrument id.')
        #     self.find_instrument()

    def _config(self):
        """Configures the VISA resource manager and connects to the electrometer."""
        if self.client is not None:
            self.client.close()
        
        self.client = self.config.rm.open_resource(self.config.electrometer_id)
        self.client.timeout = 100000  # Timeout in milliseconds (e.g., 5000 ms = 5 seconds)

        # remote connections
        # self.client = telnetlib.Telnet(self.config.keysight_addr, self.config.keysight_port)
    
    def find_instrument(self):
        """Finds the instrument."""
        print("Available USB resources:")
        print(self.config.rm.list_resources())
        self.config.electrometer_id = input("Enter the resource identifier for the electrometer: ")

    def sync_tracked_properties(self):
        """
        Synchronizes the instrument's settings with the expected parameters.
        """
        # print('Setting defult parameters')
        for p in self.tracked_properties:
            # print(f'Set {p} to {self.default_params[p]}')
            getattr(self, f'set_{p}')(self.default_params[p])
    
    def query(self, command):
        """Send a command to the instrument and return the response."""
        self._config()
        try:
            response = self.client.query(command)
            return response.strip().strip('"') 
        except visa.errors.VisaIOError as e:
            print(f"Query failed: {e}")
            return None
        finally:
            self.client.close()
            time.sleep(0.1)

    def write(self, message):
        #self.client = telnetlib.Telnet(self.config.keysight_addr, self.config.keysight_port)
        self._config()
        try:
            self.client.write(message)
        except EOFError:
            self._config()
            self.client.write(message)
        self.client.close()
        time.sleep(0.1)
    
    def read(self, message):
        self.client.write(message + '\r\n')

        self._config()
        try:
            return self.client.read().strip()  # Use read() for string data
        except visa.VisaIOError as e:  # Handle errors specific to pyvisa
            self._config()
            return self.client.read().strip()
        finally:
            self.client.close()
            time.sleep(0.1)
    
    def read_binary_data(self, message):
        self._config()
        self.client.write(message + '\r\n')
        try:
            return self.client.read_raw()  # Use read_raw() for binary data
        except visa.VisaIOError as e:  # Handle errors specific to pyvisa
            self._config()
            return self.client.read_raw()
        finally:
            self.client.close()
            time.sleep(0.1)

    # README: This function was designed to work with telnetlib
    # The function read_until() is not available in pyvisa
    # def read(self, message):
    #     # self.client = telnetlib.Telnet(self.config.keysight_addr, self.config.keysight_port)
    #     self._config()
    #     self.client.write((message+'\r\n').encode())
    #     try:
    #         return self.client.read_until(b'\n', timeout=10)
    #     except EOFError:
    #         self._config()
    #         return self.client.read_until(b'\n', timeout=10)
    #     self.client.close()
    #     time.sleep(0.1)
        
    def on(self):
        """Turns the instrument input ON."""
        self.write(':INP ON')

    def off(self):
        """Turns the instrument input OFF."""
        self.write(':INP OFF')

    def acquire(self):
        """Starts the data acquisition process."""
        # print("Get frequency")
        freq = 50 # Hz # to be checked #self.get_powerline_freq()
        # print("Get acquisition time")
        self.t_acq = float(self.params['nsamples']) * (float(self.params['nplc'])*1/freq + float(self.params['interval']))/2
        print('acquisition time:', self.t_acq)

        self.write(':INIT:ACQ')

        # Use time.time() to track real-time progress
        start_time = time.time()
        
        # Wait for the acquisition to complete based on the calculated time
        while time.time() - start_time < self.t_acq:
            elapsed = time.time() - start_time
            print(f'Acquisition {elapsed:.2f}/{self.t_acq:.2f} s', end='\r')
            time.sleep(0.005)  # Sleep for 10 ms to avoid overwhelming the system

        print('\nAcquisition finished')

    def read_binary_data(self):
        d = self.read_binary_data(f':FORM:DATA REAL,32')
        n = struct.unpack('>I', d[:4])
        data = struct.unpack(f'>{n}f', d[4:-1])
        self.write(f':FORM:DATA ASC')
        return data

    def read_data(self):
        """
        Reads the acquired data in ASCII format.

        Returns:
            np.recarray: A record array containing time and measurement data.
        """
        print('Reading the data')
        self._config()
        t = self.client.query_ascii_values(':FETC:ARR:TIME?')
        t = np.array(t, dtype=float)
        d = self.client.query_ascii_values(f':FETC:ARR:{self.params["mode"]}?')
        d = np.array(d, dtype=float)
        return np.rec.fromarrays([t, d], names=['time', self.params["mode"]])

    def reset(self):
        """Resets the charge."""
        self.write('SENS:CHAR:DISCharge')

    def set_trigger_out(self):
        """Sets up the trigger output configuration."""
        self.write('TRIG:ACQ:TOUT 1')
        self.write('TRIG:ACQ:TOUT:SIGN TOUT')

    def set_mode(self, mode):
        """Set the measurement mode of the electrometer.
        
        Args:
            mode (str): Measurement mode. One of ['CURR', 'CHAR', 'VOLT', 'RES'].
        
        Raises:
            ValueError: If an invalid mode is provided.
        """
        if mode not in ['CURR', 'CHAR', 'VOLT', 'RES']:
            raise ValueError("Invalid mode. Choose from 'CURR', 'CHAR', 'VOLT', 'RES'.")
        self.params["mode"] = mode
        self.write(f'SENSe:FUNCtion:ON "{mode}"')

    def set_rang(self, charge_range):
        """
        Set the measurement range for the selected mode.
        
        value for current measurement : 2e-12 A to 20e-3 A
        value for charge measurement : 2e-9 C to 2e-6 

        Args:
            rang (str or float): The range in scientific notation (e.g., 'AUTO, 2e-6).
        """
        self.params['rang'] = charge_range
        
        if charge_range == 'AUTO' :
            self.write(f'SENS:{self.params["mode"]}:RANG:AUTO ON')
        else :
            charge_range = float(charge_range)
            self.write(f'SENS:{self.params["mode"]}:RANG:AUTO OFF')
            self.write(f'SENS:{self.params["mode"]}:RANG {charge_range}')
    
    def set_nplc(self, nplc):
        """
        Set the number of power line cycles (NPLC) for measurement integration time.
        
        Args:
            nplc (float): NPLC value, where lower values mean faster measurements with potentially higher noise.
        """
        self.params['nplc'] = nplc
        if nplc == 'AUTO' :
            self.write(f':SENS:{self.params["mode"]}:NPLC:AUTO ON')
        else:
            self.write(f':SENS:{self.params["mode"]}:NPLC:AUTO OFF')
            self.write(f':SENS:{self.params["mode"]}:NPLC {nplc}')
    
    def set_nsamples(self, nsamples=5500):
        """
        Set the number of samples to be acquired during a measurement.
        
        Args:
            nsamples (int): Number of samples.
        """
        nsamples = int(nsamples)
        self.params['nsamples'] = nsamples
        self.write(f':TRIG:ACQ:COUN {nsamples}')
        self.params['nsamples'] = nsamples
    
    def set_delay(self, delay):
        """
        Set the delay time before starting the measurement.
        
        Args:
            delay (float): Delay time in seconds.
        """
        delay_time = float(delay)
        self.write(f':TRIG:ACQ:DEL {str(delay_time)}')
        self.write(f':TRIG:SOUR TIM')
        self.params['delay'] = delay
    
    def set_interval(self, interval):
        """
        Set the time interval between consecutive samples.
        
        Args:
            interval (float): Interval time in seconds (e.g., 2e-3 for 2 milliseconds).
        """
        interval = float(interval)
        self.write(f':TRIG:ACQ:TIM {interval}')
        self.params['interval'] = interval

    def get_params(self):
        """
        Get the current state parameters by calling each get function and storing the output in a dictionary.

        Returns:
            dict: A dictionary containing the current state parameters.
        """
        self.params = {
            'power': self.get_power(),
            "mode": self.get_mode(),
            'aper': self.get_aper(),
            'nplc': self.get_nplc(),
            'rang': self.get_rang(),
            'delay': self.get_delay(),
            'interval': self.get_interval(),
            'nsamples': self.get_nsamples()
        }
        print('\nCurrent instrument parameters:')
        for param, value in self.params.items():
            print(f"{param}: {value}")
        print("")

    def set_acquisition_time(self, time):
        """
        Set the acquisition time for the measurement.
        
        Args:
            time (float): Acquisition time in seconds.
        """
        nsamples = int(time / self.params['interval'])
        self.set_nsamples(nsamples)
        print(f"Acquisition time set to {time} s for interval {self.params['interval']} s")

    def get_power(self):
        """
        Get the power reading from the instrument.

        Returns:
            str: The power reading.
        """
        return int(self.query(':INP?'))

    def get_mode(self):
        """
        Get the current mode of the instrument.

        Returns:
            str: The current mode.
        """
        return self.query(f'SENS:FUNC?')

    def get_aper(self):
        """
        Get the aperture setting of the instrument.

        Returns:
            str: The aperture setting.
        """
        return self.query(f'SENS:{self.params["mode"]}:APER?')

    def get_nplc(self):
        """
        Get the number of power line cycles (NPLC) setting.

        Returns:
            str: The NPLC setting.
        """
        return self.query(f'SENS:{self.params["mode"]}:NPLC?')

    def get_rang(self):
        """
        Get the range setting of the instrument.

        Returns:
            str: The range setting.
        """
        return self.query(f'SENS:{self.params["mode"]}:RANG?')

    def get_delay(self):
        """
        Get the delay setting of the instrument.

        Returns:
            str: The delay setting.
        """
        return self.query(f'TRIG:ACQ:DEL?')

    def get_interval(self):
        """
        Get the interval setting between consecutive samples.

        Returns:
            str: The interval setting.
        """
        return self.query(':TRIG:ACQ:TIM?')

    def get_nsamples(self):
        """
        Get the number of samples setting.

        Returns:
            int: The number of samples.
        """
        return int(self.query(':TRIG:ACQ:COUN?'))
    
    def get_powerline_freq(self):
        """
        Get the power line frequency setting.

        Returns:
            float: The power line frequency.
        """
        return float(self.query(':SYST:POWE:FREQ?'))
    
    def get_default_params(self):
        """
        Get the current default configuration parameters.

        Returns:
            dict: Current configuration parameters.
        """
        return self.params
    
    def explain_params(self):
        """
        Print an explanation of each parameter.
        """
        explanations = {
            "mode": "Measurement mode. Options are 'CURR' (current), 'CHAR' (charge), 'VOLT' (voltage), and 'RES' (resistance).",
            'rang': "Measurement range for the selected mode (e.g., '2e-6' for 2 microamps in current mode).",
            'nplc': "Number of Power Line Cycles (NPLC). Determines integration time. Lower values are faster but noisier.",
            'nsamples': "Number of samples to acquire during measurement.",
            'delay': "Delay time in seconds before starting the measurement after a trigger.",
            'interval': "Time interval in seconds between consecutive samples (e.g., 2e-3 for 2 milliseconds).",
            # 'aper': "Aperture time for integration. 'AUTO' lets the instrument automatically adjust.",
        }
        
        for param, explanation in explanations.items():
            value = self.params.get(param)
            print(f"{param}: {value}\n    {explanation}\n")

    def start_measurement(self):
        """
        Start electrometer measurements.

        Returns:
            dict: A dictionary containing the electrometer data.
        """
        print("Enter Start Measurment")
        self.acquire()
        # wait for acquisition completion
        d = self.read_data()
        self.datavector = d
        # save the data
        self.keysight_data = {}
        self.keysight_data['mean'] = np.mean(d[self.params['mode']])
        self.keysight_data['std'] = np.std(d[self.params['mode']])
        self.keysight_data['teff'] = d['time'][-1]-d['time'][0]
        return self.keysight_data
    
if __name__=='__main__':
    k = Keysight()
    k.get_powerline_freq()
    # print each parameter and its explanation
    # k.explain_params()

    # find the instrument
    k.find_instrument()
    
    # get the power status
    k.get_power()

    # get the current configuration parameters
    k.get_params()

    #synchronize the instrument's settings with the default parameters
    k.sync_tracked_properties()
    # to see the current default parms k.get_default_params()

    # resets the charge
    k.reset()

    # acquire data
    k.acquire()

    res = k.read_data()
    np.save('data.npy', res)
    
