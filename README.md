# EVCC VenusOS Installer

**DISCLAIMER: This is a proof of concept and bound to change**

This project creates a `venus-data.tar.gz` archive for easy installation of the [evcc](https://github.com/evcc-io/evcc) project on a Victron Energy GX device running Venus OS. Within the installation process, it automatically detects and configures all Victron Energy EV Charging Stations connected to the GX device for use with evcc.

## Get the repository

Clone the repository and initialize the git submodule:
```sh
git clone https://github.com/philipptrenz/evcc-venusos-installer.git
cd evcc-venusos-installer
git submodule update --init --recursive
```

## Add your configuration

Copy and rename the file `evcc.dist.yaml` to `evcc.yaml`. Then, add your custom configurations there, like sponsor token, EV charger configurations, etc.

If you are solely using Victron EV Charging Stations connected to your GX device, you only have to add your sponsor token, as `chargers` and `loadpoints` will be automatically added for you before the start of evcc.

Please note the following:
* An error in the configuration will prevent evcc from starting. In this case, the configuration must be corrected and the archive built and installed again (see steps below)
* The entries of `database`, `interval`, `network`, `mqtt`, `meters` and `site` will be overwritten with the correct parameters for your installation, so no need to add them anyways
* If you add entries for `loadpoints` and/or `chargers` to `evcc.yaml`, Victron EV Charging Stations are no longer auto-detected and will also have to be configured manually
* For instructions on how to configure the `evcc.yaml`, please refer to the evcc [documentation](https://docs.evcc.io/en/docs/Home/) and [community](https://github.com/evcc-io/evcc/discussions/)

## Install evcc using a USB stick or SD card

Now, run `sh build.sh` to load the evcc binary and pack a `venus-data.tar.gz` archive.

Put the `venus-data.tar.gz` archive on a USB stick or SD card, connect it to the GX device and reboot the device. If you have SSH access enabled, you can alternatively call the script `/etc/init.d/update-data.sh` instead of rebooting.

After a while, evcc will get available at port `7070` of your GX device, e.g. [http://venus.local:7070/](http://venus.local:7070/).
