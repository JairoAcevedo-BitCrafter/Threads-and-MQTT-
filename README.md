# Threads-and-MQTT-
El código llamado acc_temp.py se encarga de leer ambos sensores sin hilado, a una tasa de 1 segundo. Punto1.py se encarga de leer ambos sensores de forma hilada, también promedia sus resultados a partir de una cantidad de samples controlado por medió de la recepción del valor, del mismo modo los resultados son transmitidos por protocolo Serial.
