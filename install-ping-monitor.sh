#!/bin/sh

echo "Ping Monitor to toggle relay if no host are pingable"

/usr/bin/install -m 700 -o root ./ping-monitor.py /usr/local/bin/ping-monitor.py
/usr/bin/install -m 644 -o root ./ping-monitor.service /etc/systemd/system/ping-monitor.service
/bin/systemctl daemon-reload
/bin/systemctl enable ping-monitor
/usr/sbin/service ping-monitor restart

echo "Automated backups into /root/pihole-backup"
/usr/bin/install -m 744 -o root -d /root/pihole-backup
cat > /tmp/$$ << EOF
# Backup PiHole every day and delete old backups
0 3 * * * root "cd /root/pihole-backup; /usr/local/bin/pihole -a -t; /usr/bin/find /root/pihole-backup -type f -name 'pi-hole-teleporter_*' -mtime- +150 -exec rm {} \;"
EOF
/usr/bin/install -m 644 -o root /tmp/$$ /etc/cron.d/pihole-backup
echo "To view logs: # journalctl -fu ping-monitor"
