
### How to find tag name 

In order to add new sensor or control to the integration, you have to find tag name and its data type. The easiest and most reliable method is using wireshark and SSH enabled FreeBSD-based firewall (OPNsense, Pfsense). Launch wireshark and set your firewall as an SSH source. Then go to [Moja Orca](https://moja.orca.energy) and go to menu / set the value of interest. Wireshark will display HTTP requests with tags in URL and values in response body.

Another option is to FTP (Filezila or equivalent) to the heat pump and try to find tags in various XML files representing touchscreen user interface (directory workspace/Project/config/). You can't find current values there. It is also quite hard to find relations between tags and UI label. My attempt of parsing is in file [menu_to_field.yaml](menu_to_field.yaml), but it is not reliable.

Example wireshark Orca response after changing "diferenca vklopa" in Moja Orca:
```
0000   02 00 00 00 00 00 00 00 a9 00 00 00 48 54 54 50   ............HTTP
0010   2f 31 2e 31 20 32 30 30 20 4f 4b 0d 0a 43 6f 6e   /1.1 200 OK..Con
0020   74 65 6e 74 2d 74 79 70 65 3a 20 74 65 78 74 2f   tent-type: text/
0030   70 6c 61 69 6e 0d 0a 43 6f 6e 74 65 6e 74 2d 6c   plain..Content-l
0040   65 6e 67 74 68 3a 20 33 35 0d 0a 43 6f 6e 6e 65   ength: 35..Conne
0050   63 74 69 6f 6e 3a 20 63 6c 6f 73 65 0d 0a 44 61   ction: close..Da
0060   74 65 3a 20 53 61 74 2c 20 32 30 20 44 65 63 20   te: Sat, 20 Dec 
0070   32 30 32 35 20 31 39 3a 31 36 3a 35 38 20 47 4d   2025 19:16:58 GM
0080   54 0d 0a 53 65 72 76 65 72 3a 20 30 2e 34 0d 0a   T..Server: 0.4..
0090   0d 0a 23 32 5f 44 69 66 65 72 65 6e 63 61 5f 76   ..#2_Diferenca_v
00a0   6b 6c 6f 70 61 5f 53 56 09 53 5f 4f 4b 0a 31 39   klopa_SV.S_OK.19
00b0   32 09 34 31 0a                                    2.41.
```
Tag name: 2_Diferenca_vklopa_SV
New value: 41   (4.1°C)

<br>


Example wireshark Orca request and response after displaying information in Moja Orca (settings -> INFO):  

```
............GET /cgi/readTags?client=OrcaTouch1172&n=25&t1=2_Temp_Zunanja&t2=2_Poti3&t3=2_Poti4&t4=2_Temp_Zalog&t5=2_Poti5&t6=2_Vklop_C3&t7=2_Vklop_ele_grelca_1&t8=2_Poti1&t9=2_Izrac_temp_TC&t10=2_Vklop_C0&t11=2_Pogoj_maska_pret_stik&t12=2_Rezim_delov_TC&t13=2_PRIKAZ_Reg_temp_vode&t14=2_Preklop_PV1&t15=MK1_IME&t16=2_Temp_Prostora&t17=2_Zahtevana_RF_MK_1&t18=2_Poti2&t19=2_Temp_zelena_MK_1&t20=2_Delovanje_MP1&t21=2_Odstotki_odprtosti_MP1&t22=2_Vklop_C1&t23=MK1_IME%282%29&t24=2_Temp_RF2&t25=2_Zahtevana_RF_MK_2&_=1766273651 HTTP/1.1
User-Agent: Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.132 Safari/537.36
Host: orcaproxy.eskala.eu:8088
Accept: */*
Accept-Language: en-US,en;q=0.5
Cookie: IDALToken=2610cf7af3e652863138712fd3e18ff2


........=...HTTP/1.1 200 OK
Content-type: text/plain
Content-length: 694
Connection: close
Date: Sat, 20 Dec 2025 23:34:17 GMT
Server: 0.4

#2_Temp_Zunanja	S_OK
192	71
#2_Poti3	S_OK
192	421
#2_Poti4	S_OK
192	400
#2_Temp_Zalog	S_OK
192	-9999
#2_Poti5	S_OK
192	-9999
#2_Vklop_C3	S_OK
192	0
#2_Vklop_ele_grelca_1	S_OK
192	0
#2_Poti1	S_OK
192	476
#2_Izrac_temp_TC	S_OK
192	475
#2_Vklop_C0	S_OK
192	1
#2_Pogoj_maska_pret_stik	S_OK
192	1
#2_Rezim_delov_TC	S_OK
192	1
#2_PRIKAZ_Reg_temp_vode	S_OK
192	475
#2_Preklop_PV1	S_OK
192	1
#MK1_IME	S_OK
192	16
#2_Temp_Prostora	S_OK
192	209
#2_Zahtevana_RF_MK_1	S_OK
192	203
#2_Poti2	S_OK
192	226
#2_Temp_zelena_MK_1	S_OK
192	0
#2_Delovanje_MP1	S_OK
192	0
#2_Odstotki_odprtosti_MP1	S_OK
192	0
#2_Vklop_C1	S_OK
192	0
#MK1_IME(2)	S_OK
192	2
#2_Temp_RF2	S_OK
192	-9999
#2_Zahtevana_RF_MK_2	S_OK
192	220
............
```


### How to interpret tag's value
Values are always represented as integers. 

There are three value types:
- boolean (on/off) with values 0 and 1
- float with single decimal represented as whole number (41.5˚C is 415)
- enums where integer represents a string.

There is no reliable way to determine the data type. Easiest is just monitoring values on Moja Orca and compare it with returned value.

### Adding a new sensor or control
While orca_api.py handles fetching and conversion, it requires sensors and controls to be defined in config.yml. Refer to information in the config. If you plan to submit a pull request that adds a circuit-specific tag, than make sure you add the config to both circuits (1 and 2).


### Fetching data for testing
Find older version of orca_api.py in directory [dump_all](dump_all). Add IP of your orca in test.py and choose to fetch all tag's values or just a list of specific tags.

