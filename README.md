# air-quality-rpi5
Small project for displaying air quality from indoor and outdoor providers using a raspberry pi 5 and the ST7735 display.

# How to install

Create a virtual environment 

`python -m venv myenv`

Activate the virtual environment

`source myenv/bin/activate  # On Windows: myenv\Scripts\activate`

Run `pip install -r requirements.txt` to install the dependencies in the virtual environment.

Add script to crontab

Run `crontab -e` and add the following line to the crontab:

`@reboot /bin/sleep 15 && cd /path/to/air-quality-rpi5 && /path/to/air-quality-rpi5/.venv/bin/python3 /path/to/air-quality-rpi5/start.py &`
