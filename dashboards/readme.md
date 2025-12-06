
### How to install dashboards:

1. Install [mini-graph-card](https://github.com/kalkih/mini-graph-card) and [mushroom cards](https://github.com/piitaya/lovelace-mushroom/tree/main)
2. Create two template sensors by adding the following to your configuration.yml:

```
template:
    binary_sensor:
      - name: "HP Water Heater Running"
        state: "{{ is_state('sensor.hp_current_state', 'heating') and is_state('sensor.hp_position_of_3_way_valve', 'hot_water') }}"
      - name: "HP Floor Heater Running"
        state: "{{ is_state('sensor.hp_current_state', 'heating') and is_state('sensor.hp_position_of_3_way_valve', 'floor_heating') }}"
```
Those are for red strips indicating that the heat pump is running.


3. Restart Home Assistant

4. In Home Assistant, go to Overview, click pencil at top right corner and click tripple dots. Select "Raw configuration editor".

Scroll down to bottom and paste either English or Slovenian version. It will appear as tab "Orca".
