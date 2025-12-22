from orca_api import OrcaApi
import json

def main():

    orca = OrcaApi(username="admin", password="admin", host="192.168.30.160")
    orca.initialize()

    # Dump all (prints raw response directly)
    orca.sensor_status_all()

    # fetch one or more (prints raw response directly)
    #orca.sensor_status_by_tag(["2_Temp_Zunanja", "2_Poti3"])

    # set tag (prints raw response directly)
    #orca.set_value("2_Max_moc_TC_pri_SV", "38")

if __name__ == "__main__":
    main()
