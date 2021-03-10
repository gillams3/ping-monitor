#!/bin/sh

echo "Ping Monitor to toggle relay if no host are pingable"

/usr/bin/install -m 700 -o root ./ping-monitor.py /usr/local/bin/ping-monitor.py
/usr/bin/install -m 644 -o root ./ping-monitor.service /etc/systemd/system/ping-monitor.service
/bin/systemctl daemon-reload
/bin/systemctl enable ping-monitor
/usr/sbin/service ping-monitor restart

echo "To view logs: # journalctl -fu ping-monitor"
