import asyncio
from orca_api import OrcaApi


async def main():
    orca = OrcaApi(username="admin", password="admin", host="192.168.30.160")
    await orca.initialize()

    # await orca.set_value_by_id("hc_desired_day_temp_1", 20.4)

    # results = await orca.fetch_all()
    # for r in results:
    #    print(r)

    # results = await orca.fetch_by_tags(["2_Temp_prostor_dnevna"])
    # print(results.get("2_Temp_prostor_dnevna").config)


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
