import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging

class TwilightMonitorDatabase:
    def __init__(self, day=None, month=None, year=None, path="/home/estevesjh/Documents/github/",
                 electrometer_path="/home/estevesjh/Documents/twilightMonitor/DATA/keysighB2987A",
                 mount_path='/home/estevesjh/Documents/twilightMonitor/DATA/mount/'):
        self.year = year if year is not None else datetime.now().year
        self.month = month if month is not None else datetime.now().month
        self.day = day if day is not None else datetime.now().day
        self.date_str = f"{self.year}{self.month:02d}{self.day:02d}"
        
        # Initialize logging
        logging.basicConfig(filename=add_path(path,'twmdb_log.txt'), level=logging.INFO)
        logging.info(f"Initializing TwilightMonitorDatabase for {self.date_str}")

        # Initialize paths
        self.init_paths(path, electrometer_path, mount_path)
        
        # Initialize or load database
        self.load_database()

        # count the exposures
        self.seq_id_last = self.database['seq_id'].max() if not self.database.empty else 0

    def load_database(self):
        if not os.path.exists(self.file_path):
            self.database = pd.DataFrame(columns=[
                'tmid', 'date', 'seq_id', 'exp_time_cmd', 'exp_time', 
                'filter', 'Alt', 'Az', 'current_mean', 'current_std', 
                'alt_std', 'az_std', 'alt_rank', 'az_rank', 'electrometer_filename', 'flag'
            ])
            self.database.to_csv(self.file_path, index=False)
            self.set_seq_id(0)
            logging.info(f"Created new database for {self.date_str}")
        else:
            self.database = pd.read_csv(self.file_path)
            if os.path.exists(self.seq_id_file):
                self.set_seq_id(int(self.database['seq_id'].max()))
            else:
                self.set_seq_id(self.database['seq_id'].max() + 1 if not self.database.empty else 0)
            logging.info(f"Loaded existing database for {self.date_str}")

    def init_paths(self, path, electrometer_path, mount_path):
        # Define paths
        # self.root = add_path(path, "twmdb-python")
        self.data = add_path(path, "DATA")
        self.folder_path = add_path(self.data, f"{self.year}{self.month:02d}")
        self.file_path = add_path(self.folder_path, f"{self.year}{self.month:02d}{self.day:02d}.csv")
        self.tmp_folder = add_path(self.folder_path, "tmp")
        self.seq_id_file = add_path(self.tmp_folder, "seq_id_{:04d}.csv")

        # Define paths for electrometer
        self.electrometer_path = electrometer_path
        self.electrometer_folder = add_path(self.electrometer_path, f"{self.year}{self.month:02d}")
        self.electrometer_str = add_path(self.electrometer_folder, "%s_{seq_id}.npy" % (self.date_str))

        # Define paths for mount
        self.mount_path = mount_path
        self.mount_folder = add_path(self.mount_path, f"{self.year}{self.month:02d}")
        self.mount_str = add_path(self.mount_folder, "mount_pointing_%s_{seq_id}" % (self.date_str))

        # Create necessary directories
        os.makedirs(self.tmp_folder, exist_ok=True)
        os.makedirs(self.electrometer_folder, exist_ok=True)
        os.makedirs(self.mount_folder, exist_ok=True)
        logging.info(f"Initialized paths for: {self.folder_path}, {self.tmp_folder}")
        logging.info(f"Initialized paths for electrometer path: {self.electrometer_folder}")
        logging.info(f"Initialized paths for mount path: {self.mount_folder}")

    def add_exposure(self, timestamp, alt, az, exp_time_cmd=0, exp_time=0, 
                     filter_type='Empty', current_mean=np.nan, current_std=np.nan, 
                     alt_std=np.nan, az_std=np.nan, alt_rank=-99, az_rank=-99, electrometer_filename=None, flag=False):
        
        self.set_seq_id(self.seq_id_last + 1)
        tmid = timestamp.strftime('%Y%m%d%H%M%S')
        if electrometer_filename is None:
            electrometer_filename = self.electrometer_str.format(seq_id=self.seq_id)

        new_exposure = pd.DataFrame([{
            'tmid': tmid,
            'date': timestamp,
            'seq_id': self.seq_id,
            'exp_time_cmd': exp_time_cmd,
            'exp_time': exp_time,
            'filter': filter_type,
            'Alt': alt,
            'Az': az,
            'current_mean': current_mean,
            'current_std': current_std,
            'alt_std': alt_std,
            'az_std': az_std,
            'alt_rank': int(alt_rank),
            'az_rank': int(az_rank),
            'electrometer_filename': electrometer_filename,
            'mount_filename': self.mount_str.format(seq_id=self.seq_id),
            'flag': flag
        }])
        self.database = pd.concat([self.database, new_exposure], ignore_index=True)
        self.save_exposure(self.seq_id)
        self.seq_id_last += 1
        logging.info(f"Added exposure {self.seq_id} at {timestamp}")

    def update_exposure(self, seq_id, **kwargs):
        if seq_id in self.database['seq_id'].values:
            for key, value in kwargs.items():
                if key in self.database.columns:
                    self.database.loc[self.database['seq_id'] == seq_id, key] = value
                    logging.info(f"Updated {key} for seq_id {seq_id} to {value}")
            self.save_exposure(seq_id)
        else:
            logging.warning(f"seq_id {seq_id} not found in the database.")
            raise ValueError(f"seq_id {seq_id} not found in the database.")

    def set_seq_id(self, seq_id):
        self.seq_id = int(seq_id)
        self.seq_id_str = f"{self.seq_id:04d}"
        self.exposure = self.database.loc[self.database.seq_id == self.seq_id]

    def save_exposure(self, seq_id):
        self.set_seq_id(seq_id)
        self.exposure.to_csv(self.seq_id_file.format(self.seq_id), index=False, header=True)
        logging.debug(f"Saved tmp exposure {self.seq_id} to {self.seq_id_file.format(self.seq_id)}")

    def save_electrometer_file(self, data, seq_id=None):
        if seq_id is None: seq_id = self.seq_id
        self.exposure_electrometer_file = self.electrometer_str.format(seq_id=seq_id)
        np.save(self.exposure_electrometer_file, data)
        logging.info(f"Saved electrometer file for seq_id {self.seq_id} to {self.exposure_electrometer_file}")

    def save_mount_file(self, dict, seq_id=None):
        if seq_id is None: seq_id = self.seq_id
        self.exposure_mount_file = self.mount_str.format(seq_id=seq_id)
        np.savez(self.exposure_mount_file, **dict)
        logging.info(f"Saved mount file for seq_id {self.seq_id} to {self.exposure_mount_file}")

    def save(self):
        self.exposure.to_csv(self.seq_id_file.format(self.seq_id), index=False, header=True)
        self.database.to_csv(self.file_path, index=False)
        logging.info(f"Database saved for {self.date_str}")

    def close(self):
        self.save()
        self.database = None
        logging.info(f"Closing database for {self.date_str}")
        # destroy the self object
        del self
        

def add_path(path1, path2):
    return os.path.join(path1, path2)

# Example usage
if __name__ == "__main__":
    # Example of adding a new exposure
    db = TwilightMonitorDatabase(21, 8, 2024)
    db.add_exposure(
        timestamp=datetime.utcnow(),
        alt=45.0,
        az=90.0,
        alt_std=0.3,
        az_std=0.3,
        exp_time_cmd=30,
        filter_type='SDSSr'
    )
    # The sequennce ID is automatically updated
    print(f"A new exposured added to the database, the seq_id is {db.seq_id}")
    
    # Example of updating an exposure, save as tmp file
    db.update_exposure(seq_id=db.seq_id, current_mean=0.1, current_std=0.1)
    print(f"Updated exposure {db.seq_id} with current_mean=0.1 and current_std=0.1")

    # Save the updated exposure to the database
    print("Saving the updated exposure to the database")
    db.close()

    # Uploading the database
    print("Uploading the database")
    db2 = TwilightMonitorDatabase(21, 8, 2024)
    db2.add_exposure(
        timestamp=datetime.utcnow(),
        alt=45.0,
        az=90.0,
        exp_time_cmd=30,
        filter_type='SDSSr'
    )
    print(f"A new exposured added to the database, the seq_id is {db.seq_id}")
    # once you get the electrometer file
    db2.save_electrometer_file(data, db.seq_id)

    # Save the database
    print("Saving the updated exposure to the database")
    db2.save()