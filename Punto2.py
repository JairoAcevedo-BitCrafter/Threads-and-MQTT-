import threading
import time
import serial
import board
import busio
import adafruit_adxl34x
from queue import Queue
import paho.mqtt.publish as publish
from datetime import datetime

i2c= busio.I2C(board.SCL, board.SDA)
accelerometer= adafruit_adxl34x.ADXL345(i2c)

def leer_temperatura():
    sensor_directory = '/sys/bus/w1/devices/'
    dispositivo = '28-d6531e1e64ff'
    archivo_temperatura = sensor_directory + dispositivo + '/temperature'
    try:
        with open(archivo_temperatura, 'r') as archivo:
            lineas = archivo.readlines()
    except FileNotFoundError:
        print("Error al abrir el archivo de temperatura.")
        return None
    temperatura_celsius = float(lineas[0]) / 1000.0
    return temperatura_celsius
def leer_i2c():
    x, y, z = accelerometer.acceleration
    acc=[x, y, z]
    return acc

# Datos compartidos entre los hilos
temp_data = []
i2c_x_data = []
i2c_y_data = []
i2c_z_data = []
cola_temp = Queue()
cola_prom_x = Queue()
cola_prom_y = Queue()
cola_prom_z = Queue()
cola_temp_mqtt = Queue()
cola_prom_x_mqtt = Queue()
cola_prom_y_mqtt = Queue()
cola_prom_z_mqtt = Queue()
N = 2
serial_data_received = None
evento_prom_temp = threading.Event()
evento_prom_acc = threading.Event()
evento_temp_mqtt = threading.Event()
evento_acc_mqtt = threading.Event()
ser = serial.Serial('/dev/ttyS0', 115200, timeout=1) 
def prom_temp(cola_temp,evento_prom_temp, cola_temp_mqtt, evento_temp_mqtt):
    global N
    acumulado_temp = 0
    contador_datos = 0
    while True:
        temp = float(leer_temperatura())
        acumulado_temp = float(acumulado_temp + temp)
        contador_datos += 1

        # Verifica si se alcanzó el tamaño de la ventana (N)
        if contador_datos >= N:
            # Calcula el promedio
            promedio = acumulado_temp / N

            # Añade el promedio a la cola
            cola_temp.put(promedio)
            cola_temp_mqtt.put(promedio)

            # Reinicia el acumulador y el contador
            acumulado_temp = 0
            contador_datos = 0
            evento_prom_temp.set()
            evento_temp_mqtt.set()
    #promedio
def prom_acc(cola_prom_x,cola_prom_y,cola_prom_z, evento_prom_acc, cola_prom_x_mqtt,cola_prom_y_mqtt,cola_prom_z_mqtt, evento_acc_mqtt):
    global N
    acumulado_acc = [0 ,0 ,0]
    contador_datos = 0
    while True:
        acc = leer_i2c()
        acumulado_acc[0] += acc[0]
        acumulado_acc[1] += acc[1]
        acumulado_acc[2] += acc[2]
        contador_datos += 1

        # Verifica si se alcanzó el tamaño de la ventana (N)
        if contador_datos >= N:
            # Calcula el promedio
            prom_x = acumulado_acc[0] / N
            prom_y = acumulado_acc[1] / N
            prom_z = acumulado_acc[2] / N

            # Añade el promedio a la cola
            cola_prom_x.put(prom_x)
            cola_prom_x_mqtt.put(prom_x)
            cola_prom_y.put(prom_y)
            cola_prom_y_mqtt.put(prom_y)
            cola_prom_z.put(prom_z)
            cola_prom_z_mqtt.put(prom_z)

            # Reinicia el acumulador y el contador
            acumulado_acc = [0 ,0 ,0]
            contador_datos = 0
            evento_prom_acc.set()
            evento_acc_mqtt.set()
def recibir_datos_serial():
    global N
    while True:
        datos_recibidos = ser.readline().decode('ascii')  
        if datos_recibidos:
            # Procesa los datos recibidos
            procesar_datos(datos_recibidos)
def procesar_datos(data):
    global N
    if (data[0:11] == "##PROMEDIO-") and (data[14:17] == "-##"): #Depuramos la trama de llegada
            N = int(data[11:14])
    else:
        print("Entrada invalida")
def enviar_datos_serial(cola_temp,cola_prom_x,cola_prom_y,cola_prom_z,evento_prom_temp,evento_prom_acc):
    while True:
        if(evento_prom_temp.is_set() and evento_prom_acc.is_set()):
            if not cola_prom_x.empty():
                prom_x = cola_prom_x.get()

            if not cola_prom_y.empty():
                prom_y = cola_prom_y.get()

            if not cola_prom_z.empty():
                prom_z = cola_prom_z.get()
            if not cola_temp.empty():
                prom_temp = cola_temp.get()
            if (not cola_prom_x.empty() and not cola_prom_y.empty() and not cola_prom_z.empty() and not cola_temp.empty()): 
                datos=f"N: {N},Temp: {prom_temp},ax: {prom_x},ay: {prom_y},az: {prom_z}\n\r"
                ser.write(datos.encode('ascii'))
                print(datos.encode('ascii'))
                evento_prom_temp.clear()
                evento_prom_acc.clear()
def subir_a_nube(cola_temp_mqtt, cola_prom_x_mqtt, cola_prom_y_mqtt, cola_prom_z_mqtt, evento_temp_mqtt,evento_acc_mqtt):           #definición del canal a transmitir
    channel_ID = "2349205"
    mqtt_host ="mqtt3.thingspeak.com"
    #definición del hospedador
    api_key = "X3OA324DECTW1ITN"
    mqtt_client_ID = "JxQqJSYqDg8XBzcMCiUNHzw"
#definición del usuario
    mqtt_username = "JxQqJSYqDg8XBzcMCiUNHzw"
#definición de la contraseña
    mqtt_password = "yTh7PrwKZ4G/tNYjbjKYQ74F"
    #definición del protocolo de capa 4
    t_transport = "tcp"
    #definición de puerto
    t_port = 1883
    #definición del topic
    topic =  "channels/" + channel_ID + "/publish" 
    while True:
        if(evento_temp_mqtt.is_set() and evento_acc_mqtt.is_set()):
            fechaActual=datetime.now()
            fechaActual2=datetime.strftime(fechaActual, '%d/%m/%Y,%H:%M:%S')
            acc_x = cola_prom_x_mqtt.get()
            acc_y = cola_prom_y_mqtt.get()
            acc_z = cola_prom_z_mqtt.get()
            temp = cola_temp_mqtt.get()
            print("NUBe 2")
            payload = "field1=" + fechaActual2 + "&field2=" + str(acc_x) + "&field3=" + str(acc_y) + "&field4=" + str(acc_z) + "&field5=" + str(temp)
            #publish.single(topic, payload, hostname=mqtt_host, transport=t_transport, port=t_port, tls=None, client_id=mqtt_client_ID, auth={'username':mqtt_username,'password':mqtt_password})
            publish.single(topic, payload, hostname=mqtt_host, transport=t_transport, port=t_port, client_id=mqtt_client_ID, auth={'username':mqtt_username,'password':mqtt_password})
            print("NUBe")
            evento_temp_mqtt.clear()
            evento_acc_mqtt.clear()
    
hilo_prom_temp = threading.Thread(target=prom_temp, args=(cola_temp,evento_prom_temp, cola_temp_mqtt, evento_temp_mqtt))
hilo_prom_acc = threading.Thread(target=prom_acc, args=(cola_prom_x,cola_prom_y,cola_prom_z, evento_prom_acc, cola_prom_x_mqtt,cola_prom_y_mqtt,cola_prom_z_mqtt, evento_acc_mqtt))
hilo_recibir_datos_serial = threading.Thread(target=recibir_datos_serial)
hilo_enviar_datos_serial = threading.Thread(target=enviar_datos_serial, args=(cola_temp, cola_prom_x, cola_prom_y,cola_prom_z,evento_prom_temp,evento_prom_acc))
hilo_subir_a_nube = threading.Thread(target=subir_a_nube, args=(cola_temp_mqtt, cola_prom_x_mqtt, cola_prom_y_mqtt, cola_prom_z_mqtt, evento_temp_mqtt,evento_acc_mqtt))

hilo_prom_temp.start()
hilo_prom_acc.start()
#hilo_recibir_datos_serial.start()
hilo_enviar_datos_serial.start()
hilo_subir_a_nube.start()

# Espera a que todos los hilos terminen (en este caso, nunca terminarán porque son bucles infinitos)
hilo_prom_temp.join()
hilo_prom_acc.join()
#hilo_recibir_datos_serial.join()
hilo_enviar_datos_serial.join()
hilo_subir_a_nube.join()