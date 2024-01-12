# EVCC VenusOS Installer

This project creates a `venus-data.tar.gz` file for easy install of the [evcc](https://github.com/evcc-io/evcc) project on a Victron Energy GX device running Venus OS. It automatically detects and configures all Victron Energy EV Charging Stations connected to the GX device for use with evcc.

## Enable Modbus on the GX device

On your GX device, under *Settings* > *Services* > *Modbus TCP*, turn *Enable Modbus/TCP* on.

## Add your token

In case you have an evcc [sponsorship token](https://docs.evcc.io/en/docs/sponsorship/), you can add it as follows: 
Create a text file called `token.txt` within the `evcc` folder, paste your token string into it (starting with "ey...") and save.

## Create venus-data.tar.gz

Run `sh build.sh` to load the evcc binary and pack a `venus-data.tar.gz` archive.

## Install evcc on a GX device

Put the `venus-data.tar.gz` archive on an USB stick or SD card, connect it to the GX device and reboot. If you have SSH access, you can alternatively call the script `/etc/init.d/update-data.sh` instead of rebooting.

After the reboot, evcc should get available at port 7070 of your GX device, e.g. [http://venus.local:7070/](http://venus.local:7070/);

## FAQ

### How do I change the evcc version?

Open the `./evcc/version` file and change the contents to the preferred version, then follow the installation instructions above.

## TODOs

* Make the evcc install survive a Venus OS update
