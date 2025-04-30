#Elfrich GONZALEZ AREVALO 5/JUNE/2024 
from gattlib import GATTRequester,GATTResponse
import time


'''
if len(sys.argv)!=3:
    print("Usage: {} <addr> <characteristic-UUID>".format(sys.argv[0]))
    sys.exit(1)
'''


def write_file(datafile,string):
    with open(datafile,'a') as file:
        file.write(string + '\n')


def conversion(value,sensor_n,file_name):
    #print(len(value))
    press_counts=0
    temp_counts=0
    pressure=0.0
    temperature=0.0
    outputmax=15099494
    outputmin=1677722
    pmax=1
    pmin=0
    percentage=0
    press_counts = value[2]+value[1]*256+value[0]*65536
    pressure = ((press_counts - outputmin)*(pmax-pmin))/(outputmax-outputmin)+pmin
    percentage = (press_counts/16777215)*100
    temp_counts = value[5] + value[4]*256 + value[3]*65536
    temperature = (temp_counts*200/16777215)-50
    data= 'pressure: '+str(pressure)+' '+ 'percentage: '+str(percentage) + ' '+'temperature: '+str(temperature) + ' '+'press_counts: '+str(press_counts) + ' '+'temp_counts: ' +str(temp_counts) 
    datafile = file_name + ' pressure_sensor ' + str(sensor_n) + '.txt'
    write_file(datafile,data)
    print("===================================")
    print("txt file:{}".format(datafile))
    print("sensor number:{}".format(sensor_n))
    print("pressure: {}".format(pressure))
    print("percentage: {}".format(percentage))
    print("press_counts: {}".format(press_counts))
    print("temp_counts: {}".format(temp_counts))
    print("temperature: {}".format(temperature))

    #return (pressure,percentage,temperature,temp_counts,press_counts)
        
def peripheric_pico(address_picos,handle_number,name_cluster):
  print("Connecting...")
  req = GATTRequester(address_picos)#,auto_connect=True)
  req.exchange_mtu(720)
  print("connected ok")
  aux = req.read_by_handle(handle_number)[0]
  req.disconnect()
  print("disconnected ok")
  #print("aux: {}".format(aux)) 
  aux_tmp1 = aux.decode('utf-8')
  if len(aux_tmp1) != 0:
    '''
    print("0 aux_tmp1: {}".format(aux_tmp1))
    print(type(aux_tmp1))
    print(len(aux_tmp1))
    '''
    
    aux_tmp1 = aux_tmp1.replace(aux_tmp1[0],"",1)#delete first character '['
    #if aux_tmp1[len(aux_tmp1)-1] != 'e':
    aux_tmp1 = aux_tmp1[:-1]#delete last character '['
    '''
    print("1 aux_tmp1: {}".format(aux_tmp1))
    print(type(aux_tmp1))
    print(len(aux_tmp1))
    '''
    aux_tmp1 = aux_tmp1.split(',')#
    '''
    print("2 split aux_tmp1: {}".format(aux_tmp1))
    print(type(aux_tmp1))
    print(len(aux_tmp1))
    '''
    #==============
    length = len(aux_tmp1)
    cycles = length/7
    #print("cycles: {}".format(cycles))
    array_data = [0 for i in range(length)]
    
    if cycles.is_integer() == True:
        n = 0
        open_ch = [k for k in range(0,length,7)]
        close_ch = [l for l in range(6,length,7)]
        while n < cycles:
            for j in range(length):
                if j in open_ch:
                    aux_tmp1[j]=aux_tmp1[j].replace('(',"")#delete first character '('
                    array_data[j]=int(aux_tmp1[j])
                if j in close_ch:
                    aux_tmp1[j]=aux_tmp1[j].replace(')',"")#delete last character ')'
                    array_data[j]=int(aux_tmp1[j])
                    conversion(array_data[n*7:j],array_data[j],name_cluster)# + str(n))
                    n+=1
                    
                array_data[j]=int(aux_tmp1[j])    
        #print("aux_tmp1: {}".format(aux_tmp1))

    return array_data

def main():
    address_pico = "28:CD:C1:13:1E:46"#"28:CD:C1:11:62:12"
    address_pico2 = "28:CD:C1:13:1E:48"
    handle_number = 0x09
    name_cluster = "Cluster " + str(address_pico)    
    name_cluster2 = "Cluster " + str(address_pico2)
    aux_data=[0]
    
    #for i in range(0,5,1):
    #  for j in range(0,5,1):
    aux_data = peripheric_pico(address_pico,handle_number,name_cluster)
    #aux_data2 = peripheric_pico(address_pico2,handle_number,name_cluster2)
        
    

    
    #print("data in")
    #print(type(aux_data))
    #print(aux_data)
    #print(len(aux_data))
    
    
if __name__ == "__main__":
    main()
    
