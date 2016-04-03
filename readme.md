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

The base distribution is [Raspbian Lite](https://downloads.raspberrypi.org/raspbian_lite_latest)
(Feb 2016 as I write this). Use `sudo raspi-config` to:

* expand file system
* change the password
* set internationalization options to your preference; we use
    * US locale & keyboard setup
    * year-round Pacific Standard Time (`GMT+8`)
* *advanced options*
    * change the hostname
    * enable SSH (if you use it; you should be using it)

Reboot after exiting then run a complete update:

```
pi@tracer:~ $ sudo apt-get update && sudo apt-get dist-upgrade -y
```

And install some basic programs:

```
pi@tracer:~ $ sudo apt-get install git tmux
```

Now is a good time eliminate tabs. Create the file `~/.nanorc`:

```
set tabsize 4
set tabstospaces
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

Here's our rules file, `/etc/udev/rules.d/98-tracer-release.rules`:

```
KERNEL=="ttyUSB0", SYMLINK+="mfc"
KERNEL=="ttyAMA0", SYMLINK+="co2" 
```

Reboot for rules to take effect. YMMV with other brands of USB
serial adapters. 


#### Software packages

Install python support for the serial ports:

```
pi@tracer:~ $ sudo apt-get install python-serial
```

#### Share data

First, create shared data directories for LI840A

* `sudo mkdir /var/log/li840a`
* `sudo mkdir -p /var/log/li840a/raw` (XML data stream *TODO*)
* `sudo mkdir -p /var/log/li840a/1hz` ("raw" but in TSV)
    * TODO: `.../1min', mean 1-minute values
    * TODO: `.../30min`, mean/sdev/min/max half-hour values
    * TODO: `.../daily`, mean/sdev/min/max daily values
* `sudo mkdir /var/log/tracer`
* `sudo ln -s /var/log/li840a /var/log/tracer/sample`
* `sudo ln -s /var/log/mfc /var/log/tracer/inject`

Now export 

* Install samba: `sudo apt-get install samba -y`
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
pi@tracer:~/2015-iaq-tracer $ sudo cp scripts/co2-logger.py /usr/sbin/co2-logger
pi@tracer:~/2015-iaq-tracer $ sudo cp scripts/mfc-control.py /usr/bin/mfc-control
pi@tracer:~/2015-iaq-tracer $ sudo chmod +x /usr/sbin/co2-logger
pi@tracer:~/2015-iaq-tracer $ sudo chmod +x /usr/bin/mfc-control
```

Now install and enable the co2 logging service:

```
pi@tracer:~/2015-iaq-tracer $ sudo cp etc/systemd/system/co2-logger.service /etc/systemd/system/
pi@tracer:~/2015-iaq-tracer $ sudo systemctl enable co2-logger.service
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


#### Configure serial console for bluetooth dongles

**Ignore this section:**

> In previous release, a Bluetooth serial adapter was used to
> provide shell access via the hardware UART (`/ttyAMA0`). That
> access route has been shelved so the UART can be used with
> paired Bluetooth serial modules to wirelessly record the 
> CO2/H2O analyzer.

We've selected an HC-06 module (linvor1.8) which, unfortunately,
cannot operate above 38400 baud rate. The default serial UART is
115200 so it must be changed.

First, re-enable serial console output via `raspi-config`, if req'd.
Then change instances of '115200' to '19200' in `/boot/cmdline.txt`. 

Since Raspbian Jessie uses systemd, there is no `/etc/inittab` file.

> https://learn.adafruit.com/adafruit-ultimate-gps-hat-for-raspberry-pi/pi-setup
> http://blog.miguelgrinberg.com/post/a-cheap-bluetooth-serial-port-for-your-raspberry-pi



