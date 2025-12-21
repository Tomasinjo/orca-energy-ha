import asyncio
from orca_api import OrcaApi

# Define an async main function


async def main():
    # Initialize OrcaApi with your credentials and host
    orca = OrcaApi(username="admin", password="admin", host="192.168.30.160")
    await orca.initialize()
    # await orca.set_value_by_id('hc_desired_day_temp', 20.1)
    # Call sensor_status_all and print the result
    results = await orca.fetch_all()
    for r in results:
        print(r)
    # results = await orca.fetch_by_tags(['2_Temp_prostor_dnevna'])
    # print(orca.available_circuits)


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
