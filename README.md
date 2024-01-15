# EVCC VenusOS Installer

**DISCLAIMER: This is a proof of concept and bound to change**

This project creates a `venus-data.tar.gz` archive for easy install of the [evcc](https://github.com/evcc-io/evcc) project on a Victron Energy GX device running Venus OS. Within the installation process, it automatically detects and configures all Victron Energy EV Charging Stations connected to the GX device for use with evcc.

## Enable Modbus on the GX device

On your GX device, under *Settings* > *Services* > *Modbus TCP*, turn *Enable Modbus/TCP* on.

## Add your token

In case you have an evcc [sponsorship token](https://docs.evcc.io/en/docs/sponsorship/), you can add it as follows: 
Create a text file called `token.txt` within the `evcc` folder, paste your token string into it (starting with "ey...") and save.

## Create venus-data.tar.gz

Clone the repository and initialize the git submodule:
```sh
git clone https://github.com/philipptrenz/evcc-venusos-installer.git
cd evcc-venusos-installer
git submodule update --init --recursive
```

Now, run `sh build.sh` to load the evcc binary and pack a `venus-data.tar.gz` archive.

## Install evcc on a GX device

Put the `venus-data.tar.gz` archive on an USB stick or SD card, connect it to the GX device and reboot. If you have SSH access, you can alternatively call the script `/etc/init.d/update-data.sh` instead of rebooting.

After another reboot, evcc should get available at port 7070 of your GX device, e.g. [http://venus.local:7070/](http://venus.local:7070/).

## FAQ

### How do I change the evcc version?

Open the `./evcc/version` file and change it to the preferred version, then build and install again.
Please note: For Victron Energy EV Charging Stations to work properly, it requires evcc <= 0.122.1 or > 0.123.8.