Tracer Release
==============

Indoor Air and Climate Change (2015-2017)
-----------------------------------------

Carbon dioxide (CO2) tracer injection/detection for time-resolved indoor
air ventilation rates. Parts include:

* CO2 analyzer (LI-840A; LICOR Biosciences) and accessories (e.g. pump,
  power supply, filters, etc)
* Volumetric mass flow controller (0-20 sLPM; Alicat Scientific) and
  cable for 8-pin interface
* Linux computer (Raspberry Pi B+) plus
    * Paired Bluetooth serial dongles (for CO2 analyzer)
    * USB-serial adapter (for flow controller)
* Enclosure plus cable grommets, hardware, etc


### Usage

***TODO***




### Initial Setup

#### OS Prep

Based on latest [Raspbian Lite](https://downloads.raspberrypi.org/raspbian_lite_latest)
release. Use `sudo raspi-config` to:

* expand file system
* change the password
* set internationalization options to your preference; we use
    * US locale & keyboard setup
    * year-round Pacific Standard Time (`GMT+8`)
* *advanced options*
    * change the hostname
    * enable SSH (optional, recommended)

Reboot after exiting then run a complete update:

```
pi@tracer:~ $ sudo apt-get update && sudo apt-get dist-upgrade -y
```

And install some basic programs:

```
pi@tracer:~ $ sudo apt-get install git
```

#### Hardware setup

The mass flow controller is connected to the Raspberry Pi using a
USB serial (RS-232) adapter. The CO2/H2O analyzer is connected to
the Pi using paired Bluetooth serial dongles (HC-05).

> In the previous release, we created udev rules to assign device
> names to the USB serial adapters based on their physical USB
> port. This was only required because (1) we used two identical
> adapters and (2) the specific adapters we bought are relatively
> poor quality (they do not possess unique serial numbers).
>
> Going forward, the analyzer is connected using paired Bluetooth
> serial modules. Since the modules are 3.3V logic, the receiving
> module is directly connected to the Pi's hardware UART and there
> is no need to assign names based on physical USB port.

> Raspberry Pi 3 users must also restore the GPIO UART -- see
> the following subsection.

Here's our rules file, `/etc/udev/rules.d/98-tracer-release.rules`:

```
KERNEL=="ttyUSB0", SYMLINK+="mfc"
KERNEL=="ttyAMA0", SYMLINK+="co2" 
```

Reboot for rules to take effect. YMMV with other brands of USB
serial adapters.

##### Raspberry Pi 3 UART

On the Pi 3, the UART has been repurposed for Bluetooth features
which means the GPIO pins use the "mini" UART. To restore original
behavior (a la <= Pi 2), we have two options:

* disable bluetooth entirely (also requires disabling the `hciuart`
  service on Raspbian)
* tie bluetooth to the mini-uart (to make it useful, you must
  also set a static CPU freq)

Let's try the first option. Disable hciuart service:

```
sudo systemctl disable hciuart
```

Enable device tree overlay:

```
sudo nano /boot/config.txt
```
```diff
-#dtoverlay=pi3-disable-bt
+dtoverlay=pi3-disable-bt
```

References:

* <http://www.slideshare.net/yeokm1/raspberry-pi-3-uartbluetooth-issues>
* <http://www.briandorey.com/post/Raspberry-Pi-3-UART-Boot-Overlay-Part-Two>


#### Software packages

Install python support for the serial ports:

```
pi@tracer:~ $ sudo apt-get install python-serial
```

#### Share data

First, create shared data directories for LI840A

* `sudo mkdir -p /var/log/li840a/1hz` (raw in TSV)
* `sudo mkdir /var/log/mfc`
* `sudo mkdir /var/log/tracer`
* `sudo ln -s /var/log/li840a /var/log/tracer/sample`
* `sudo ln -s /var/log/mfc /var/log/tracer/inject`

> in preparation for moving all log dirs under `/var/log/tracer`:

* `sudo mkdir /var/log/tracer/typek`

Now export 

* Install samba: `sudo apt-get install samba samba-common-bin -y`
* Modify samba config: `sudo nano /etc/samba/smb.conf`
    * comment out default exports (home, printers)
    * add following:

```
...
unix extensions = no

[data]
   browseable = yes
   comment = Data directory
   create mask = 0700
   directory mask = 0700
   only guest = yes
   path = /var/log/tracer
   public = yes
   read only = yes
   follow symlinks = yes
   wide links = yes
```


#### Setup wifi connection

*Before connecting wifi adapter,* add the following block to 
`/etc/wpa_supplicant/wpa_supplicant.conf`:

```
network={
  ssid="<the SSID we use>"
  psk="<the long password we use>"
}
```


#### Install scripts as services

Copy the scripts to appropriate directory (per the Linux
Filesystem Hierarchy Standard) and drop file extensions.
Then make the files executable.

```
$ cd ~/rpi-co2-tracer
$ sudo cp scripts/co2-logger.py /usr/sbin/co2-logger
$ sudo cp scripts/typek-logger.py /usr/sbin/typek-logger
$ sudo cp scripts/switch-logger.py /usr/sbin/switch-logger
$ sudo cp scripts/mfc-control.py /usr/bin/mfc-control
$ sudo chmod +x /usr/sbin/co2-logger
$ sudo chmod +x /usr/sbin/typek-logger
$ sudo chmod +x /usr/sbin/switch-logger
$ sudo chmod +x /usr/bin/mfc-control
```

Now install and enable the co2 logging service:

```
pi@tracer:~/2015-iaq-tracer $ sudo cp etc/systemd/system/co2-logger.service /etc/systemd/system/
pi@tracer:~/2015-iaq-tracer $ sudo systemctl enable co2-logger.service
```

Also the thermocouple logging service:

```
$ sudo cp /etc/tracer/typek-logger.conf /etc/tracer/
$ sudo cp /etc/systemd/system/typek-logger.service /etc/systemd/system/
$ sudo systemctl enable typek-logger.service
```

Plus the current switch logging service:

```
$ sudo cp etc/tracer/switch-logger.conf /etc/tracer/
$ sudo cp etc/systemd/system/switch-logger.service /etc/systemd/system/
$ sudo systemctl enable switch-logger
```

And finally, setup the mass flow controller script on a timer:

```
pi@tracer:~ $ sudo crontab -e
```
```
...
0 */3 * * * /usr/bin/mfc-control
```

This would run the script every 3 hours, at the start (zeroth
minute) of the hour.


#### Report data to ScadaBR

Run the file `scripts/update-scadabr.py` every minute using cron:

```
$ sudo crontab -e
```
```
...
* * * * * python /full/path/to/the/script
```



