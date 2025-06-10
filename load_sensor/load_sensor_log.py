import asyncio
import time
import h5py
import numpy as np
from bleak import BleakClient
import nest_asyncio
nest_asyncio.apply()

# UUID for Load Data characteristic
CHAR_UUID = "0000ffb1-0000-1000-8000-00805f9b34fb"
ADDRESS = "84:C6:92:EC:BF:AC"  # Your sensor MAC address

def twos_comp_32(var_byte):
    # Computes the 2-complement of a 32-bit variable in byte array format
    for n in range(0, len(var_byte), 4):
        y = int.from_bytes(var_byte[n:(n+4)], 'little')
    aux0 = str(bin(np.longlong(y)))
    aux0 = aux0.replace('0b', '')
    N = int(aux0, 2)
    if len(aux0) == 32:
        TC = (-1)*(4294967295 + 1 - N)
    else:
        TC = N
    return TC

def initialize_h5(filename):
    h5f = h5py.File(filename, 'a')
    if 'force_timestamp' not in h5f:
        h5f.create_dataset('force_timestamp', (0,), maxshape=(None,), dtype='f8')
    if 'force_value' not in h5f:
        h5f.create_dataset('force_value', (0,), maxshape=(None,), dtype='f8')
    return h5f

def log_force_reading(h5f, timestamp, value):
    h5f['force_timestamp'].resize((h5f['force_timestamp'].shape[0] + 1,))
    h5f['force_timestamp'][-1] = timestamp
    h5f['force_value'].resize((h5f['force_value'].shape[0] + 1,))
    h5f['force_value'][-1] = value
    h5f.flush()

async def run_force_sensor(h5f):
    async with BleakClient(ADDRESS) as client:
        print("[FORCE SENSOR] Connected, starting continuous logging...")
        try:
            while True:
                response = await client.read_gatt_char(CHAR_UUID)
                TC = twos_comp_32(response)
                weight_kg = TC / 10
                timestamp = time.time()
                log_force_reading(h5f, timestamp, weight_kg)
                print(f"[FORCE] {timestamp:.6f}: Weight (kg): {weight_kg:.2f}")
                await asyncio.sleep(0.1)  # Adjust delay as needed for your sensor's update rate
        except asyncio.CancelledError:
            print("[FORCE SENSOR] Logging cancelled.")
        except Exception as e:
            print(f"[FORCE SENSOR] Error: {e}")

async def main():
    h5f = initialize_h5('force_data.h5')
    task = asyncio.create_task(run_force_sensor(h5f))
    try:
        await task
    except KeyboardInterrupt:
        print("Force sensor logging stopped by user.")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    finally:
        h5f.close()

if __name__ == "__main__":
    asyncio.run(main())
