# EVCC VenusOS Installer

**DISCLAIMER: This is a proof of concept and bound to change**

This project creates a `venus-data.tar.gz` archive for easy installation of the [evcc](https://github.com/evcc-io/evcc) project on a Victron Energy GX device running Venus OS. Within the installation process, it automatically detects and configures all Victron Energy EV Charging Stations connected to the GX device for use with evcc.

**Please note:** Currently, when evcc is used together with a Victron EV Charging Station, it will overrule any manual input from the GX device, VRM portal or even from the web interface and the display of the EV Charging Station itself. We are working on making it possible to enable and disable evcc from the GX device in order to restore manual control.

## Get the repository

Clone the repository and initialize the git submodule:
```sh
git clone https://github.com/victronenergy/evcc-venusos-installer.git
cd evcc-venusos-installer
git submodule update --init --recursive
```

## Add your configuration

If you have a Victron system together with an Victron Energy EV Charging Station, you can skip this step, as your EVCS is automatically detected when evcc starts.

Otherwise, copy and rename the file `evcc.dist.yaml` to `evcc.yaml`. Then, add your custom configurations there, like sponsor token, EV charger configurations, etc.

Please note the following:
* An error in the configuration will prevent evcc from starting – In this case, the configuration must be corrected and the archive built and installed again (see steps below)
* On evcc startup, the entries for `database` and `mqtt` will always be replaced with the correct parameters for the GX device
* The entries for `interval`, `network`, `meters`, `site`, `chargers` and `loadpoints` will be added automatically on evcc startup, as long as they are not already present in your `evcc.yaml`
* If you add `loadpoints` and/or `chargers` to `evcc.yaml`, Victron Energy EV Charging Stations are no longer auto-detected and will also have to be configured manually

For general instructions on how to configure `evcc.yaml`, please refer to the evcc [documentation](https://docs.evcc.io/en/docs/Home/) and [community](https://github.com/evcc-io/evcc/discussions/).

## Install evcc using a USB stick or SD card

Now, run the following command to load the evcc binary and pack a `venus-data.tar.gz` archive:

```sh
sh build.sh
```

Put the `venus-data.tar.gz` archive on a USB stick or SD card, connect it to the GX device and reboot the device.

After some seconds, evcc will get available at port `7070` of your GX device, e.g. [http://venus.local:7070/](http://venus.local:7070/).

Please don't forget to remove the USB stick after the installation process.

## Frequently Asked Questions (FAQs)

### How to disable the evcc service?

We are working on controls via the user interface of the GX device. Until then, this must be done via SSH by executing `/data/evcc/down` to disable and `/data/evcc/up` for re-enabling it.

### How to uninstall evcc?

Actually, it should be enough to delete the folder `/data/evcc` and the symlink `/service/evcc`. And then restart venus-OS.
Of course, exit with `/data/evcc/down` first.
You may also need to remove the evcc entries from `/data/rc.local` and delete the `/data/.evcc_disabled` file that may be present.

```
/data/evcc/down
rm -r /service/evcc
rm -r /data/evcc
rm -f /data/.evcc_disabled
reboot
```

### How do I install a newer version of evcc using the script?

Just adjust the `/evcc/version` file und run the script.

### How to update via ssh?

Everything should be done from your home directory (`cd ~`) to avoid errors:
- stop evcc (`/data/evcc/down`)
- download the latest evcc package (`wget https://github.com/evcc-io/evcc/releases/download/x.xxx.x/evcc_x.xxx.x_linux-armv6.tar.gz`)
- unpack the  archive (`tar xzf evcc_x.xxx.x_linux-armv6.tar.gz`)
- copy evcc (`cp evcc /data/evcc/`)
- delete the downloaded files (`rm evcc*`) - make sure there are no other files named evcc before doing this (`ls -n`) ...
- start evcc (`/data/evcc/up`)

### How to edit evcc.yaml via ssh?

Just login and then `nano /data/evcc/evcc.yaml`, then you have to restart evcc (`/data/evcc/down` & `/data/evcc/up`).
The required evcc.ve.yaml will then be recreated automatically.
