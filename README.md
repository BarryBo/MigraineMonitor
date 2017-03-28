# MigraineMonitor
Migraine Monitor app for Raspberry Pi

Developed on Raspberry Pi 3 with:
- an LED on GPIO 21 (flashes every 5s to indicate the app is running)
- A digital barometric pressure sensor module on i2c
- A button on GPIO 23.  Press this to report the beginning of a migaine

Every 5 seconds, the app records pressure and temperature readings to /home/pi/migraine_pressure_log.txt in CSV format.
A button press is logged to /home/pi/migraine_start_log.txt in CSV format
