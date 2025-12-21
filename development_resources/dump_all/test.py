import asyncio
from orca_api import OrcaApi
import json

async def main():

    orca = OrcaApi(username="admin", password="admin", host="HP IP")
    await orca.initialize()

    # Dump all
    #for s in await orca.sensor_status_all():
    #    print(f'{s.name}: {s.value}')

    # fetch one or more
    for s in await orca.sensor_status_by_tag(["2_Temp_Zunanja", "2_Poti3"]):
        print(f'{s.name}: {s.value}')
if __name__ == "__main__":
    asyncio.run(main())
