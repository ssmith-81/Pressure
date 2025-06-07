#Elfrich GONZALEZ AREVALO 5/JUNE/2024 
from gattlib import GATTRequester,GATTResponse
import time
from datetime import datetime


'''
if len(sys.argv)!=3:
    print("Usage: {} <addr> <characteristic-UUID>".format(sys.argv[0]))
    sys.exit(1)
'''


def write_file(datafile,string):
    with open(datafile,'a') as file:
        file.write(string + '\n')


from datetime import datetime

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

    print("===================================")
    print(f"txt file: {datafile}")
    print(f"sensor number: {sensor_n}")
    print(f"pressure: {pressure}")
    print(f"percentage: {percentage}")
    print(f"press_counts: {press_counts}")
    print(f"temp_counts: {temp_counts}")
    print(f"temperature: {temperature}")
    print(f"dt: {dt:.3f} s  --> {1/dt:.2f} Hz" if dt and dt > 0 else "")


    #return (pressure,percentage,temperature,temp_counts,press_counts)
        
def peripheric_pico(address_picos, handle_number, name_cluster, last_time):
    print("Connecting...")
    req = GATTRequester(address_picos)
    req.exchange_mtu(720)
    print("connected ok")

    aux = req.read_by_handle(handle_number)[0]
    req.disconnect()
    print("disconnected ok")

    new_time = time.time()
    dt = new_time - last_time if last_time is not None else 0.0

    aux_tmp1 = aux.decode('utf-8').lstrip('[').rstrip(']')
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
                elif j in close_ch:
                    aux_tmp1[j] = aux_tmp1[j].replace(')', "")
                    array_data[j] = int(aux_tmp1[j])
                    conversion(array_data[n*7:j+1], array_data[j], name_cluster, dt)
                    n += 1
                else:
                    array_data[j] = int(aux_tmp1[j])
    return array_data, new_time


def main():
    address_pico = "28:CD:C1:13:1E:46"#"28:CD:C1:11:62:12"
    address_pico2 = "28:CD:C1:13:1E:48"
    handle_number = 0x09
    name_cluster = "Cluster " + str(address_pico)    
    name_cluster2 = "Cluster " + str(address_pico2)
    aux_data=[0]

    last_time = time.time()
    
    #for i in range(0,5,1):
    #  for j in range(0,5,1):
    # aux_data = peripheric_pico(address_pico,handle_number,name_cluster)
    #aux_data2 = peripheric_pico(address_pico2,handle_number,name_cluster2)

     # Continuous logging loop
    try:
        while True:
            aux_data, last_time = peripheric_pico(address_pico, handle_number, name_cluster, last_time)
            time.sleep(0.1)  # Optional delay to avoid hammering the BLE device
    except KeyboardInterrupt:
        print("Logging stopped by user.")
        
    

    
    #print("data in")
    #print(type(aux_data))
    #print(aux_data)
    #print(len(aux_data))
    
    
if __name__ == "__main__":
    main()
    
