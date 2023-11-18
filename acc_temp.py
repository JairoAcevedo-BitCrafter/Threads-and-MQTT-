import time
import board
import busio
import adafruit_adxl34x

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
while True:
    print("%f %f %f" % accelerometer.acceleration)
    temperatura = leer_temperatura()
    if temperatura is not None:
        print(f'{temperatura:.3f}°C')
    else:
        print("Error al leer la temperatura.")
    time.sleep(1)
