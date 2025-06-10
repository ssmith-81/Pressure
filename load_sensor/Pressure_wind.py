import asyncio
import time
import h5py
from gattlib import GATTRequester
from calypso_anemometer.core import CalypsoDeviceApi, CalypsoDeviceDataRate

# === SETTINGS ===
PRINT_LOGS = True  # Set False to disable prints
HDF5_FILENAME = "merged_sensor_data.h5"

# BLE info
PICO_PRESSURE_ADDR = "28:CD:C1:13:1E:48"
PRESSURE_HANDLE = 0x09

# === DATA LOGGING ===

def conversion_h5(value, sensor_n, dt, h5f):
    press_counts = value[2] + value[1] * 256 + value[0] * 65536
    temp_counts = value[5] + value[4] * 256 + value[3] * 65536
    outputmax = 15099494
    outputmin = 1677722
    pmax = 1
    pmin = 0

    pressure = ((press_counts - outputmin) * (pmax - pmin)) / (outputmax - outputmin) + pmin
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

    if PRINT_LOGS:
        print(f"[PRESSURE] {timestamp:.2f}: p={pressure:.3f} bar, temp={temperature:.1f}°C")

def log_pressure_sensor(h5f, last_time):
    try:
        req = GATTRequester(PICO_PRESSURE_ADDR)
        req.exchange_mtu(720)
        aux = req.read_by_handle(PRESSURE_HANDLE)[0]
        req.disconnect()
    except Exception as e:
        if PRINT_LOGS:
            print(f"[ERROR] Pressure read failed: {e}")
        return None, last_time

    new_time = time.time()
    dt = new_time - last_time if last_time else 0.0

    aux_tmp1 = aux.decode('utf-8')
    if aux_tmp1:
        aux_tmp1 = aux_tmp1.replace(aux_tmp1[0], "", 1)
        aux_tmp1 = aux_tmp1[:-1].split(',')

        length = len(aux_tmp1)
        cycles = length / 7
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
                        conversion_h5([int(x) for x in aux_tmp1[n * 7:j + 1]], int(aux_tmp1[j]), dt, h5f)
                        n += 1

    return aux_tmp1, new_time

def start_wind_logging(h5f, log_duration=60, wind_log_rate=1):
    async def wind_logger():
        if PRINT_LOGS:
            print(f"[WIND] Starting wind logging for {log_duration}s at {wind_log_rate} Hz")

        async with CalypsoDeviceApi() as calypso:
            # Set data rate (must be one of CalypsoDeviceDataRate)
            rate_enum = {
                1: CalypsoDeviceDataRate.HZ_1,
                4: CalypsoDeviceDataRate.HZ_4,
                8: CalypsoDeviceDataRate.HZ_8,
            }.get(wind_log_rate, CalypsoDeviceDataRate.HZ_1)
            await calypso.set_datarate(rate_enum)

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

                if PRINT_LOGS:
                    print(f"[WIND] {timestamp:.2f}: speed={reading.wind_speed:.2f} m/s, dir={reading.wind_direction}°")

            await calypso.subscribe_reading(log_reading)

            try:
                await asyncio.sleep(log_duration)
            finally:
                if PRINT_LOGS:
                    print("[WIND] Unsubscribing from wind sensor readings")
                await calypso.unsubscribe_reading()

    return wind_logger()

def initialize_h5():
    h5f = h5py.File(HDF5_FILENAME, 'a')
    keys = {
        'pressure_timestamp': 'f', 'pressure_value': 'f', 'pressure_percentage': 'f', 'pressure_temperature': 'f',
        'pressure_counts': 'i', 'temp_counts': 'i', 'pressure_dt': 'f', 'sensor_n': 'i',
        'wind_timestamp': 'f', 'wind_speed': 'f', 'wind_direction': 'i', 'wind_battery': 'f',
        'wind_temp': 'f', 'wind_roll': 'f', 'wind_pitch': 'f', 'wind_heading': 'f'
    }
    for k, dtype in keys.items():
        if k not in h5f:
            h5f.create_dataset(k, (0,), maxshape=(None,), dtype=dtype)
    return h5f

async def main():
    h5f = initialize_h5()
    last_time = time.time()

    # Configurable params
    log_duration = 60         # seconds
    wind_log_rate = 1         # Hz (choose from 1,4,8)

    wind_task = asyncio.create_task(start_wind_logging(h5f, log_duration, wind_log_rate))

    start_time = time.time()
    try:
        while time.time() - start_time < log_duration:
            _, last_time = log_pressure_sensor(h5f, last_time)
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("Logging stopped by user.")
    finally:
        wind_task.cancel()
        try:
            await wind_task
        except asyncio.CancelledError:
            pass
        h5f.close()


if __name__ == "__main__":
    asyncio.run(main())
