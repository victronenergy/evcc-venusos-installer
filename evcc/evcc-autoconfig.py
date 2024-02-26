#! /usr/bin/python3 -u

import os
import sys
import dbus
import logging


# configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('evcc-autoconfig.py')


app_dir = os.path.dirname(os.path.realpath(__file__))

# Locally installed packages, namingly pyyaml
sys.path.insert(1, os.path.join(app_dir, 'ext'))
EGG_DIR =  os.path.join(app_dir, 'ext')
for filename in os.listdir(EGG_DIR):
    if filename.endswith(".egg"):
        sys.path.insert(2, os.path.join(EGG_DIR, filename))

# Victron packages
sys.path.insert(3, os.path.join(app_dir, 'ext', 'velib_python'))

import yaml
from ve_utils import get_vrm_portal_id, wrap_dbus_value

software_version = '0.1'


class EvccDbusConfig:

    def __init__(self):
        self._bus = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

        self.evcc_hostname = 'venus.local'
        self.evcc_port     = 7070

        self.mqtt_hostname      = '127.0.0.1:1883'
        self.mqtt_topic         = f"N/{ get_vrm_portal_id() }/evcc"

        self.gx_modbus_hostname = '127.0.0.1'
        self.gx_modbus_port     = 502

        self.interval    = 30  # in seconds
        self.system_name = self._get_dbus_value('com.victronenergy.settings', '/Settings/SystemSetup/SystemName')

        self.meter_refs = {
            # usage: name
            'grid': 've-grid',
            'pv': 've-pv',
            'battery': 've-battery'
        }

    def _get_dbus_value(self, service, path, type=str, fallback=None):
        try:
            val = self._bus.call_blocking(service, path, None, 'GetValue', '', [])
        except dbus.exceptions.DBusException:
            val = None
        if isinstance(val, dbus.Array) and len(val) == 0:
            val = None
        return type(val) if val is not None else fallback

    def _set_dbus_value(self, service, path, value):
        value = wrap_dbus_value(value)
        return self._bus.call_blocking(service, path, None, 'SetValue', 'v', [value])

    def _enable_gx_modbus_server(self):
        service = 'com.victronenergy.settings'
        try:
            self._set_dbus_value(service, '/Settings/Services/Modbus', 1)
            logger.info(f"enabled GX Modbus server")
        except:
            logger.exception('enabling GX Modbus server failed')

    def _switch_ev_charger_to_manual(self, unique_name):
        service = 'com.victronenergy.evcharger.' + unique_name
        try:
            self._set_dbus_value(service, '/Mode', 0)
            logger.info(f"switched evcharger ({ unique_name }) to manual mode")
        except:
            logger.exception('setting evcharger to manual mode failed')

    def _find_evchargers(self):
        services = self._bus.list_names()
        chargers = []
        loadpoints = []

        for service in services:
            if service.startswith('com.victronenergy.evcharger.'):

                if not self._get_dbus_value(service, '/Connected', bool):
                    continue

                unique_name = service.replace('com.victronenergy.evcharger.', '')
                device_instance = self._get_dbus_value(service, '/DeviceInstance', int)
                name = self._get_dbus_value(service, '/CustomName') \
                    or self._get_dbus_value(service, '/ProductName')

                if isinstance(name, dbus.Array):
                    name = name.pop() \
                        or self._get_dbus_value(service, '/ProductName')

                logger.info(f"found evcharger '{ name }' ({ unique_name })")

                max_current = self._get_dbus_value(service, '/MaxCurrent', int)
                min_current = self._get_dbus_value(service, '/MinCurrent', int, fallback=6)
                num_phases  = self._get_dbus_value(service, '/NrOfPhases', int, fallback=3)

                chargers.append({
                    'type': 'template',
                    'template': 'victron',
                    'host': self.gx_modbus_hostname,
                    'port': self.gx_modbus_port,
                    'id': device_instance,
                    'modbus': 'tcpip',
                    'name': unique_name
                })

                loadpoints.append({
                    'title': name,
                    'charger': unique_name,
                    'mode': 'pv',
                    'phases': num_phases,
                    'mincurrent': min_current,
                    'maxcurrent': max_current
                })

        return chargers, loadpoints

    def get_network(self):
        return {
            'schema': 'http',
            'host': self.evcc_hostname,
            'port': self.evcc_port
        }

    def get_meters(self):
        meters = []
        for usage, name in self.meter_refs.items():
            meters.append({
                'type': 'template',
                'template': 'victron-energy',
                'usage': usage,
                'host': self.gx_modbus_hostname,
                'port': self.gx_modbus_port,
                'name': name
            })
        return meters

    def get_site(self):
        return {
            'title': self.system_name or "Victron Energy",
            'meters': self.meter_refs,
            'residualPower': 100
        }

    def get_mqtt(self):
        return {
            'broker': self.mqtt_hostname,
            'topic': self.mqtt_topic
        }

    def get_interval(self):
        return f"{ self.interval }s"

    def get_config(self, config:dict={}):

        # add or override, if user-defined
        config.update({
            'database': {
                'type': 'sqlite',
                'dsn': '/data/evcc/evcc.db'
            },
            'mqtt': self.get_mqtt(),
        })

        # add, if not user-defined
        config['interval'] = config.get('interval', self.get_interval())
        config['network']  = config.get('network', self.get_network())
        config['meters']   = config.get('meters', self.get_meters())
        config['site']     = config.get('site', self.get_site())

        # add auto-detected chargers or loadpoints, if not user-defined
        if config.get('chargers', []) or config.get('loadpoints', []):
            config.update({
                'chargers': config['chargers'],
                'loadpoints': config['loadpoints']
            })
        else:
            chargers, loadpoints = self._find_evchargers()
            config.update({
                'chargers': chargers,
                'loadpoints': loadpoints
            })

            for charger in chargers:
                self._switch_ev_charger_to_manual(charger['name'])

        self._enable_gx_modbus_server()

        return config

    @staticmethod
    def get(custom_config={}):
        return EvccDbusConfig().get_config(custom_config)

if __name__ == "__main__":

    logger.info("creating evcc.yaml ...")

    CUSTOM_CONFIG_PATH = os.path.join(app_dir, 'evcc.yaml')
    CONFIG_PATH = os.path.join(app_dir, 'evcc.ve.yaml')

    add_cfg = {}
    if os.path.isfile(CUSTOM_CONFIG_PATH):
        with open(CUSTOM_CONFIG_PATH, 'r') as f:
            add_cfg = yaml.safe_load(f)

    data = EvccDbusConfig.get(add_cfg)

    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(data, f)

    logger.info(f"written config to { CONFIG_PATH }")
