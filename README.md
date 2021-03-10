# ping-monitor
Toggle the signal on a relay to toggle the relay

# Intro
This was developed to run as a service on a Raspberry Pi connected to a relay which in turn is connect to power cord (via the normally connected side of the relay).
The program constantly monitors for internet access via ping.
If no internet access is deceted, then the relay is toggled for a few senconds and connectivity monitoring is delayed for a number of minutes.

The intent is to connect a cable or DSL modem to the power cord.

# Installation
This was developed on the DietPi Linux distro. The script _install-ping-monitor.sh_ should install and start the service.

# Customization
When an internet outage is detected and restored, the service will send a text message.
This is done by sending an email to your phone providers SMS gateway.
To configure this set the five _ALERT*_ variables near the top of the ping-monitor.py script.
