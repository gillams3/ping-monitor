#!/usr/bin/python3

import subprocess
import sys
import time
import logging
import signal
import RPi.GPIO as GPIO
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration settings for receiving text messages after reset.
ALERT_EMAIL_ADDRESS = "<email address>"
ALERT_EMAIL_PASSWORD = "<email account password>"
ALERT_SMS_GATEWAY = "<mobile server SMS gateway, like your-phone-#@txt.att.net>'
ALERT_SMTP_SERVER_HOST = "<SMTP server for ALERT_EMAIL_ADDRESS>"
ALERT_SMTP_SERVER_PORT = SMTP PORT (like 587)

# Global variables.
RELAY_GPIO = 17 # GPIO pin controlling the relay
LOG_LEVEL = logging.INFO
HOSTS = ["google.com", "8.8.8.8", "8.8.4.4", "208.67.222.222", "208.67.220.220"]
PING_DELAY = 0.1
TOGGLE_DELAY = 5
RESTART_DELAY = 60 * 10
TEST_DELAY = 60 * 5
PING_ATTEMPTS = 5

# Signal handler for graceful exit/restart.
def exitFromSignal(signalNumber, stack):
    logging.error("Interrupted by signal %d", signalNumber)
    sys.exit(0)

# Signal handler for toggling the relay.
def toggleRelayFromSignal(signalNumber, stack):
    logging.warning("Toggling power from signal %d", signalNumber)
    toggleRelay(TOGGLE_DELAY)
    logging.warning("Power toggled from signal %d", signalNumber)

# Turn on the relay (change it from closed to open).
def turnRelayOn():
    GPIO.output(RELAY_GPIO, GPIO.LOW)

# Turn off the relay (change it from open to closed).
def turnRelayOff():
    GPIO.output(RELAY_GPIO, GPIO.HIGH)

# Release GPIO access.
def cleanup():
    # Make sure the relay is turned on before cleaning up.
    turnRelayOn()
    GPIO.cleanup()

# Close and open the relay with a delay in between.
def toggleRelay(delay):
    logging.error("Toggling power for %d seconds", delay)
    turnRelayOff()
    time.sleep(delay)
    turnRelayOn()
    logging.error("Waiting for modem to restart") 

# Determine of a host is pingable. Return 1 if so or 0 if not.
def pingHost(host):
  cmd = "/bin/ping -c 1 -W 2 " + host
  try:
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
  except subprocess.CalledProcessError:
    logging.warning("%s not reachable", host)
    return 0
  else:
    logging.debug("%s reachable", host)
  return 1

# Ping a list of host and return the precentage which are pingable.
def pingHosts(hostList, pingDelay, pingAttempts):
    pings = 0
    for attempt in range(0, pingAttempts):
        for host in hostList:
            pings += pingHost(host)
            time.sleep(pingDelay)
    pingRate = int(100 * (pings / float(pingAttempts * len(hostList))))
    if pingRate == 0:
        logging.error("Ping success rate %d%%, internet is UNREACHABLE!", pingRate)
    elif pingRate < 100:
        logging.warning("Ping success rate %d%%, internet connectivity issues detected", pingRate)
    else:
        logging.info("Ping success rate %d%%, internet is reachable", pingRate)
    return pingRate

def sendInternetReachableMessage(downTimestamp, upTimestamp):
    # Start our email server and login
    server = smtplib.SMTP(ALERT_SMTP_SERVER_HOST, ALERT_SMTP_SERVER_PORT)
    server.starttls()
    server.login(ALERT_EMAIL_ADDRESS, ALERT_EMAIL_PASSWORD)

    # Now we use the MIME module to structure our message.
    msg = MIMEMultipart()
    msg['From'] = ALERT_EMAIL_ADDRESS
    msg['To'] = ALERT_SMS_GATEWAY
    # Make sure you add a new line in the subject and body
    msg['Subject'] = "Internet Ping Monitor\n"
    body = "Internet connectivity lost at " + "{:%Y-%b-%d %H:%M:%S}".format(downTimestamp) + " and restored at " + "{:%Y-%b-%d %H:%M:%S}".format(upTimestamp) + "\n"
    msg.attach(MIMEText(body, 'plain'))

    # Send the email (SMS) and logout of the server
    server.sendmail(ALERT_EMAIL_ADDRESS, ALERT_SMS_GATEWAY, msg.as_string())
    server.quit()

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            # -debug to change the logging level.
            if sys.argv[1] == "-debug":
                LOG_LEVEL = logging.DEBUG
            # -test to force a failure.
            elif sys.argv[1] == "-test":
                LOG_LEVEL = logging.DEBUG
                HOSTS = ["google.comx", "apple.comx"]
                RESTART_DELAY = 10
                TEST_DELAY = 5
                PING_ATTEMPTS = 1

        # Set logging format.
        # To view the logs use "journalctl -fu ping-monitor"
        logging.basicConfig(format='%(levelname)s:%(message)s', level=LOG_LEVEL)
        logging.debug("Ping monitor starting")

        # Setup GPIO access.
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY_GPIO, GPIO.OUT, initial=GPIO.LOW)

        # Install signal handlers for clean exit/restart and manual relay toggling.
        signal.signal(signal.SIGTERM, exitFromSignal)
        signal.signal(signal.SIGINT, exitFromSignal)
        signal.signal(signal.SIGHUP, toggleRelayFromSignal)
        signal.signal(signal.SIGUSR1, toggleRelayFromSignal)
        signal.signal(signal.SIGUSR2, toggleRelayFromSignal)

        # The time the internet was not reachable.
        downTimestamp = None

        while True:
            # Reset the testing delay. It could have been changed if all host are not pingable.
            testDelay = TEST_DELAY
            pingRate = pingHosts(HOSTS, PING_DELAY, PING_ATTEMPTS)
            # If no host can be pinged, toggle the relay to reboot the modem.
            if pingRate == 0:
                # If this is the first detection of the internet not being reachable, save the current time.
                if downTimestamp == None:
                    downTimestamp = datetime.datetime.now()
                toggleRelay(TOGGLE_DELAY)
                # Adjust the delay time to allow the modem to reboot and reconnect.
                testDelay = RESTART_DELAY
            else:
                # If the internet just became reachable, then send an alert.
                if downTimestamp != None:
                    sendInternetReachableMessage(downTimestamp, datetime.datetime.now())
                    downTimestamp = None

            time.sleep(testDelay)
    except:
        logging.warning("Ping monitor terminating")

    finally:
        cleanup()
