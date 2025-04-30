# This example demonstrates a UART periperhal.

# This example demonstrates the low-level bluetooth module. For most
# applications, we recommend using the higher-level aioble library which takes
# care of all IRQ handling and connection management. See
# https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble
# 03/june/2024 modified by Elfrich GONZALEZ AREVALO to send data from a pressure sensor in a cluster
# last update 26/june/2024 by Elfrich GONZALEZ AREVALO: in the function i2c.writeto(arg1,arg2), the hex. address must be i2c.writeto(mux_addr,b'\x01')  

import bluetooth
import random
import struct
import time
from ble_advertising import advertising_payload

from machine import Pin, I2C
#from machine import Pin, SoftI2C
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)

from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)


class BLESimplePeripheral:
    def __init__(self, ble, name="node0"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()
        self._ble.gatts_set_buffer(self._handle_tx, 720)

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            #self._ble.gatts_notify(conn_handle, self._handle_tx, data)            
            self._ble.gatts_write(self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=100000):#500000
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback

def MUX_I2C_TCA9548A():
    data0=()
    data1=()
    data2=()
    data3=()
    data4=()
    data5=()
    data6=()
    data7=()
    send_data = []#bytearray([0,0,0,0,0,0,0,0])
    array_ = []
    mux_addr = 0x70
    addrs0 = i2c.scan()
    wait_x = 1 #10
    print("Scanning Mux devices:", [hex(x) for x in addrs0])
    
    if mux_addr not in addrs0:
        print("I2C Mux TCA9548A is not detected")
        #send_data = bytearray([0,0,0,0,0,0,0,0])
        #return send_data
    else:
         while True:
             i2c.writeto(mux_addr,b'\x00') # disable channels
             i2c.writeto(mux_addr,b'\x01') # enable channel 0
             time.sleep_ms(wait_x)
             data0 = I2C_ABP2DRRN002ND2B3XX()
             
             if len(data0) != 0:#if type(data0) != str:
                 data0 = data0  + (1,) #adding sensor number
             time.sleep_ms(wait_x)
             i2c.writeto(mux_addr,b'\x00') # disable channel 0
             
             i2c.writeto(mux_addr,b'\x02') # enable channel 1
             time.sleep_ms(wait_x)
             data1 = I2C_ABP2DRRN002ND2B3XX()
             if len(data1) != 0:#if type(data1) != str:
                 data1 = data1  + (2,)
             time.sleep_ms(wait_x) 
             i2c.writeto(mux_addr,b'\x00') # disable channels
             
             i2c.writeto(mux_addr,b'\x04') # enable channel 2
             time.sleep_ms(wait_x)
             data2 = I2C_ABP2DRRN002ND2B3XX()
             if len(data2) != 0:#if type(data2) != str:
                 data2 = data2 + (3,)
             time.sleep_ms(wait_x)
             i2c.writeto(mux_addr,b'\x00') # disable channels
             
             i2c.writeto(mux_addr,b'\x08') # enable channel 3
             time.sleep_ms(wait_x)
             data3 = I2C_ABP2DRRN002ND2B3XX()
             if len(data3) != 0:#if type(data3) != str:
                 data3 = data3 + (4,)
             time.sleep_ms(wait_x)
             i2c.writeto(mux_addr,b'\x00') # disable channels
             
             i2c.writeto(mux_addr,b'\x10') # enable channel 4
             time.sleep_ms(wait_x)
             data4 = I2C_ABP2DRRN002ND2B3XX()
             if len(data4) != 0:#if type(data4) != str:
                 data4 = data4  + (5,)
             time.sleep_ms(wait_x)
             i2c.writeto(mux_addr,b'\x00') # disable channels
             
             i2c.writeto(mux_addr,b'\x20') # enable channel 5
             time.sleep_ms(wait_x)
             data5 = I2C_ABP2DRRN002ND2B3XX()
             if len(data5) != 0:#if type(data5) != str:
                 data5 = data5 + (6,)
             time.sleep_ms(wait_x)
             i2c.writeto(mux_addr,b'\x00') # disable channels
             
             i2c.writeto(mux_addr,b'\x40') # enable channel 6
             time.sleep_ms(wait_x)
             data6 = I2C_ABP2DRRN002ND2B3XX()
             if len(data6) != 0:#if type(data6) != str:
                 data6 = data6 + (7,)
             time.sleep_ms(wait_x)
             i2c.writeto(mux_addr,b'\x00') # disable channels
             
             i2c.writeto(mux_addr,b'\x80') # enable channel 7
             time.sleep_ms(wait_x)
             data7 = I2C_ABP2DRRN002ND2B3XX()
             if len(data7) != 0:#if type(data7) != str:
                 data7 = data7 + (8,)
             time.sleep_ms(wait_x)
             i2c.writeto(mux_addr,b'\x00') # disable channels
             
             
             array_ = [data0,data1,data2,data3,data4,data5,data6,data7]
             #array_ = [data0,data0,data0,data0,data0,data0,data0,data0]
             #array_ = [data1,data0,data0,data3,data4,data0,data0,data7]
             
                          
             length=len(array_)
             j = length-1             
             while j >= 0:                 
                 if len(array_[j]) == 0:                     
                     array_.pop(j)
                 j-=1
                 
             send_data = array_    
             return send_data
             

def I2C_ABP2DRRN002ND2B3XX():
    press_counts = 0
    temp_counts = 0
    pressure = 0
    temperature = 0
    outputmax = 15099494
    outputmin = 1677722
    pmax = 1
    pmin = 0
    percentage = 0
    addrs = i2c.scan()
    print("Scanning devices:", [hex(x) for x in addrs])
    pS_addr = 0x28    
    pS_cmd = [0xAA,0x00,0x00]#cmd to the pressure sensor
    pS_data = 7
    
    send_data=()
    array_int = []
    wait_x = 10
    
    if pS_addr not in addrs:
        print("Pressure Sensor ABP2DRRN002ND2B3XX is not detected")                
    else:
            ##while True:
            n_acks=i2c.writeto(pS_addr,bytearray(pS_cmd))#with vector
            #print(n_acks)
            time.sleep_ms(wait_x)
            aux = i2c.readfrom(pS_addr, pS_data)
            array_int=(aux[1],aux[2],aux[3],aux[4],aux[5],aux[6])            
            send_data = array_int
            #aux = i2c.readfrom_mem(pS_addr,0x00, pS_data)            
            time.sleep_ms(wait_x)
            #int_val= int.from_bytes(aux,"big")
            press_counts = aux[3]+aux[2]*256+aux[1]*65536
            pressure = ((press_counts - outputmin)*(pmax-pmin))/(outputmax-outputmin) + pmin
            percentage = (press_counts/16777215)*100
            temp_counts = aux[6]+aux[5]*256+aux[4]*65536
            temperature = (temp_counts*200/16777215) -50
            #send_data = str(pressure) +","+ str(percentage)+"," + str(temperature)+"," + str(press_counts)+"," + str(temp_counts) 
            #send_data = [str(pressure),str(percentage),str(temperature),str(press_counts),str(temp_counts)]
            #send_data = [hex(pressure),hex(percentage),hex(temperature),hex(press_counts),hex(temp_counts)]
            #send_data = [pressure,percentage,temperature,press_counts,temp_counts]                   
            '''
            print("-- values --")
            #print(int_val)
            print("data_sensor: {}".format(aux) )
            print(type(aux))            
            print(f'press_counts: {press_counts}')
            print(f'temp_counts: {temp_counts}')
            print(f'* temperature: {temperature}')
            print(f'* pressure: {pressure}')
            print(f'percentage: {percentage}')
            '''
    return send_data
    #print("*--End transmisition--*")
    #return send_data

def com_ble():
    ble = bluetooth.BLE()
    p = BLESimplePeripheral(ble)
    send_data=[]
    led = Pin('LED', Pin.OUT)
    
    for i in range(0,5):
        led.low()
        time.sleep_ms(25)
        led.high()
        time.sleep_ms(25)

    #def on_rx(v):
    #    print("RX", v)

    #p.on_write(on_rx)

    #i = 0
    while True:
        led.low()
        '''
        led.low()
        time.sleep_ms(500)
        led.high()
        time.sleep_ms(500)
        '''
        if p.is_connected():


                # Short burst of queued notifications.            
                send_data = MUX_I2C_TCA9548A()#str(i) + "_"
                #print(len(send_data[0]))
                #print(type(send_data[0]))
                ##print("TX", send_data)
                #p.send("123456789.0 123456789.1 123456789.2 123456789.3 123456789.4 123456789.5 123456789.6 123456789.7 123456789.8")
                p.send(str(send_data).encode())
                #p.send(send_data)
                led.low()
                time.sleep_ms(55)
                led.high()
                time.sleep_ms(55)
                send_data=[]
            
        led.low()
        #time.sleep_ms(100)


if __name__ == "__main__":
    com_ble()
