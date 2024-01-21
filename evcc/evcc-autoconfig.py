#! /usr/bin/python3 -u

import os
import sys
import dbus

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
        
        self.evcc_hostname = 'evcc.local'
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

        self.chargers = []
        self.loadpoints = []

        self._enable_gx_modbus_server()
        self._find_evchargers()

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
        ve_settings = 'com.victronenergy.settings'
        services = self._bus.list_names()
        if ve_settings in services:
            self._set_dbus_value(ve_settings, '/Settings/Services/Modbus', 1)

    def _switch_ev_charger_to_manual(self, service):
        # Switch to Manual mode, if not already set
        if self._get_dbus_value(service, '/Mode', int) > 0:
            self._set_dbus_value(service, '/Mode', 0)

    def _find_evchargers(self):
        services = self._bus.list_names()

        for service in services:
            if service.startswith('com.victronenergy.evcharger.'):

                if not self._get_dbus_value(service, '/Connected', bool): 
                    continue

                self._switch_ev_charger_to_manual(service)

                unique_name = service.replace('com.victronenergy.evcharger.', '')
                device_instance = self._get_dbus_value(service, '/DeviceInstance', int)
                name = self._get_dbus_value(service, '/CustomName') \
                    or self._get_dbus_value(service, '/ProductName')

                if isinstance(name, dbus.Array):
                    name = name.pop() \
                        or self._get_dbus_value(service, '/ProductName')

                max_current = self._get_dbus_value(service, '/MaxCurrent', int)
                min_current = self._get_dbus_value(service, '/MinCurrent', int, fallback=6)
                num_phases  = self._get_dbus_value(service, '/NrOfPhases', int, fallback=3)

                self.chargers.append({
                    'type': 'template',
                    'template': 'victron',
                    'host': self.gx_modbus_hostname,
                    'port': self.gx_modbus_port,
                    'id': device_instance,
                    'modbus': 'tcpip',
                    'name': unique_name
                })

                self.loadpoints.append({
                    'title': name,
                    'charger': unique_name,
                    'mode': 'pv',
                    'phases': num_phases,
                    'mincurrent': min_current,
                    'maxcurrent': max_current
                })

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
    
    def get_chargers(self):
        return self.chargers
    
    def get_loadpoints(self):
        return self.loadpoints
    
    def get_site(self):
        return {
            'title': self.system_name or "Victron Energy",
            'meters': self.meter_refs
        }
    
    def get_mqtt(self):
        return {
            'broker': self.mqtt_hostname,
            'topic': self.mqtt_topic
        }
    
    def get_interval(self):
        return f"{ self.interval }s"
    
    def get_config(self, config={}):

        config.update({
            'database': {
                'type': 'sqlite',
                'dsn': '/data/evcc/evcc.db'
            },
            'interval': self.get_interval(),
            'network': self.get_network(),
            'mqtt': self.get_mqtt(),
            'meters': self.get_meters(),
            'site': self.get_site(),
        })

        if 'chargers' not in config:
            config['chargers'] = []
        if 'loadpoints' not in config:
            config['loadpoints'] = []

        # if chargers or loadpoints are configured manually, do not auto-detect
        if config['chargers'] or config['loadpoints']:
            chargers = config['chargers']
            loadpoints = config['loadpoints']
        else:
            chargers = self.get_chargers()
            loadpoints = self.get_loadpoints()
    
        config.update({
            'chargers': chargers,
            'loadpoints': loadpoints
        })

        return config

    @staticmethod
    def get(additional_config={}):
        return EvccDbusConfig().get_config(additional_config)

if __name__ == "__main__":

    ADDITIONAL_CONFIG_PATH = os.path.join(app_dir, 'evcc.additional.yaml')
    CONFIG_PATH = os.path.join(app_dir, 'evcc.yaml')

    add_cfg = {}
    if os.path.isfile(ADDITIONAL_CONFIG_PATH):
        with open(ADDITIONAL_CONFIG_PATH, 'r') as f:
            add_cfg = yaml.safe_load(f)

    data = EvccDbusConfig.get(add_cfg)

    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(data, f)