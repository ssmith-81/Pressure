# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@panodata.org>
# License: GNU Affero General Public License, Version 3
import asyncio
import h5py
import time

from calypso_anemometer.core import CalypsoDeviceApi, CalypsoDeviceDataRate


async def calypso_read(filename, datarate, log_duration=60):
    async with CalypsoDeviceApi() as calypso:
        
        # Set the desired data rate
        await calypso.set_datarate(datarate)

        # Open the HDF5 file for appending
        with h5py.File(filename, 'a') as f:
            # Create datasets if they don't already exist
            if 'timestamp' not in f:
                f.create_dataset('timestamp', (0,), maxshape=(None,), dtype='f8')  # float for timestamps
            if 'wind_speed' not in f:
                f.create_dataset('wind_speed', (0,), maxshape=(None,), dtype='f8')
            if 'wind_direction' not in f:
                f.create_dataset('wind_direction', (0,), maxshape=(None,), dtype='f4')
            if 'battery_level' not in f:
                f.create_dataset('battery_level', (0,), maxshape=(None,), dtype='f')
            if 'temperature' not in f:
                f.create_dataset('temperature', (0,), maxshape=(None,), dtype='f')
            if 'roll' not in f:
                f.create_dataset('roll', (0,), maxshape=(None,), dtype='f')
            if 'pitch' not in f:
                f.create_dataset('pitch', (0,), maxshape=(None,), dtype='f')
            if 'heading' not in f:
                f.create_dataset('heading', (0,), maxshape=(None,), dtype='f8')

            # Define the callback for logging each reading
            def log_reading(reading):
                # Resize datasets to accommodate new entries
                for key in ['timestamp', 'wind_speed', 'wind_direction', 'battery_level',
                            'temperature', 'roll', 'pitch', 'heading']:
                    f[key].resize((f[key].shape[0] + 1,))
                
                # Get the current timestamp and log the reading
                timestamp = time.time()
                f['timestamp'][-1] = timestamp
                f['wind_speed'][-1] = reading.wind_speed
                f['wind_direction'][-1] = reading.wind_direction
                f['battery_level'][-1] = reading.battery_level
                f['temperature'][-1] = reading.temperature
                f['roll'][-1] = reading.roll
                f['pitch'][-1] = reading.pitch
                f['heading'][-1] = reading.heading

                # Print the logged data for verification
                print(f"Logged at {timestamp}: {reading}")

            # Subscribe to wind sensor readings
            await calypso.subscribe_reading(log_reading)

            try:
                await asyncio.sleep(log_duration)  # Adjust the logging duration as needed
            finally:
                await calypso.unsubscribe_reading()
        #reading = await calypso.get_reading()
        #reading.dump()


if __name__ == "__main__":  # pragma: nocover
    filename = 'calypso_wind_data.h5'
    
    # Set the data rate (example: 1 Hz)
    data_rate = CalypsoDeviceDataRate.HZ_1 

    # class CalypsoDeviceDataRate(IntEnum):
    # HZ_1 = 0x01  # 1 Hz, i.e., 1 reading per second
    # HZ_4 = 0x04  # 4 Hz, i.e., 4 readings per second
    # HZ_8 = 0x08  # 8 Hz, i.e., 8 readings per second
    
    # Log readings for a specified amount of time
    asyncio.run(calypso_read(filename, data_rate, log_duration=10)) # 60 s