#!/bin/bash
pip install pytz pycoingecko dash plotly dash-core-components dash-html-components dash-table
# Run the Python script
python3 display_script.py &

# Wait for the Python script to start the server (adjust the sleep duration as needed)
sleep 120

# Open the Chromium browser to the specific local port (e.g., 8080)
chromium-browser --noerrdialogs --disable-session-crashed-bubble --disable-infobars --kiosk http://localhost:8050 &