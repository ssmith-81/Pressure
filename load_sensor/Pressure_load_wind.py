import asyncio
import time
from datetime import datetime
import numpy as np
import h5py
from gattlib import GATTRequester
from bleak import BleakClient
from calypso_anemometer.core import CalypsoDeviceApi, CalypsoDeviceDataRate

# UUID for Load Sensor (Channel A)
LOAD_SENSOR_UUID = "0000ffb1-0000-1000-8000-00805f9b34fb"

# BLE addresses
PICO_PRESSURE_ADDR = "28:CD:C1:13:1E:48"
LOAD_SENSOR_ADDR = "84:C6:92:EC:BF:AC"

# Pressure sensor characteristic handle
PRESSURE_HANDLE = 0x09

# HDF5 filename
HDF5_FILENAME = "merged_sensor_data.h5"

# Convert raw 32-bit byte array to 2's complement integer
def twos_comp_32(var_byte):
    for n in range(0, len(var_byte), 4):
        y = int.from_bytes(var_byte[n:(n+4)], 'little')
    aux0 = str(bin(np.longlong(y))).replace('0b', '')
    N = int(aux0, 2)
    if len(aux0) == 32:
        TC = -1 * (4294967295 + 1 - N)
    else:
        TC = N
    return TC

# Process and store pressure sensor data
def conversion_h5(value, sensor_n, dt, h5f):
    press_counts = value[2] + value[1]*256 + value[0]*65536
    temp_counts = value[5] + value[4]*256 + value[3]*65536
    outputmax = 15099494
    outputmin = 1677722
    pmax = 1
    pmin = 0

    pressure = ((press_counts - outputmin)*(pmax - pmin))/(outputmax - outputmin) + pmin
    percentage = (press_counts / 16777215) * 100
    temperature = (temp_counts * 200 / 16777215) - 50
    timestamp = time.time()

    for k, v in zip([
        'pressure_timestamp', 'pressure_value', 'pressure_percentage', 'pressure_temperature',
        'pressure_counts', 'temp_counts', 'pressure_dt', 'sensor_n'
    ], [
        timestamp, pressure, percentage, temperature, press_counts, temp_counts, dt, sensor_n
    ]):
        h5f[k].resize((h5f[k].shape[0] + 1,))
        h5f[k][-1] = v

# Connect and read pressure data from Pico using gattlib
def log_pressure_sensor(h5f, last_time):
    try:
        req = GATTRequester(PICO_PRESSURE_ADDR)
        req.exchange_mtu(720)
        aux = req.read_by_handle(PRESSURE_HANDLE)[0]
        req.disconnect()
    except Exception as e:
        print(f"[ERROR] Pressure read failed: {e}")
        return None, last_time

    new_time = time.time()
    dt = new_time - last_time if last_time is not None else 0.0

    aux_tmp1 = aux.decode('utf-8')
    if aux_tmp1:
        aux_tmp1 = aux_tmp1.replace(aux_tmp1[0], "", 1)
        aux_tmp1 = aux_tmp1[:-1].split(',')

        length = len(aux_tmp1)
        cycles = length / 7
        array_data = [0] * length

        if cycles.is_integer():
            n = 0
            open_ch = list(range(0, length, 7))
            close_ch = list(range(6, length, 7))
            while n < cycles:
                for j in range(length):
                    if j in open_ch:
                        aux_tmp1[j] = aux_tmp1[j].replace('(', '')
                    if j in close_ch:
                        aux_tmp1[j] = aux_tmp1[j].replace(')', '')
                        conversion_h5([int(x) for x in aux_tmp1[n*7:j+1]], int(aux_tmp1[j]), dt, h5f)
                        n += 1
                    array_data[j] = int(aux_tmp1[j])

    return array_data, new_time

# Read and store load sensor value via Bleak
async def log_load_sensor(h5f):
    try:
        async with BleakClient(LOAD_SENSOR_ADDR) as client:
            response = await client.read_gatt_char(LOAD_SENSOR_UUID)
            TC = twos_comp_32(response)
            weight = TC / 10
            timestamp = time.time()

            h5f['load_timestamp'].resize((h5f['load_timestamp'].shape[0] + 1,))
            h5f['load_timestamp'][-1] = timestamp
            h5f['load_kg'].resize((h5f['load_kg'].shape[0] + 1,))
            h5f['load_kg'][-1] = weight
    except Exception as e:
        print(f"[ERROR] Load read failed: {e}")

# Continuously read wind sensor data and log
def start_wind_logging(h5f):
    async def wind_logger():
        async with CalypsoDeviceApi() as calypso:
            await calypso.set_datarate(CalypsoDeviceDataRate.HZ_1)

            def log_reading(reading):
                timestamp = time.time()
                for key, value in zip([
                    'wind_timestamp', 'wind_speed', 'wind_direction', 'wind_battery',
                    'wind_temp', 'wind_roll', 'wind_pitch', 'wind_heading'
                ], [
                    timestamp, reading.wind_speed, reading.wind_direction, reading.battery_level,
                    reading.temperature, reading.roll, reading.pitch, reading.heading
                ]):
                    h5f[key].resize((h5f[key].shape[0] + 1,))
                    h5f[key][-1] = value

            await calypso.subscribe_reading(log_reading)
            try:
                while True:
                    await asyncio.sleep(1)
            finally:
                await calypso.unsubscribe_reading()

    return wind_logger()

# Create and initialize HDF5 datasets
def initialize_h5():
    h5f = h5py.File(HDF5_FILENAME, 'a')
    keys = {
        'pressure_timestamp': 'f', 'pressure_value': 'f', 'pressure_percentage': 'f', 'pressure_temperature': 'f',
        'pressure_counts': 'i', 'temp_counts': 'i', 'pressure_dt': 'f', 'sensor_n': 'i',
        'load_timestamp': 'f', 'load_kg': 'f',
        'wind_timestamp': 'f', 'wind_speed': 'f', 'wind_direction': 'i', 'wind_battery': 'f',
        'wind_temp': 'f', 'wind_roll': 'f', 'wind_pitch': 'f', 'wind_heading': 'f'
    }
    for k, dtype in keys.items():
        if k not in h5f:
            h5f.create_dataset(k, (0,), maxshape=(None,), dtype=dtype)
    return h5f

# Main loop
async def main():
    h5f = initialize_h5()
    last_time = time.time()
    wind_task = asyncio.create_task(start_wind_logging(h5f))

    try:
        while True:
            _, last_time = log_pressure_sensor(h5f, last_time)
            await log_load_sensor(h5f)
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("Logging stopped by user.")
    finally:
        wind_task.cancel()
        h5f.close()

if __name__ == "__main__":
    asyncio.run(main())
