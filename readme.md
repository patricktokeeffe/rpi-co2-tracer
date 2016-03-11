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
    * USB-serial adapter (for CO2 analyzer)
    * USB-serial adapter (for flow controller)
* Enclosure plus cable grommets, hardware, etc


### Usage






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

Both the mass flow controller and CO2 analyzer use RS-232 serial
ports (vs. TTL-style voltages), thus USB serial port adapters are
required. The hardware UART could also be used but it would still
mean converting voltage levels with an intermediate chip so might
as well use matching USB thingies.

> Our mass flow controller cable had tinned bare wire ends so we
> soldered the cable into a female DB9 connector to connect it to
> the USB serial adapter. 

To avoid having a specific order of operations, assign the USB 
serial adapters permanent device names. By default, the adapters
would be named "ttyUSB0" and "ttyUSB1", depending on what order
they are plugged into the Pi -- we don't want that.

Unfortunately, the specific USB adapters [I chose](http://www.amazon.com/gp/product/B00IDSM6BW) 
does not have unique serial numbers programmed so the often
recommended method for assigning persistent names with udev won't
work. Instead, we follow [this Ask Ubuntu answer](http://askubuntu.com/a/50412)
and assign names based on which physical USB port it plugs into.

With the Pi held "upright" (network port left of USB ports), the
mass flow controller USB adapter plugs into the lower-left port and
CO2/H2O analyzer plugs into the lower-right port. Our rules are 
written to the file `/etc/udev/rules.d/98-usb-serial.rules`:

```
# http://askubuntu.com/a/50412
#  lower-left, next to ethernet: Alicat mass flow controller
KERNEL=="ttyUSB*", KERNELS=="1-1.3:1.0", SYMLINK+="mfc"
#  lower-right, away to ethernet: Licor LI840A co2/h2o analyzer
KERNEL=="ttyUSB*", KERNELS=="1-1.5:1.0", SYMLINK+="li840a" 
```

Reboot for rules to take effect. YMMV with other brands of USB
serial adapters. 


#### Software packages

Install utilities and python support for the serial ports:

```
pi@tracer:~ $ sudo apt-get install minicom python-serial
```

The `minicom` package is useful for testing but not required.
`python-serial` is required for interfacing with the CO2/H2O
analyzer and flow controller.

#### Share data

First, create shared data directories for LI840A

* `sudo mkdir /var/log/li840a` (shared as "co2")
* `sudo mkdir /var/log/li840a/raw/xml` (direct from instrument)
* `sudo mkdir /var/log/li840a/raw/tsv` (parsed to daily tab separated files)
* `mkdir /home/pi/data` (shared on network)
* `ln -s /var/log/li840a /home/pi/data/co2-monitor` (add to share)
* `ln -s /var/log/mfc /home/pi/data/co2-injection` (add to share)

Now export 

* Install samba: `sudo apt-get install samba -y`
* Modify samba config: `sudo nano /etc/samba/smb.conf`
    * comment out default exports (home, printers)
    * add following:

```
[data]
   browseable = yes
   comment = Data directory
   create mask = 0700
   directory mask = 0700
   only guest = yes
   path = /home/pi/data
   public = yes
   read only = yes
```


#### Setup wifi connection

*Before connecting wifi adapter,* add the following block to 
`/etc/wpa_supplicant/wpa_supplicant.conf`:

```
network={
  ssid="WSU LAR Indoor AQ"
  psk="the long password we used"
}

> http://thepihut.com/blogs/raspberry-pi-tutorials/83502916-how-to-setup-wifi-on-raspbian-jessie-lite

#### Configure serial console for bluetooth dongles

We've selected an HC-06 module (linvor1.8) which, unfortunately,
cannot operate above 38400 baud rate. The default serial UART is
115200 so it must be changed.

First, re-enable serial console output via `raspi-config`, if req'd.
Then change instances of '115200' to '19200' in `/boot/cmdline.txt`. 

Since Raspbian Jessie uses systemd, there is no `/etc/inittab` file.


> https://learn.adafruit.com/adafruit-ultimate-gps-hat-for-raspberry-pi/pi-setup

> http://blog.miguelgrinberg.com/post/a-cheap-bluetooth-serial-port-for-your-raspberry-pi



