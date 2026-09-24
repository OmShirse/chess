# MicroPython ESP8266

## mpremote (PC ↔ chip)

```bash
mpremote connect /dev/ttyUSB0                  # open REPL
mpremote connect /dev/ttyUSB0 run script.py     # run once, no save
mpremote connect /dev/ttyUSB0 fs cp local.py :main.py   # upload as main.py (auto-run on boot)
mpremote connect /dev/ttyUSB0 fs ls             # list files on chip
mpremote connect /dev/ttyUSB0 fs cat main.py    # print file content
mpremote connect /dev/ttyUSB0 fs rm main.py     # delete file
mpremote connect /dev/ttyUSB0 reset             # soft reset chip
```

Inside REPL:
- `Ctrl+C` — stop running program
- `Ctrl+D` — soft reset
- `Ctrl+E` — paste mode (for multi-line blocks), `Ctrl+D` to execute
- `Ctrl+]` or `Ctrl+X` — exit mpremote session

---

## GPIO — `machine.Pin`

```python
from machine import Pin

led = Pin(2, Pin.OUT)        # set pin 2 as output
led.value(1)                 # HIGH
led.value(0)                 # LOW
led.on()                     # HIGH (shortcut)
led.off()                    # LOW (shortcut)
led.value(not led.value())   # toggle

btn = Pin(0, Pin.IN, Pin.PULL_UP)   # input w/ pull-up
btn.value()                  # read state (0 or 1)
```

Note: onboard LED (GPIO2) usually **active-low** on NodeMCU/Wemos D1 Mini — `off()` may light it.

---

## Timing — `time`

```python
import time

time.sleep(1)          # seconds
time.sleep_ms(500)     # milliseconds
time.sleep_us(100)     # microseconds
time.ticks_ms()        # ms counter since boot
time.ticks_diff(a, b)  # safe diff between tick values
```

---

## PWM — `machine.PWM`

```python
from machine import Pin, PWM

pwm = PWM(Pin(2))
pwm.freq(1000)      # Hz
pwm.duty(512)        # 0-1023 range
pwm.deinit()          # stop PWM
```

---

## ADC — `machine.ADC` (ESP8266: single pin, A0, 0-1V range)

```python
from machine import ADC

adc = ADC(0)
adc.read()   # returns 0-1023
```

---

## I2C

```python
from machine import Pin, I2C

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
i2c.scan()                        # list connected device addresses
i2c.writeto(addr, b'\x00\x01')
i2c.readfrom(addr, 2)
```

---

## UART

```python
from machine import UART

uart = UART(0, baudrate=9600)
uart.write('hello\n')
uart.read()
```

---

## WiFi — `network`

```python
import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('SSID', 'PASSWORD')
wlan.isconnected()     # True/False
wlan.ifconfig()         # (ip, mask, gateway, dns)
wlan.disconnect()

# Access point mode
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='ESP-AP', password='12345678')
```

---

## Sockets — basic web server

```python
import socket

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

while True:
    cl, addr = s.accept()
    request = cl.recv(1024)
    cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<h1>Hello</h1>')
    cl.close()
```

---

## File system

```python
import os

os.listdir()          # list files
os.remove('file.py')
os.rename('a.py', 'b.py')
os.mkdir('data')
```

---

## Deep sleep / power

```python
import machine

machine.deepsleep(10000)   # sleep 10 sec (ms), resets on wake
machine.reset()             # hard reset
machine.reset_cause()       # why last reset happened
```

---

## Common gotchas

- `main.py` on chip = auto-runs on every boot/reset. `boot.py` runs before it (use for WiFi setup, etc).
- GPIO16 has no interrupt/PWM support (different from other pins).
- Flash size limited (~1MB usable on ESP8266) — avoid large libraries.
- Blocking loops without `time.sleep()` can starve WiFi stack — keep loops light.