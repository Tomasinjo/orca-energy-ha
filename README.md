## Home Assistant integration with Orca Energy 
Home Assistant Integration for Orca Energy Heat Pump. It was only tested with Duo 200 with Floor Heating and Mono with radiators.

## Requirements
Orca Heat Pump should be accessible via network by HA. First test your access by connecting to http://{ip_addr_of_orca_hp}. You should see login prompt. Try default admin/admin credentials, it should let you in.

## Installation
1. Add Integration  
    A.  When using HACS add this repository as custom repository by opening HACS, select Integrations, press the three dots in the upper right corner, select Custom Repositories and add https://github.com/Tomasinjo/orca-energy-ha as new repository. Install it by pressing button right button "Explore & Download Repositories", search for "orca" and select "Orca Engery Heat Pump".

    B.  Without HACS, copy folder orca-ha to your custom_components directory, which is usually located in /config directory.

2. Go to Settings -> Devices & Services -> + Add Integration -> Search for "Orca".
Configure integration using admin/admin, and domain name or IP address of Orca Heat Pump.

## Changing Sensors and Binary Sensors
Everything in config.yml will be added as entity. If type is set to "boolean", it will become binary sensor, else normal sensor. I managed to dump all field names (a.k.a tags) from heat pump. They are available in "others/all_fields.txt" and can be added to config.yml if you know the type and unit.