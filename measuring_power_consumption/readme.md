Orca does not provide measurement of current power. This guide desribes cheap and reliable way of measuring power using ESP32 with ESPHome and Home Assistant.


### Hardware
- [Three phase inline power meter from aliexpress ~30€](https://www.aliexpress.com/item/32884383998.html)
- ESP32 board, I use esp32-c3 super mini, but any should work.
- Pair of wires

### Wiring

Mount the meter on din rail and connect three phases and neutral wire between breakers and heat pump. Connect the pulse output to ESP32 pin GPIO5 and GND. 

> [!WARNING]
> Polarity of pulse output is important! It will not work if you switch + and -!

<br>

![alt text](pm_schema.png?raw=true "")
### ESPHome config


If you use the same board and pin, then you can use the following ESPHome config.

Don't forget to replace network config and encryption key.

> [!NOTE]
> The config assumes 400 pulses / kW - this is what linked power meter uses. Make sure to recalculate relevant values if your power meter uses different pulse/kW.


```yaml
substitutions:
  devicename: tc_energy_meter

esphome:
  name: ${devicename}
  friendly_name: ${devicename}

esp32:
  board: esp32-c3-devkitm-1 # esp32-c3 super mini
  framework:
    type: esp-idf

logger:
  level: INFO

api:
  encryption:
    key: "xxxxxxxxxxxxxxxxxx"
ota:
 - platform: esphome
   password: !secret wifi_password

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  power_save_mode: HIGH
  fast_connect: true
  manual_ip:
    static_ip: 192.168.xx.xx
    gateway: 192.168.xx.xx
    subnet: 255.255.255.0
    dns1: 192.168.xx.xx
    dns2: 192.168.xx.xx
  ap:
    ssid: ${devicename}
    password: ${password}
    manual_ip:
      static_ip: 192.168.100.2
      gateway: 192.168.100.1
      subnet: 255.255.255.0
      dns1: 8.8.8.8
      dns2: 8.8.4.4

captive_portal:

web_server:
  port: 80

time:
  - platform: homeassistant
    id: homeassistant_time

sensor:
  - platform: pulse_meter
    pin: 
      number: GPIO5
      inverted: true
      mode:
        input: true
        pullup: true
    unit_of_measurement: 'W'
    name: "Power"
    id: power0
    accuracy_decimals: 0
    internal_filter: 10ms # standard pulse is around 30ms according to sources
    internal_filter_mode: PULSE # discards any spikes shorter than 10ms
    timeout: 60min  # If no pulse for 60 minutes, assume 0 W. in reality, this means less than 2.5W

    filters:
      - multiply: 150  # 400 pulses/kW.. 60s/400 * 1000W. Ce bi v kwh, bi bilo 0.15
      # drop impossible power levels
      - lambda: |-
          if (x > 7000.0) {
            return {};
          } else {
            return x;
          }
    total:
      name: "Energy"
      id: energy0
      unit_of_measurement: "kWh"
      accuracy_decimals: 3
      filters:
        - multiply: 0.0025  # 1/400#
  - platform: total_daily_energy
    name: 'Daily Energy'
    power_id: energy0

## Calculate power from pulse period
# P = 3 600 000 / (400 x sekund med impulzi)


# debug/test
#binary_sensor:
#  - platform: gpio
#    pin:
#      number: GPIO5
#      inverted: true
#      mode:
#        input: true
#        pullup: true
#    name: "Power Meter Pulse Debug"

# Kako deluje: power meter ima dva pina, normalno sklenjena. ESP pina drzi na 3.3V (pullup). Pina se razkleneta ob pulzu. Polariteta je pomembna!
```
<br>
<br>

After the ESPHome device is added in Home Assistant, the following entities will be available:

![alt text](entities.png?raw=true "")

<br>

![alt text](graph.png?raw=true "")