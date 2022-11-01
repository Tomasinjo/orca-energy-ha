## Home Assistant integration with Orca Energy 

This is early preview of integration. There is still lots of polishing to do as well as figuring out what some of the values mean. It was only tested with heat pump Orca Energy Duo 200 with Floor Heating, and two outlets for Hot Water. 

## Requirements
Orca Heat Pump should be accessible via network by HA. First test your access by connecting to http://{ip_addr_of_orca_hp}. You should see login prompt. Try default admin/admin credentials, it should let you in.

## Installation
For now, just copy folder orca-ha to your custom_components directory and go to Settings -> Devices & Services -> + Add Integration -> Search for "Orca"

Now configure integration using admin/admin, and domain or IP address of Orca Heat Pump. That is it, around 20 entities should be added - Climate, Sensors and Binary Sensors

## Changing Sensors and Binary Sensors
For now, everything in config.yml will be added as entity. If type is set to "boolean", it will become binary sensor, else normal sensor. I managed to dump all field names (a.k.a tags) from heat pump. They are available in "others/all_fields.txt" and can be added to config.yml if you know the type and unit.