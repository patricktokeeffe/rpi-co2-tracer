#!/bin/bash

mkdir -p /etc/tracer

# Licor CO2/H2O analyzer
echo "Installing CO2/H2O analyzer logging service..."
cp scripts/co2-logger.py /usr/sbin/co2-logger
chmod +x /usr/sbin/co2-logger
cp etc/tracer/co2-logger.conf /etc/tracer/

echo "Registering service..."
cp etc/systemd/system/co2-logger.service /etc/systemd/system/

echo "Enabling start at boot..."
systemctl enable co2-logger.service

echo "Starting service..."
systemctl restart co2-logger.service


# mass flow control routine
echo "Installing mass flow controller script..."
cp scripts/mfc-control.py /usr/sbin/mfc-control
chmod +x /usr/sbin/mfc-control
cp etc/tracer/mfc-control.conf /etc/tracer/


# thermocouple logger
echo "Installing thermocouple logging service..."
cp scripts/typek-logger.py /usr/sbin/typek-logger
chmod +x /usr/sbin/typek-logger
cp etc/tracer/typek-logger.conf /etc/tracer/

echo "Registering service..."
cp etc/systemd/system/typek-logger.service /etc/systemd/system/

echo "Enabling start at boot..."
systemctl enable typek-logger.service

echo "Starting service..."
systemctl restart typek-logger.service


# current switch logger
echo "Installing current switch logging service..."
cp scripts/switch-logger.py /usr/sbin/switch-logger
chmod +x /usr/sbin/switch-logger
cp etc/tracer/switch-logger.conf /etc/tracer/

echo "Registering service..."
cp etc/systemd/system/switch-logger.service /etc/systemd/system/

echo "Enabling start at boot..."
systemctl enable switch-logger.service

echo "Starting service..."
systemctl restart switch-logger.service


echo "Performing clean-up..."
echo "Done."

