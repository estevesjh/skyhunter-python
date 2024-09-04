"""
Module for interfacing and communicating with stuff over serial.
@author - James Malone
"""

import logging
import sys
import time
import numpy as np
import serial
import serial.tools.list_ports

class USBSerial:
    """Class for communicating with devices over serial."""
    def __init__(self, port = 'COM5', baud = 115200, log_level = logging.INFO):
        self.send_wait = 0.20 # Arbritrary waiting period to save flooding comms
        logging.basicConfig(filename='iotty.log', format='%(asctime)s - %(message)s',\
            level=log_level)
            
        try:
            self.ser = serial.Serial(port, baud)
        except:
            logging.critical("Could not open port '%s'", port)
            # list all available ports
            ports = serial.tools.list_ports.comports()
            print(f"Connection failed, the port {port} is not available")
            print("Available ports in the system:")
            for port in ports:
                print(f"Device: {port.device}, Description: {port.description}")
            sys.exit(1)

    def open(self):
        """Open the serial connection."""
        self.ser.isOpen()
        logging.debug("Opened serial port successfully")

    def send(self, data):
        """Send data over the serial connection."""
        bytes_to_send = data.encode('utf-8')
        logging.debug("Sending -> %s", str(data))
        self.ser.write(bytes_to_send)
        time.sleep(self.send_wait)

    def recv(self):
        """Receive the output."""
        output = ''
        while self.ser.inWaiting() > 0:
            output += self.ser.read(1).decode('utf-8')
        logging.debug("Received <- %s", str(output))
        return output
    
    def recv_timestamp(self):
        """Receive the output with a timestamp."""
        output = ''
        while self.ser.inWaiting() > 0:
            output += self.ser.read(1).decode('utf-8')
            timestamp = time.time()
        logging.debug("Received <- %s", str(output))
        return output, np.datetime64(int(timestamp * 1e9), 'ns')

    def close(self):
        """Close the connection."""
        self.ser.close()
        logging.debug("Closed serial port successfully")
