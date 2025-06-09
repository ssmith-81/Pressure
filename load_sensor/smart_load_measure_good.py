# Check that the sensor is NOT connected to the computer

import asyncio
from bleak import BleakClient
#from PyObjCTools import KeyValueCoding
import numpy as np

import nest_asyncio
nest_asyncio.apply()

#Services
# Direct connection smartload integration guide
char_uuid = "0000ffb1-0000-1000-8000-00805f9b34fb" # Load data characteristic (Channel A)
# char_uuid = "0000ffb4-0000-1000-8000-00805f9b34fb" # Battery level characteristic
# char_uuid = "0000ffb5-0000-1000-8000-00805f9b34fb" # Status characteristic
# char_uuid = "0000ffc1-0000-1000-8000-00805f9b34fb" # Local name characteristic
# char_uuid = "0000ffc3-0000-1000-8000-00805f9b34fb" # Period

def twos_comp_32(var_byte):
    # Computes the 2-complement of a 32 bits variable in byte array format
    # Checked with
    # https://www.rapidtables.com/convert/number/hex-to-decimal.html?x=00000016
    for n in range(0, len(var_byte), 4):
        y = int.from_bytes(var_byte[n:(n+4)], 'little')
    # print(f"hex value: {hex(y)}")
    # print(f"integer value: {y}")
    aux0 = str(bin(np.longlong(y)))
    aux0 = aux0.replace('0b', '')
    # https://gist.github.com/ariutti/80173ac6fa1acef4c7ab2a9aecf038a5
    N = int(aux0, 2)
    # this is the two complements
    if len(aux0) == 32:
        TC = (-1)*(4294967295 + 1 - N)
    else:
        TC = N
    return TC

async def main():    
    address = "84:C6:92:EC:BF:AC" #str(KeyValueCoding.getKey(myDevice.details,'identifier'))
    async with BleakClient(address) as client:
        # Read the response from the characteristic and print to the console        
        response = await client.read_gatt_char(char_uuid)
        TC = twos_comp_32(response)
        print(f"Weight (kg): {TC/10}")


asyncio.run(main())
