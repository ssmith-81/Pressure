#!/bin/bash
python3 pressure_sensor.py &
python3 wind_sensor.py &
python3 force_sensor.py &
wait
