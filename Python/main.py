from machine import Pin
import dht
import time

sensor = dht.DHT11(Pin(4))   # DATA connected to GPIO 4

while True:
    sensor.measure()          # Trigger a measurement

    temp = sensor.temperature()
    humidity = sensor.humidity()

    print("Temperature:", temp, "°C")
    print("Humidity:", humidity, "%")

    time.sleep(2)             # Wait at least 1 second before the next reading