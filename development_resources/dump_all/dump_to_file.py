from orca_api import OrcaApi
from datetime import datetime

HARDCODED_HOST_IP = ""  # Set IP here to skip prompt, e.g. "192.168.1.100"


def main():
    host = HARDCODED_HOST_IP or input("Enter device IP address: ").strip()

    orca = OrcaApi(username="admin", password="admin", host=host)
    orca.initialize()

    # Dump all (prints raw response directly)
    raw_data = orca.sensor_status_all()

    # Save raw data to file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"development_resources/dump_all/tag_dump_{timestamp}.txt"
    with open(filename, "w") as f:
        f.write(raw_data)
    print(f"Raw data saved to {filename}")

    # fetch one or more (prints raw response directly)
    # orca.sensor_status_by_tag(["2_Temp_Zunanja", "2_Poti3"])

    # set tag (prints raw response directly)
    # orca.set_value("2_Max_moc_TC_pri_SV", "38")


if __name__ == "__main__":
    main()
