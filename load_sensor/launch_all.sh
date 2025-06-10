#!/bin/bash
python3 ble_server_with_one_client_2.py &
python3 windsensor.py &
python3 force_sensor.py &
wait
