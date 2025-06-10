# === IMPORTS ===
import time
import threading
from datetime import datetime
from gattlib import GATTRequester
from bleak import BleakClient
import asyncio
import numpy as np
import nest_asyncio
nest_asyncio.apply()

# === BLE SHARED LOCK ===
ble_lock = asyncio.Lock()

# === PRESSURE SENSOR FUNCTIONS ===
def write_file(datafile, string):
    with open(datafile, 'a') as file:
        file.write(string + '\n')

def conversion(value, sensor_n, file_name, dt=None):
    press_counts = value[2] + value[1]*256 + value[0]*65536
    temp_counts = value[5] + value[4]*256 + value[3]*65536

    outputmax = 15099494
    outputmin = 1677722
    pmax = 1
    pmin = 0

    pressure = ((press_counts - outputmin)*(pmax - pmin))/(outputmax - outputmin) + pmin
    percentage = (press_counts / 16777215) * 100
    temperature = (temp_counts * 200 / 16777215) - 50

    timestamp = datetime.now().isoformat()
    data = f"{timestamp}, dt: {dt:.3f}s, pressure: {pressure}, percentage: {percentage}, temperature: {temperature}, press_counts: {press_counts}, temp_counts: {temp_counts}"
    datafile = f"{file_name} pressure_sensor {sensor_n}.txt"

    write_file(datafile, data)

    print("=== PRESSURE SENSOR ===")
    print(f"Sensor {sensor_n} | Pressure: {pressure:.3f} | Temp: {temperature:.2f}°C | dt: {dt:.3f}s")

def peripheric_pico(address_picos, handle_number, name_cluster, last_time):
    try:
        print("Connecting to pressure sensor...")
        req = GATTRequester(address_picos)
        req.exchange_mtu(720)
        print("connected ok")
        aux = req.read_by_handle(handle_number)[0]
        req.disconnect()
        print("disconnected ok")
    except Exception as e:
        print(f"[ERROR] Failed pressure read: {e}")
        return None, last_time

    new_time = time.time()
    dt = new_time - last_time if last_time is not None else 0.0

    aux_tmp1 = aux.decode('utf-8')
    if len(aux_tmp1) != 0:
        aux_tmp1 = aux_tmp1.replace(aux_tmp1[0], "", 1)
        aux_tmp1 = aux_tmp1[:-1]
        aux_tmp1 = aux_tmp1.split(',')

        length = len(aux_tmp1)
        cycles = length / 7
        array_data = [0 for _ in range(length)]

        if cycles.is_integer():
            n = 0
            open_ch = [k for k in range(0, length, 7)]
            close_ch = [l for l in range(6, length, 7)]
            while n < cycles:
                for j in range(length):
                    if j in open_ch:
                        aux_tmp1[j] = aux_tmp1[j].replace('(', "")
                        array_data[j] = int(aux_tmp1[j])
                    if j in close_ch:
                        aux_tmp1[j] = aux_tmp1[j].replace(')', "")
                        array_data[j] = int(aux_tmp1[j])
                        conversion(array_data[n*7:j+1], array_data[j], name_cluster, dt)
                        n += 1
                    array_data[j] = int(aux_tmp1[j])

        return array_data, new_time
    return None, last_time

def pressure_loop(address_pico, handle_number, name_cluster):
    last_time = time.time()
    while True:
        _, last_time = peripheric_pico(address_pico, handle_number, name_cluster, last_time)
        time.sleep(0.1)

# === LOAD SENSOR FUNCTIONS ===
char_uuid = "0000ffb1-0000-1000-8000-00805f9b34fb"
load_sensor_address = "84:C6:92:EC:BF:AC"

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

async def load_sensor_loop():
    retry_delay = 5  # seconds
    while True:
        async with ble_lock:
            try:
                async with BleakClient(load_sensor_address) as client:
                    if not client.is_connected:
                        print("[ERROR] Client not connected")
                        continue
                    response = await client.read_gatt_char(char_uuid)
                    TC = twos_comp_32(response)
                    weight_kg = TC / 10
                    timestamp = datetime.now().isoformat()
                    log_str = f"{timestamp}, Load Sensor (kg): {weight_kg:.2f}"
                    write_file("load_sensor_log.txt", log_str)
                    print("=== LOAD SENSOR ===")
                    print(log_str)
            except Exception as e:
                print(f"[ERROR] Load sensor read failed: {e}")
        await asyncio.sleep(retry_delay)

# === MAIN ===
def main():
    address_pico2 = "28:CD:C1:13:1E:48"
    handle_number = 0x09
    name_cluster2 = "Cluster " + str(address_pico2)

    pressure_thread = threading.Thread(
        target=pressure_loop,
        args=(address_pico2, handle_number, name_cluster2),
        daemon=True
    )
    pressure_thread.start()

    asyncio.run(load_sensor_loop())

if __name__ == "__main__":
    main()
