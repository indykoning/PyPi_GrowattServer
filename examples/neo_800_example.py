import datetime
import getpass
import os
from time import sleep

# Use system's certificate store
# if your system complains about SSL issues, run `pip install truststore` and uncomment following lines
# import truststore
# truststore.inject_into_ssl()

import growattServer  # noqa: E402
from growattServer import (  # noqa: E402
    Timespan,
    TlxDataTypeNeo,
    LanguageCode,
)

"""
This script will show all data available in the ShinePhone Android App (version 2025-01-31) for a NEO 800M-X
Network calls have been sniffed using BlueStack and HTTP-Toolkit
"""


def miniplot(
    key_value_dict: dict,
    rows_to_plot: int = 6,
    max_width: int = 80,
    prefix: str = "| ",
):
    """hacky function to plot an ascii chart"""
    if not key_value_dict:
        print(f"|  ↑")
        print(f"|  │  no data to plot")
        print(f"|  │")
        print(f"|  └───────────────────→")
        return

    key_value = {k: float(v) for k, v in key_value_dict.items()}
    x_min, x_max = min(key_value.keys()), max(key_value.keys())
    y_max = max(key_value.values())
    tuples = sorted(key_value.items())
    step = (len(key_value) * 3) // max_width + 1
    print(f"{prefix} ↑")
    for row in range(rows_to_plot, 0, -1):
        row_string = f"{prefix} │ "
        range_start = (y_max / rows_to_plot) * (row - 1)
        range_end = (y_max / rows_to_plot) * row
        for x, y in tuples[::step]:
            if (y <= 0) or (y < range_start):
                row_string += "   "
            elif y >= range_end - ((range_end - range_start) / 2):
                row_string += " | "
            else:
                row_string += " . "
        print(row_string)
    print(f"{prefix} └" + "─" * (len(key_value) // step) * 3 + "──→")
    print(f"{prefix} {x_min} " + " " * (len(key_value) // step) + "..." + " " * (len(key_value) // step) + f"{x_max}")
    return


"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> User data input - query for username and password
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""

# Prompt user for username (if not in environment variables)
USER_NAME = os.environ.get("GROWATT_USER") or input("Enter username:")

# Prompt user to input password (if not in environment variables)
PASSWORD = os.environ.get("GROWATT_PASS") or getpass.getpass("Enter password:")

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> Login to Growatt server API
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""

api = growattServer.GrowattApi(
    add_random_user_id=True,
    agent_identifier=os.environ.get("GROWATT_USERAGENT"),  # use custom user agent if defined
)

login_response = api.login_v2(USER_NAME, PASSWORD)

# remember plant id as we will use it in following requests
PLANT_ID = (login_response.get("data") or [{}])[0].get("plantId")

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Dashboard
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
# get weather data
weather_dict = api.weather(language="de")

# get dashboard energy values
dashboard_energy_dict = api.plant_energy_data_v2(language_code=LanguageCode.de)

# get chart data
# get chart data - tab "Power|Energy"
dashboard_energy_chart = api.plant_energy_chart(
    timespan=Timespan.month,  # daily values
    # timespan=Timespan.year,   # monthly values
    # timespan=Timespan.total,  # yearly values
    date=datetime.date.today(),
)
# get chart data - tab "Power comparison"
dashboard_energy_chart_comparison = api.plant_energy_chart_comparison(
    timespan=Timespan.year,  # monthly values
    # timespan=Timespan.total,  # quarterly values
    date=datetime.date.today(),
)

sunshine_time = datetime.datetime.strptime(weather_dict["basic"]["ss"], "%H:%M") - datetime.datetime.strptime(
    weather_dict["basic"]["sr"], "%H:%M"
)
online_status = ", ".join(
    [f"{k.replace('Num', '').capitalize()}: {v}" for k, v in dashboard_energy_dict["statusMap"].items() if v > 0]
)

# prepare data for miniplot
plot_energy_chart = dashboard_energy_chart["chartData"]
plot_dashboard_energy_chart_comparison = {}
for k, v in dashboard_energy_chart_comparison["chartData"].items():
    plot_dashboard_energy_chart_comparison[f"{k}_0"] = v[0]
    plot_dashboard_energy_chart_comparison[f"{k}_1"] = v[1]

print('\nTab "Dashboard":')
print(
    f"""
+=================================================================================+
|                              Dashboard                                          |
+=================================================================================+
| [{weather_dict["now"]["cond_code"]}] {weather_dict["now"]["cond_txt"]}, {weather_dict["now"]["tmp"]}°C
+---------------------------------------------------------------------------------+
| Daily power generation: {dashboard_energy_dict['todayValue']} {dashboard_energy_dict['todayUnit']}
| Month:                  {dashboard_energy_dict['monthValue']} kWh
| Total:                  {dashboard_energy_dict['totalValue']} kWh
| Current Power:          {dashboard_energy_dict['powerValue']} W
+---------------------------------------------------------------------------------+
| Daily Revenue:   {dashboard_energy_dict['todayProfitStr']}
| Monthly Revenue: {dashboard_energy_dict['monthProfitStr']}
| Total:           {dashboard_energy_dict['totalProfitStr']}
+---------------------------------------------------------------------------------+
| PV capacity           {dashboard_energy_dict['nominalPowerValue']:0.0f} Wp
| Power station status: {online_status}
| Alarm:                {dashboard_energy_dict['alarmValue']}
+---------------------------------------------------------------------------------+
| Power|Energy
|  [DAY][MONTH][YEAR]      [2025]
""".strip()
)
miniplot(plot_energy_chart)
print(
    f"""
+---------------------------------------------------------------------------------+
| Power comparison
|  [MONTH][QUARTER]        [2025]
""".strip()
)
miniplot(plot_dashboard_energy_chart_comparison)
print(
    f"""
+---------------------------------------------------------------------------------+
| CO2 reduced:           {dashboard_energy_dict["formulaCo2Vlue"]} kg
| Standard coal saved:   {dashboard_energy_dict["formulaCoalValue"]} kg
| Deforestation reduced: {dashboard_energy_dict["treeValue"]}
+---------------------------------------------------------------------------------+
| [{weather_dict["now"]["cond_code"]}]
| {weather_dict["city"]}
| {weather_dict["now"]["cond_txt"]}, {weather_dict["now"]["tmp"]}°C
| Wind direction:     {weather_dict["now"]["wind_dir"]}
| Wind speed:         {weather_dict["now"]["wind_spd"]} km/h
| Sunrise:            {weather_dict["basic"]["sr"]}
| Sunset:             {weather_dict["basic"]["ss"]}
| Length of sunshine: {sunshine_time.total_seconds() // 60 // 60:0.0f}h{sunshine_time.total_seconds() // 60 % 60:02.0f}min
+=================================================================================+
| (*Dashboard*)          ( Plant )          ( Service )          ( Me )           |
+=================================================================================+
""".lstrip()
)

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
# get basic plant energy data
plant_energy_dict = api.plant_energy_data(plant_id=PLANT_ID, language_code=LanguageCode.de)

# get inverter list data
plant_info_dict = api.plant_info(plant_id=PLANT_ID, language="de")
inv_dict = plant_info_dict["invList"][0]

# get Power|Energy chart
plant_power_chart_dict = api.plant_power_chart(
    plant_id=PLANT_ID,
    timespan=Timespan.day,
    # timespan=Timespan.month,
    # timespan=Timespan.year,
    # timespan=Timespan.total,
    date=datetime.date.today(),
)

device_status_mapper = {
    "-1": "Disconnected",
    "0": "Standby",
    "1": "Online",
    "2": "Off Grid",
    "3": "Fault",
    "4": "Maintenance",
    "5": "Checking",
}

print('\nTab "Plant":')
print(
    f"""
+=================================================================================+
|                                {plant_energy_dict['plantBean']['plantName']}
+=================================================================================+
|  (#) Panel view   (#) Panel data
| Address:           {plant_energy_dict['plantBean']['plantAddress']}
| PV capacity:       {plant_energy_dict['plantBean']['nominalPower']} Wp
| Installation date: {plant_energy_dict['plantBean']['createDateText']}
+---------------------------------------------------------------------------------+
| [{plant_energy_dict['weatherMap']['cond_code']}] {plant_energy_dict['weatherMap']['cond_txt']}, {float(plant_energy_dict['weatherMap']['tmp']):0.1f}°C
| Today:                  {float(plant_energy_dict['todayValue']):5.1f} kWh
| Generation this month:  {float(plant_energy_dict['monthValue']):5.1f} kWh
| Total power generation: {float(plant_energy_dict['totalValue']):5.1f} kWh
+---------------------------------------------------------------------------------+
| Current Power: {plant_energy_dict['powerValue']} W
+---------------------------------------------------------------------------------+
| Power|Energy
|  [Hour] [DAY] [MONTH] [YEAR]
|     (<) {datetime.date.today()} (>)
""".strip()
)
miniplot(plant_power_chart_dict)
print(
    f"""
+---------------------------------------------------------------------------------+
| My device list >
| {inv_dict['deviceAilas'] or inv_dict['deviceSn']}              {device_status_mapper.get(inv_dict['deviceStatus'], "Unknown")}
| Power:       {float(inv_dict['power']):4.0f} W     Today: {inv_dict['eToday']} kWh
| Data logger: {inv_dict['datalogSn']}
+---------------------------------------------------------------------------------+
| CO2 reduced:           {plant_energy_dict['formulaCo2Vlue']} kg
| Coal saved:            {plant_energy_dict['formulaCoalValue']} kg
| Deforestation reduced: {plant_energy_dict['treeValue']}
+=================================================================================+
| ( Dashboard )          (*Plant*)          ( Service )          ( Me )           |
+=================================================================================+
""".lstrip()
)

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> Plant list (button in upper left)
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
plant_list_dicts = api.plant_list_two(language_code=LanguageCode.de, page_size=5)

cnt_all = len(plant_list_dicts)
cnt_online = len([x for x in plant_list_dicts if x["status"] == 0])
cnt_offline = len([x for x in plant_list_dicts if x["status"] == 1])
cnt_fault = cnt_all - cnt_online - cnt_offline

print('\nTab "Plant" -> Plant list:')
print(
    f"""
+=================================================================================+
|                              Plant list                                         |
+=================================================================================+
| [#] (🔍Search ______________________ x)                                         |
+---------------------------------------------------------------------------------+
|     All ({cnt_all})    Online({cnt_online})    Offline({cnt_offline})    Fault({cnt_fault})
| Plant name  Current Power↕  PV capacity↕  Daily Power Gen.↕  Total Power Gen.↕
""".strip()
)
for plant_dict in plant_list_dicts:
    print(
        f"""
+---------------------------------------------------------------------------------+
| ___ {plant_dict['plantName']} ___
| Image:                  [{plant_dict['imgPath']}]
| Address:                {plant_dict['plantAddress']}
| Current Power:          {(plant_dict['currentPac']):0.0f} W
| Installation date:      {plant_dict['createDateText']}
| PV capacity:            {plant_dict['nominalPower']} Wp
| Daily Power Generation: {plant_dict['eToday']:0.2f} kWh
""".strip()
    )
print(
    f"""
+=================================================================================+
| ( Dashboard )          (*Plant*)          ( Service )          ( Me )           |
+=================================================================================+
""".lstrip()
)

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> My device list
> => Datalogger list shown
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""

# get datalogger list data
# # data already retrieved before
# plant_info_dict = api.plant_info(plant_id=PLANT_ID, language="de")
datalogger_list = plant_info_dict["datalogList"]

print('\nTab "Plant" -> My device list => Datalogger:')
print(
    f"""
+=================================================================================+
|                            My device list                                       |
+---------------------------------------------------------------------------------+
|  ( Search _______________________________ 🔍 )
|  [*Datalogger*]    [ Inverter ]
""".strip()
)
for datalogger_dict in datalogger_list:
    print(
        f"""
+---------------------------------------------------------------------------------+
| {datalogger_dict['alias'] or datalogger_dict['datalog_sn']}
| SN:                   {datalogger_dict['datalog_sn']}
| Device type:          {datalogger_dict['device_type']}
""".strip()
    )
    for item_name, item_value in zip(datalogger_dict["keys"], datalogger_dict["values"]):
        print(f"| {(item_name + ':'):21} {item_value}")
print(
    f"""
|                                                                                 |
+=================================================================================+
""".lstrip()
)

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> My device list
> -> Tab "Inverter"
> => Inverter list shown
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""

# get inverter list data
# # data already retrieved before
# plant_info_dict = api.plant_info(plant_id=PLANT_ID, language="de")
inverter_list = plant_info_dict["invList"]

print('\nTab "Plant" -> My device list => Inverter:')
print(
    f"""
+=================================================================================+
|                            My device list                                       |
+---------------------------------------------------------------------------------+
|  ( Search _______________________________ 🔍 )
|  [ Datalogger ]    [*Inverter*]
""".strip()
)
for inverter_dict in inverter_list:
    print(
        f"""
+---------------------------------------------------------------------------------+
| {inverter_dict['deviceAilas'] or inverter_dict['deviceSn']}
| Connection Status: {device_status_mapper.get(inverter_dict['deviceStatus'], "Unknown")}
| Power:             {inverter_dict['power']} W
| Today:             {inverter_dict['eToday']} kWh
| Data Logger:       {inverter_dict['datalogSn']}
| Device type:       {inverter_dict['deviceType'].upper()}
| SN:                {inverter_dict['deviceSn']}
""".strip()
    )
print(
    f"""
|                                                                                 |
+=================================================================================+
""".lstrip()
)

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> My device list
> -> Tab "Inverter"
> -> select your (NEO/TLX) inverter
> => Inverter details shown
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
# as "NEO 800M-X" is a TLX inverter, we get TLX data
INVERTER_SN = inverter_list[0]["deviceSn"]

# get inverter detail data
tlx_info_dict = api.tlx_params(tlx_id=INVERTER_SN)
tlx_info_bean = tlx_info_dict["newBean"]

# get chart data for "Real time data" chart
# "Hour" (5min values) chart support different types of data
hour_pac = api.tlx_data(
    tlx_id=INVERTER_SN,
    date=datetime.date.today(),
    tlx_data_type=TlxDataTypeNeo.power_ac,
)["invPacData"]
hour_ppv = api.tlx_data(
    tlx_id=INVERTER_SN,
    date=datetime.date.today(),
    tlx_data_type=TlxDataTypeNeo.power_pv,
)["invPacData"]
hour_upv1 = api.tlx_data(
    tlx_id=INVERTER_SN,
    date=datetime.date.today(),
    tlx_data_type=TlxDataTypeNeo.voltage_pv1,
)["invPacData"]
hour_ipv1 = api.tlx_data(
    tlx_id=INVERTER_SN,
    date=datetime.date.today(),
    tlx_data_type=TlxDataTypeNeo.current_pv1,
)["invPacData"]
hour_upv2 = api.tlx_data(
    tlx_id=INVERTER_SN,
    date=datetime.date.today(),
    tlx_data_type=TlxDataTypeNeo.voltage_pv2,
)["invPacData"]
hour_ipv2 = api.tlx_data(
    tlx_id=INVERTER_SN,
    date=datetime.date.today(),
    tlx_data_type=TlxDataTypeNeo.current_pv2,
)["invPacData"]
# Month/Year/Total chart uses different endpoint
month_pac = api.tlx_energy_chart(tlx_id=INVERTER_SN, timespan=Timespan.month, date=datetime.date.today())
year_pac = api.tlx_energy_chart(tlx_id=INVERTER_SN, timespan=Timespan.year, date=datetime.date.today())
total_pac = api.tlx_energy_chart(tlx_id=INVERTER_SN, timespan=Timespan.total, date=datetime.date.today())

print('\nTab "Plant" -> My device list -> select NEO inverter:')
print(
    f"""
+=================================================================================+
|                             {tlx_info_bean['alias'] or tlx_info_bean['serialNum']}
+---------------------------------------------------------------------------------+
| SN:    {tlx_info_bean['serialNum']}
| Model: {tlx_info_dict['inverterType']}                                           All parameters>
+---------------------------------------------------------------------------------+
| {device_status_mapper.get(str(tlx_info_bean['status']), "Unknown")}
| Current Power:          {tlx_info_bean['power']:0.1f} W
| Rated power:            {tlx_info_bean['pmax']:0.0f} W
| Daily Power Generation: {tlx_info_bean['eToday']:0.1f} kWh
| Total Power Generation: {tlx_info_bean['eTotal']:0.1f} kWh
+---------------------------------------------------------------------------------+
| Real time data
|  [*Hour*] [ DAY ] [ MONTH ] [ YEAR ]
|  (<) {datetime.date.today()} (>)              [Pac]
""".strip()
)
miniplot(hour_pac, rows_to_plot=5, max_width=80)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [*Hour*] [ DAY ] [ MONTH ] [ YEAR ]
|  (<) {datetime.date.today()} (>)              [PV Power]
""".strip()
)
miniplot(hour_ppv, rows_to_plot=3)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [*Hour*] [ DAY ] [ MONTH ] [ YEAR ]
|  (<) {datetime.date.today()} (>)              [PV1 Voltage]
""".strip()
)
miniplot(hour_upv1, rows_to_plot=3)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [*Hour*] [ DAY ] [ MONTH ] [ YEAR ]
|  (<) {datetime.date.today()} (>)              [PV1 Current]
""".strip()
)
miniplot(hour_ipv1, rows_to_plot=3)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [*Hour*] [ DAY ] [ MONTH ] [ YEAR ]
|  (<) {datetime.date.today()} (>)              [PV2 Voltage]
""".strip()
)
miniplot(hour_upv2, rows_to_plot=3)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [*Hour*] [ DAY ] [ MONTH ] [ YEAR ]
|  (<) {datetime.date.today()} (>)              [PV2 Current]
""".strip()
)
miniplot(hour_ipv2, rows_to_plot=3)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [ Hour ] [*DAY*] [ MONTH ] [ YEAR ]
|  (<) {datetime.date.today().strftime("%Y-%m")} (>)
""".strip()
)
miniplot(month_pac, rows_to_plot=4)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [ Hour ] [ DAY ] [*MONTH*] [ YEAR ]
|  (<) {datetime.date.today().strftime("%Y")} (>)
""".strip()
)
miniplot(year_pac, rows_to_plot=4)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [ Hour ] [ DAY ] [ MONTH ] [*YEAR*]
|
""".strip()
)
miniplot(total_pac, rows_to_plot=4)
print(
    f"""
+=================================================================================+
|            ( Events )            ( Control )            ( Edit )                |
+=================================================================================+
""".lstrip()
)

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> My device list
> -> Tab "Inverter"
> -> select your (NEO/TLX) inverter
> -> click "All parameters>"
> => Inverter details shown
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""

# get inverter detail data
# # already retrieved before
# tlx_info_dict = api.tlx_params(tlx_id=INVERTER_SN)
# tlx_info_bean = tlx_info_dict["newBean"]

# get "Important" Data (current Volt/Current/Power)
tlx_detail_info_vaw = api.device_detail(device_id=INVERTER_SN, device_type="tlx")

# get "Other" Data (frequency, temperature, etc.)
# GET https://server-api.growatt.com/newTlxApi.do?op=getTlxDetailData&id={INVERTER_SN}
tlx_detail_dict = api.tlx_detail(tlx_id=INVERTER_SN)

print('\nTab "Plant" -> My device list -> select NEO inverter -> All parameters:')
print(
    f"""
+=================================================================================+
|                                      Info                                       |
+---------------------------------------------------------------------------------+
|                                 Basic Parameters                                |
| SN:                   {tlx_info_bean['serialNum']}
| Model:                {tlx_info_dict['inverterType']}
| Firmware Version:     {tlx_info_bean['fwVersion']}/{tlx_info_bean['innerVersion']}
| COM software version: {tlx_info_bean['communicationVersion']}
| Port:                 {tlx_info_bean['dataLogSn']}
| Rated power:          {tlx_info_bean['pmax']:0.0f} W
| Model:                {tlx_info_bean['modelText']}
+---------------------------------------------------------------------------------+
|                                  Important Data                                 |
""".strip()
)
for info_line in tlx_detail_info_vaw["parameterGreat"]:
    print("| " + " ".join([f"{token:15}" for token in info_line]))
print(
    f"""
+---------------------------------------------------------------------------------+
|                                    Other Data                                   |
| Fac:              {tlx_detail_dict['data']['fac']} Hz
| Pac:              {tlx_detail_dict['data']['pac']} W
| Ppv:              {tlx_detail_dict['data']['ppv']} W
| Ppv1:             {tlx_detail_dict['data']['ppv1']} W
| Ppv2:             {tlx_detail_dict['data']['ppv2']} W
| Vpv1:             {tlx_detail_dict['data']['vpv1']} V
| Ipv1:             {tlx_detail_dict['data']['ipv1']} A
| Vpv2:             {tlx_detail_dict['data']['vpv2']} V
| Ipv2:             {tlx_detail_dict['data']['ipv2']} A
| Vac1:             {tlx_detail_dict['data']['vac1']} V
| Iac1:             {tlx_detail_dict['data']['iac1']} A
| Pac1:             {tlx_detail_dict['data']['pac1']} W
| VacRs:            {tlx_detail_dict['data']['vacRs']} V
| EacToday:         {tlx_detail_dict['data']['eacToday']} kWh
| EacTotal:         {tlx_detail_dict['data']['eacTotal']} kWh
| Epv1Today:        {tlx_detail_dict['data']['epv1Today']} kWh
| Epv2Today:        {tlx_detail_dict['data']['epv2Today']} kWh
| Temp1:            {tlx_detail_dict['data']['temp1']} ℃
| Temp2:            {tlx_detail_dict['data']['temp2']} ℃
| Temp3:            {tlx_detail_dict['data']['temp3']} ℃
| Temp4:            {tlx_detail_dict['data']['temp4']} ℃
| Temp5:            {tlx_detail_dict['data']['temp5']} ℃
| PBusVoltage:      {tlx_detail_dict['data']['pBusVoltage']} V
| NBusVoltage:      {tlx_detail_dict['data']['nBusVoltage']} V
| OpFullwatt:       {tlx_detail_dict['data']['opFullwatt']} W
| InvDelayTime:     {tlx_detail_dict['data']['invDelayTime']} S
| DciR:             {tlx_detail_dict['data']['dciR']} mA
| DciS:             {tlx_detail_dict['data']['dciS']} mA
| DciT:             {tlx_detail_dict['data']['dciT']} mA
| SysFaultWord:     {tlx_detail_dict['data']['sysFaultWord']}
| SysFaultWord1:    {tlx_detail_dict['data']['sysFaultWord1']}
| SysFaultWord2:    {tlx_detail_dict['data']['sysFaultWord2']}
| SysFaultWord3:    {tlx_detail_dict['data']['sysFaultWord3']}
| SysFaultWord4:    {tlx_detail_dict['data']['sysFaultWord4']}
| SysFaultWord5:    {tlx_detail_dict['data']['sysFaultWord5']}
| SysFaultWord6:    {tlx_detail_dict['data']['sysFaultWord6']}
| SysFaultWord7:    {tlx_detail_dict['data']['sysFaultWord7']}
| FaultType:        {tlx_detail_dict['data']['faultType']}
| WarnCode:         {tlx_detail_dict['data']['warnCode']}
| RealOPPercent:    {tlx_detail_dict['data']['realOPPercent']}
| DeratingMode:     {tlx_detail_dict['data']['deratingMode']}
| DryContactStatus: {tlx_detail_dict['data']['dryContactStatus']}
| LoadPercent:      {tlx_detail_dict['data']['loadPercent']}
| uwSysWorkMode:    {tlx_detail_dict['data']['uwSysWorkMode']}
| Gfci:             {tlx_detail_dict['data']['gfci']} mA
| Iso:              {tlx_detail_dict['data']['iso']} KΩ
| EtoUserToday:     {tlx_detail_dict['data']['etoUserToday']} kWh
| EtoUserTotal:     {tlx_detail_dict['data']['etoUserTotal']} kWh
| EtoGridToday:     {tlx_detail_dict['data']['etoGridToday']} kWh
| EtoGridTotal:     {tlx_detail_dict['data']['etoGridTotal']} kWh
| ElocalLoadToday:  {tlx_detail_dict['data']['elocalLoadToday']} kWh
| ElocalLoadTotal:  {tlx_detail_dict['data']['elocalLoadTotal']} kWh
| Epv1Total:        {tlx_detail_dict['data']['epv1Total']} kWh
| Epv2Total:        {tlx_detail_dict['data']['epv2Total']} kWh
| EpvTotal:         {tlx_detail_dict['data']['epvTotal']} kWh
| BsystemWorkMode:  {tlx_detail_dict['data']['bsystemWorkMode']}
| BgridType:        {tlx_detail_dict['data']['bgridType']}
+=================================================================================+
""".lstrip()
)

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> My device list
> -> Tab "Inverter"
> -> select your (NEO/TLX) inverter
> -> click "Events"
> => Event log (Alarms) shown
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
# get event log data
event_log_dict = api.device_event_logs(
    device_id=INVERTER_SN,
    device_type="tlx",
    language_code=LanguageCode.de,
)
events = event_log_dict.get("eventList", [])

print('\nTab "Plant" -> My device list -> select NEO inverter -> Events:')
print(
    f"""
+=================================================================================+
|                                 Warning list                                    |
+---------------------------------------------------------------------------------+
""".strip()
)
for event in events:
    print(
        f"""
|      ({event['occurTime']})
| SN:          {event['deviceAlias'] or event['deviceSerialNum']}
| Plant name:  {event_log_dict['plantName']}
| Description: {event['eventCode']} {event['description']}
| Instruction: {event['solution']}
+---------------------------------------------------------------------------------+
""".strip()
    )
print(
    f"""
|          No more data
|
+=================================================================================+
|            (*Events*)            ( Control )            ( Edit )                |
+=================================================================================+
""".lstrip()
)


"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> My device list
> -> Tab "Inverter"
> -> select your (NEO/TLX) inverter
> -> click "Edit"
> => Inverter alias shown
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
# get inverter detail data
# # already retrieved before
# tlx_info_dict = api.tlx_params(tlx_id=INVERTER_SN)

print('\nTab "Plant" -> My device list -> select NEO inverter -> Edit:')
print(
    f"""
+=================================================================================+
|                                    Edit                              [ Save ]   |
+---------------------------------------------------------------------------------+
| Alias: {tlx_info_bean['alias'] or tlx_info_bean['serialNum']}
+---------------------------------------------------------------------------------+
|  [Delete device]
+=================================================================================+
|            ( Events )            ( Control )            (*Edit*)                |
+=================================================================================+
""".lstrip()
)

# change alias and save
# enable if you know what you are doing
# print(f""")
# +=================================================================================+
# |                                    Edit                              [*Save*]   |
# +=================================================================================+
# |                                                                                 |
# |      +-------------------------------------------------------------------+      |
# """.strip())
# new_alias = f"{tlx_info_bean['serialNum']}"
# if api.update_device_alias(device_id=INVERTER_SN, device_type="tlx", new_alias=new_alias):
#     print(f"|      |   Device alias changed to '{new_alias}'")
# else:
#     print(f"|      |   Failed to save alias '{new_alias}'")
# print(f"""
# |      +-------------------------------------------------------------------+      |
# |                                                                                 |
# +=================================================================================+
# |            ( Events )            ( Control )            (*Edit*)                |
# +=================================================================================+
# """.lstrip())

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> Panel data
> -> Daily performance curve
> => Chart is shown
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
# get chart data for "Daily performance curve"
inverter_chart_data = api.inverter_energy_chart(
    plant_id=PLANT_ID,
    inverter_id=INVERTER_SN,
    date=datetime.date.today(),
    timespan=Timespan.day,
    filter_type="all",
)

print('\nTab "Plant" -> Panel data -> Daily performance curve:')
print(
    f"""
+=================================================================================+
|                                   Panel data                                    |
+---------------------------------------------------------------------------------+
|  [*Daily performance curve*]         [ Production ]                             |
|  [ Filter   "All" ▼ ]     (<) {datetime.date.today()} (>)
+---------------------------------------------------------------------------------+
| AC(W)
""".strip()
)
miniplot(
    {k: v for k, v in zip(inverter_chart_data["time"], inverter_chart_data["pac"])},
    rows_to_plot=4,
)
print(
    f"""
+---------------------------------------------------------------------------------+
| PV1 (W)
""".strip()
)
miniplot(
    {k: v for k, v in zip(inverter_chart_data["time"], inverter_chart_data["ppv1"])},
    rows_to_plot=4,
)
print(
    f"""
+---------------------------------------------------------------------------------+
| T (°C)
""".strip()
)
miniplot(
    {k: v for k, v in zip(inverter_chart_data["time"], inverter_chart_data["temp1"])},
    rows_to_plot=4,
)
print(
    f"""
+---------------------------------------------------------------------------------+
|  ☑ PV1 (W)    ☑ PV2 (W)    ☑ PV3 (W)    ☑ PV4 (W)    ☑ PV1 (V)    ☑ PV2 (V)   |
|  ☑ PV3 (V)    ☑ PV4 (V)    ☑ PV1 (I)    ☑ PV2 (I)    ☑ PV3 (I)    ☑ PV4 (I)   |
|  ☑ AC (W)     ☑ AC (F)     ☑ AC (V)     ☑ AC (I)     ☑ T (°C)     ☑ AP (W)    |
+=================================================================================+
""".lstrip()
)


"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> Panel data
> -> Production
> => Chart is shown
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
# get chart data for "Production"
inverter_chart_data_month = api.inverter_energy_chart(
    plant_id=PLANT_ID,
    inverter_id=INVERTER_SN,
    date=datetime.date.today(),
    timespan=Timespan.month,
    filter_type="pv1",
)
inverter_chart_data_year = api.inverter_energy_chart(
    plant_id=PLANT_ID,
    inverter_id=INVERTER_SN,
    date=datetime.date.today(),
    timespan=Timespan.year,
    filter_type="pv1",
)
inverter_chart_data_total = api.inverter_energy_chart(
    plant_id=PLANT_ID,
    inverter_id=INVERTER_SN,
    date=datetime.date.today(),
    timespan=Timespan.total,
    filter_type="pv1",
)

print('\nTab "Plant" -> Panel data -> Production:')
print(
    f"""
+=================================================================================+
|                                   Panel data                                    |
+---------------------------------------------------------------------------------+
|  [ Daily performance curve ]         [*Production*]                             |
+---------------------------------------------------------------------------------+
|  [ Filter   "PV1" ▼ ]     (<) {datetime.datetime.today().strftime("%Y-%m")} (>)
|  [*DAY*]  [ MONTH ]  [ YEAR ]
""".strip()
)
miniplot(
    {k: v for k, v in zip(inverter_chart_data_month["time"], inverter_chart_data_month["epv1Energy"])},
    rows_to_plot=4,
)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [ Filter   "PV1" ▼ ]     (<) {datetime.datetime.today().strftime("%Y")} (>)
|  [ DAY ]  [*MONTH*]  [ YEAR ]
""".strip()
)
miniplot(
    {
        k: v
        for k, v in zip(
            [int(t) for t in inverter_chart_data_year["time"]],
            inverter_chart_data_year["epv1Energy"],
        )
    },
    rows_to_plot=4,
)
print(
    f"""
+---------------------------------------------------------------------------------+
|  [ Filter   "PV1" ▼ ]         {(datetime.datetime.today().year - 5):04g}-{datetime.datetime.today().year:04g}
|  [ DAY ]  [ MONTH ]  [*YEAR*]
""".strip()
)
miniplot(
    {
        k: v
        for k, v in zip(
            [int(t) for t in inverter_chart_data_total["time"]],
            inverter_chart_data_total["epv1Energy"],
        )
    },
    rows_to_plot=4,
)
print(
    f"""
+---------------------------------------------------------------------------------+
| ☑ PV1 (Energy)  ☐ PV2 (Energy)  ☐ PV3 (Energy)  ☐ PV4 (Energy)  ☐ AC (Energy) |
+=================================================================================+
""".lstrip()
)

"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> Panel view
> -> Panel power
> => Small solar-panel pictures shown in a grid
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
panel_view_chart_data = api.inverter_panel_energy_chart(
    plant_id=PLANT_ID,
    inverter_id=INVERTER_SN,
    date=datetime.date.today(),
    timespan=Timespan.day,
)

# small plots for each panel
plot_boxes = {}
for ts, box_data in panel_view_chart_data["box"].items():
    for box in box_data:
        box_name = box["name"]
        plot_boxes[box_name] = plot_boxes.get(box_name, {})
        plot_boxes[box_name][ts] = float(box["power"])

# big plot for cumulated data
plot_big = {
    k: float(v) for k, v in zip(panel_view_chart_data["chart"]["time"], panel_view_chart_data["chart"]["power"])
}

print('\nTab "Plant" -> Panel view (Panel power):')
print(
    f"""
+=================================================================================+
|                                   Panel view                                    |
+---------------------------------------------------------------------------------+
|  [*Panel power*]         [ Panel production ]                                   |
|  [ Filter   "All" ▼ ]     (<) {datetime.date.today()} (>)
+---------------------------------------------------------------------------------+
|                                                                                 |
""".strip()
)
for idx, (panel_name, plt_data) in enumerate(plot_boxes.items()):
    print(f"|   +-------------------------------------------------------------------------+   |")
    print(f"|   |     {panel_name}  (mean: {sum(plt_data.values()) / len(plt_data):0.1f} W)")
    miniplot(plt_data, rows_to_plot=3, max_width=70, prefix="|   | ")
    print(f"|   +-------------------------------------------------------------------------+   |")
    print(f"|                                                                                 |")

print(f"+---------------------------------------------------------------------------------+")
miniplot(plot_big)
print(
    f"""
+=================================================================================+
""".lstrip()
)


"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> Panel view
> -> Panel producution
> => Small solar-panel pictures shown in a grid
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
plot_date = datetime.date.today() - datetime.timedelta(days=31)
panel_view_chart_data = api.inverter_panel_energy_chart(
    plant_id=PLANT_ID,
    inverter_id=INVERTER_SN,
    date=plot_date,
    timespan=Timespan.month,
)

# small plots for each panel
plot_boxes = {}
for ts, box_data in panel_view_chart_data["box"].items():
    for box in box_data:
        box_name = box["name"]
        plot_boxes[box_name] = plot_boxes.get(box_name, {})
        plot_boxes[box_name][int(ts)] = float(box["energy"])

# big plot for cumulated data
plot_big = {
    int(k): float(v) for k, v in zip(panel_view_chart_data["chart"]["time"], panel_view_chart_data["chart"]["energy"])
}

print('\nTab "Plant" -> Panel view (Panel production):')
print(
    f"""
+=================================================================================+
|                                   Panel view                                    |
+---------------------------------------------------------------------------------+
|  [ Panel power ]         [*Panel production*]                                   |
|  [ Filter   "All" ▼ ]     (<) {plot_date.strftime("%Y-%m")} (>)
+---------------------------------------------------------------------------------+
|                                                                                 |
""".strip()
)
for idx, (panel_name, plt_data) in enumerate(plot_boxes.items()):
    print(f"|   +-------------------------------------------------------------------------+   |")
    print(f"|   |     {panel_name}  (sum: {sum(plt_data.values())} kWh)")
    miniplot(plt_data, rows_to_plot=3, max_width=70, prefix="|   | ")
    print(f"|   +-------------------------------------------------------------------------+   |")
    print(f"|                                                                                 |")

print(f"+---------------------------------------------------------------------------------+")
miniplot(plot_big)
print(
    f"""
+=================================================================================+
""".lstrip()
)


"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> APP
> -> Plant
> -> My device list
> -> Tab "Inverter"
> -> select your (NEO/TLX) inverter
> -> click "Control"
> => Inverter settings shown
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
# # already retrieved before
# tlx_info_dict = api.tlx_params(tlx_id=INVERTER_SN)
# tlx_info_bean = tlx_info_dict["newBean"]
inverter_device_type_int = tlx_info_bean["deviceType"]

# get all settings
tlx_settings_all_dict = api.tlx_all_settings(tlx_id=INVERTER_SN)

# enabled settings and PW
tlx_enabled_settings = api.tlx_enabled_settings(
    tlx_id=INVERTER_SN,
    language_code=LanguageCode.de,
    device_type_id=inverter_device_type_int,
)
settings_pw = tlx_enabled_settings["settings_password"]


def try_type_convert(val_, type_):
    try:
        if type_ is bool:
            return val_ == "1"  # as bool('0') would evaluate to True
        return type_(val_)
    except (ValueError, TypeError, IndexError):
        return val_


def get_inv_setting(tcpset: str = None, register: int = None, tlx_keys: list = None, dtypes: list = None):
    # try to get from tlx settings
    if tlx_keys:
        results = {0: "CACHED"}
        collected = True
        for idx_, param_name in enumerate(tlx_keys):
            if param_name not in tlx_settings_all_dict:
                collected = False
                break  # not found in cached data
            results[idx_ + 1] = try_type_convert(tlx_settings_all_dict[param_name], dtypes[idx_])
        if collected:
            return results
    # get from tcpSet using setting name or register
    elif (tcpset is not None) or (register is not None):
        inv_result = api.read_inverter_setting(
            inverter_id=INVERTER_SN,
            device_type="tlx",
            setting_name=tcpset if tcpset else None,
            register_address=register if not tcpset else None,
        )
        if inv_result["success"] is False:
            return {i: f"ERROR {inv_result['error_message']}" for i in range(10)}
        retval = {0: "SUCCESS"}
        idx_ = 0
        for key_ in sorted(inv_result.keys()):
            if key_.startswith("param"):
                val_ = try_type_convert(inv_result[key_], dtypes[idx_])
                idx_ += 1
                retval[idx_] = val_
        return retval
    else:
        raise AttributeError


country_data = get_inv_setting(register=90, dtypes=[int])
active_power_data = get_inv_setting(
    tlx_keys=["activeRate", "pvPfCmdMemoryState"],
    tcpset="pv_active_p_rate",
    dtypes=[int, bool],
)
reactive_power = get_inv_setting(tcpset="pv_reactive_p_rate", dtypes=[int, int, bool])
reactive_power_mode, range_hint = {
    0: ("PF fixed", "(value can only be '1')"),
    1: ("Set power factor", "(-1 ~ 1)"),
    2: ("Default PF Curve", "(value field not existing for this setting)"),
    3: ("Customize PF Curve", "special settings apply"),
    4: ("Conductive reactive power ratio (%)", "(0 ~ 100)"),
    5: ("Inductive reactive power ratio (%)", "(0 ~ 100)"),
    6: ("QV mode", "(value field not existing for this setting)"),
    7: ("Set reactive power percentage", "(-100 ~ +100)"),
}.get(reactive_power[2], (f"{reactive_power[2]}", ""))
if reactive_power[2] == 0:
    # PF fixed: value can only be '1'
    reactive_power[1] = 1
# "Customize PF Curve" has special settings
reactive_power_custom = get_inv_setting(
    tlx_keys=[
        "tlx_pflinep1_lp",
        "tlx_pflinep1_pf",
        "tlx_pflinep2_lp",
        "tlx_pflinep2_pf",
        "tlx_pflinep3_lp",
        "tlx_pflinep3_pf",
        "tlx_pflinep4_lp",
        "tlx_pflinep4_pf",
    ],
    tcpset="tlx_custom_pf_curve",
    dtypes=[int, float, int, float, int, float, int, float],
)
inverter_time = get_inv_setting(
    tcpset="pf_sys_year",
    tlx_keys=["pf_sys_year"],
    dtypes=[
        # returns param1='2024-2-4 11:38:4'  # (without leading zeroes)
        lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S").isoformat(sep=" ")
    ],
)
over_voltage = get_inv_setting(tcpset="pv_grid_voltage_high", tlx_keys=["pv_grid_voltage_high"], dtypes=[float])
under_voltage = get_inv_setting(tcpset="pv_grid_voltage_low", tlx_keys=["pv_grid_voltage_low"], dtypes=[float])
over_frequency = get_inv_setting(tcpset="pv_grid_frequency_high", tlx_keys=["pv_grid_frequency_high"], dtypes=[float])
under_frequency = get_inv_setting(tcpset="pv_grid_frequency_low", tlx_keys=["pv_grid_frequency_low"], dtypes=[float])
export_limitation = get_inv_setting(tcpset="backflow_setting", dtypes=[int, float, bool])
export_limitation_selection = {0: "Disable", 1: "Enable meter"}.get(export_limitation[1], f"{export_limitation[1]}")
failsafe_power_limit = get_inv_setting(
    tcpset="tlx_backflow_default_power",
    tlx_keys=["tlx_backflow_default_power"],
    dtypes=[float],
)
power_sensor = get_inv_setting(tcpset="tlx_limit_device", tlx_keys=["tlx_limit_device"], dtypes=[int])
power_sensor_setting = {
    0: "not connected to power collection",
    1: "Meter",
    2: "CT",
}.get(power_sensor[1], f"{power_sensor[1]}")

operating_mode = get_inv_setting(tcpset="system_work_mode", tlx_keys=["system_work_mode"], dtypes=[int])
operating_mode_setting = {
    0: "Default",
    1: "System retrofit",
    2: "Multi-parallel",
    3: "System retrofit-simplification",
}.get(operating_mode[1], f"unknown value '{operating_mode[1]}'")

print('\nTab "Plant" -> My device list -> select NEO inverter -> Control:')
print(
    f"""
+=================================================================================+
|                             {tlx_info_bean['serialNum']}
+---------------------------------------------------------------------------------+
| Country & Regulation                          [Read]
|   [ {(country_data[1] or "Not set - Click to select"):^30} ]
|         ( Done )
+---------------------------------------------------------------------------------+
| Set active power                              [Read]
|   [ {active_power_data[1]:^30} ] % (0 ~ 100)
|   Whether to remember ({active_power_data[2]})
|         ( Done )
+---------------------------------------------------------------------------------+
| Set reactive power                            [Read]
|   [ {reactive_power_mode:^28s} ▼ ]
""".strip()
)
if reactive_power[2] == 3:
    print(
        f"""
|                                                                                 |
|  +--- PopUp -----------------------------------------------------------------+  |
|  | Point 1  Power percentage   [ {reactive_power_custom[1]:^5} ] (0 ~ 100)
|  |          Power factor point [ {reactive_power_custom[2]:^5} ] (-1 ~ -0.8 | 0.8 ~ 1)
|  | Point 2  Power percentage   [ {reactive_power_custom[3]:^5} ] (0 ~ 100)
|  |          Power factor point [ {reactive_power_custom[4]:^5} ] (-1 ~ -0.8 | 0.8 ~ 1)
|  | Point 3  Power percentage   [ {reactive_power_custom[5]:^5} ] (0 ~ 100)
|  |          Power factor point [ {reactive_power_custom[6]:^5} ] (-1 ~ -0.8 | 0.8 ~ 1)
|  | Point 4  Power percentage   [ {reactive_power_custom[7]:^5} ] (0 ~ 100)
|  |          Power factor point [ {reactive_power_custom[8]:^5} ] (-1 ~ -0.8 | 0.8 ~ 1)
|  |       ( Yes )
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
""".strip()
    )
elif reactive_power[1] is not None:
    print(f"|   [ {reactive_power[1]:^30} ] {range_hint}")
print(
    f"""
|   Whether to remember ({reactive_power[3]})
|         ( Done )
+---------------------------------------------------------------------------------+
| Set inverter time                             [Read]
|   [ {inverter_time[1]:^30} ]
|         ( Done )
+---------------------------------------------------------------------------------+
| Over voltage / High Grid Voltage Limit        [Read]
|   [ {over_voltage[1]:^30} ]
|         ( Yes )
+---------------------------------------------------------------------------------+
| Under voltage / Low Grid Voltage Limit        [Read]
|   [ {under_voltage[1]:^30} ]
|         ( Yes )
+---------------------------------------------------------------------------------+
| Overfrequency / High Grid Frequency Limit     [Read]
|   [ {over_frequency[1]:^30} ]
|         ( Yes )
+---------------------------------------------------------------------------------+
| Underfrequency / High Grid Frequency Limit    [Read]
|   [ {under_frequency[1]:^30} ]
|         ( Done )
+---------------------------------------------------------------------------------+
| Export Limitation                             [Read]
|   [ {export_limitation_selection:^28} ▼ ]
""".strip()
)
if export_limitation[1] != 0:
    print(f"|   [ {export_limitation[2]:^30} ] Power (W)")
print(
    f"""
|         ( Done )
+---------------------------------------------------------------------------------+
| Failsafe power limit                          [Read]
|   [ {failsafe_power_limit[1]:^30} ]
|         ( Yes )
+---------------------------------------------------------------------------------+
| Power Sensor                                  [Read]
|   [ {power_sensor_setting:^28} ▼ ]
|         ( Done )
+---------------------------------------------------------------------------------+
| Reset                                         [Read]
|   Make sure the inverter is in a waiting or standby state.
|         ( Done )
+---------------------------------------------------------------------------------+
| Operating mode                                [Read]
|   [ {operating_mode_setting:^28} ▼ ]
|         ( Done )
+=================================================================================+
|            ( Events )            (*Control*)            ( Edit )                |
+=================================================================================+
""".lstrip()
)


"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> Web Frontend (offers additional settings not available in App)
> -> Dashboard
> -> My Photovoltaic Devices
> -> select your (NEO/TLX) inverter
> -> click "Setting" -> "Advanced Setting"
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
regulation_frequency_low = get_inv_setting(
    tcpset="l_1_freq", tlx_keys=["l_1_freq_1", "l_1_freq_2"], dtypes=[float, float]
)
regulation_frequency_high = get_inv_setting(
    tcpset="h_1_freq", tlx_keys=["h_1_freq_1", "h_1_freq_2"], dtypes=[float, float]
)
regulation_voltage_low = get_inv_setting(
    tcpset="l_1_volt", tlx_keys=["l_1_volt_1", "l_1_volt_2"], dtypes=[float, float]
)
regulation_voltage_high = get_inv_setting(
    tcpset="h_1_volt", tlx_keys=["h_1_volt_1", "h_1_volt_2"], dtypes=[float, float]
)
loading_rate = get_inv_setting(tcpset="loading_rate", tlx_keys=["loading_rate"], dtypes=[float])
restart_loading_rate = get_inv_setting(tcpset="restart_loading_rate", tlx_keys=["restart_loading_rate"], dtypes=[float])
overfrequency_start_point = get_inv_setting(tcpset="over_fre_drop_point", dtypes=[float])
overfrequency_loadreduction_gradient = get_inv_setting(tcpset="over_fre_lored_slope", dtypes=[float])
overfrequency_load_reduction_delay_time = get_inv_setting(tcpset="over_fre_lored_delaytime", dtypes=[float])
qv_volt_high_out = get_inv_setting(tlx_keys=["qv_h1"], tcpset="qv_h1", dtypes=[float])
qv_volt_high_in = get_inv_setting(tlx_keys=["qv_h2"], tcpset="qv_h2", dtypes=[float])
qv_volt_low_out = get_inv_setting(tlx_keys=["qv_l1"], tcpset="qv_l1", dtypes=[float])
qv_volt_low_in = get_inv_setting(tlx_keys=["qv_l2"], tcpset="qv_l2", dtypes=[float])
qv_delay = get_inv_setting(tlx_keys=["delay_time"], tcpset="delay_time", dtypes=[float])
qv_percent = get_inv_setting(tlx_keys=["q_percent_max"], tcpset="q_percent_max", dtypes=[float])
inverter_on_off = get_inv_setting(tlx_keys=["tlx_on_off"], tcpset="tlx_on_off", dtypes=[int])
inverter_on_off_str = {
    1: "On",
    0: "Off",
}.get(inverter_on_off[1], f"Unknown status {inverter_on_off[1]}")

print("\nAdditional settings from Web frontend")
print(
    f"""
+=================================================================================+
|                    Additional settings available in Web frontend                |
+---------------------------------------------------------------------------------+
| ▼ Regulation parameter setting
|    Low Frequency Setting
|       AC Frequency Low 1         [ {regulation_frequency_low[1]:^8} ]
|       AC Frequency Low 2         [ {regulation_frequency_low[2]:^8} ]
|    High Frequency Setting
|       AC Frequency High 1        [ {regulation_frequency_high[1]:^8} ]
|       AC Frequency High 2        [ {regulation_frequency_high[2]:^8} ]
|    Low Voltage Setting
|       AC Voltage Low 1           [ {regulation_voltage_low[1]:^8} ]
|       AC Voltage Low 2           [ {regulation_voltage_low[2]:^8} ]
|    High Voltage Setting
|       AC Voltage High 1          [ {regulation_voltage_high[1]:^8} ]
|       AC Voltage High 2          [ {regulation_voltage_high[2]:^8} ]
|    Loading rate                  [ {loading_rate[1]:^8} ] % ( 0.0 ~ 6000.0 )
|    Restart loading rate          [ {restart_loading_rate[1]:^8} ] % ( 0.0 ~ 6000.0 )
|    Over-freq. start point        [ {overfrequency_start_point[1]:^8} ] Hz
|    Over-freq. load red. gradient [ {overfrequency_loadreduction_gradient[1]:^8} ]%
|    Over-freq. load red. delay    [ {overfrequency_load_reduction_delay_time[1]:^8} ] ms
+---------------------------------------------------------------------------------+
| ▼ Q (V) setting
|    Cut out high Voltage          [ {qv_volt_high_out[1]:^8} ] V
|    Cut into high Voltage         [ {qv_volt_high_in[1]:^8} ] V
|    Cut out low Voltage           [ {qv_volt_low_out[1]:^8} ] V
|    Cut into low Voltage          [ {qv_volt_low_in[1]:^8} ] V
|    Delay time                    [ {qv_delay[1]:^8} ] ms
|    Reactive power percentage     [ {qv_percent[1]:^8} ] %
+---------------------------------------------------------------------------------+
| Set Inverter On/Off              [ {inverter_on_off_str:^8} ]
| Register [ ________ ]      Value [ ________ ] -> see next screen "Register dump"
+---------------------------------------------------------------------------------+
|  Please enter password ({settings_pw})   (Yes)  (Advanced Settings)  (Cancel) |
+=================================================================================+
"""
)


"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> Web Frontend (register dump not available in App)
> -> Dashboard
> -> My Photovoltaic Devices
> -> select your (NEO/TLX) inverter
> -> click "Setting" -> "Advanced Setting"
> -> Start Address (...) / End Address (...) -> "Advanced Read)
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
# dump inverter registers
# fmt: off
register_ranges = [  # skipping "Reserved" registers
    (0, 124), (125, 179), (180, 188), (201, 203), (209, 223), (229, 229), (230, 242), (304, 345), (532, 554), (600, 612),
    (660, 660), (1000, 1038), (1044, 1044), (1047, 1048), (1060, 1062), (1070, 1071), (1080, 1092), (1100, 1121),
    (1125, 1204), (1244, 1249), (3000, 3059), (3070, 3071), (3079, 3082), (3085, 3114), (3125, 3238),
]
# fmt: on

min_reg = register_ranges[0][0]
max_reg = register_ranges[-1][1]
print(f"\nreading registers {min_reg} ~ {max_reg}")
register_result = {}
register_read_error = None
for register_start, register_end in register_ranges:
    chunk_size = register_end - register_start + 1
    query_start = register_start
    while query_start < register_end:
        print(f"\r {((query_start / max_reg) * 100):0.1f}% ...", end="")
        query_end = min(query_start + chunk_size, register_end)
        registers_dict = api.read_inverter_registers(
            inverter_id=INVERTER_SN,
            device_type="tlx",
            register_address_start=query_start,
            register_address_end=query_end,
        )
        if registers_dict["success"] is True:
            register_result.update(registers_dict["register"])
            query_start = query_end
            sleep(0.1)
        elif registers_dict["error_message"].startswith("500"):
            new_chunk_size = max(chunk_size // 2, 10)
            if new_chunk_size == chunk_size:
                print(
                    f"\rrequest timed out - inverter is either offline or booting from standby - Waiting 30 seconds..."
                )
                sleep(30)
            else:
                print(f"\rrequest timed out - reduced chunk size to {chunk_size}")
                chunk_size = new_chunk_size
                sleep(0.3)
        else:
            register_read_error = f"failed to read registers: '{registers_dict['error_message']}'"
            break
print(f"\r finished reading registers {min_reg} ~ {max_reg}\n")

# fmt: off
register_names = {
    0: "OnOff", 1: "SaftyFuncEn", 2: "PF CMD memory state", 3: "Active P Rate (Power limit)", 4: "Reactive P Rate", 5: "Power factor", 6: "Pmax HighByte (Wp)", 7: "Pmax LowByte (Wp)", 8: "Vnormal", 9: "Fw version H",
    10: "Fw version M", 11: "Fw version L", 12: "Fw version2 H", 13: "Fw version2 M", 14: "Fw version2 L", 15: "LCD language", 16: "CountrySelected", 17: "Vpv start", 18: "Time start", 19: "RestartDelay Time",
    20: "wPowerStart Slope", 21: "wPowerRestartSlopeEE", 22: "wSelectBaudrate", 23: "Serial NO", 24: "Serial NO", 25: "Serial NO", 26: "Serial NO", 27: "Serial NO", 28: "Module H", 29: "Module L",
    30: "Com Address", 31: "FlashStart", 32: "Reset User Info", 33: "Reset to factory", 34: "Manufacturer Info 8", 35: "Manufacturer Info 7", 36: "Manufacturer Info 6", 37: "Manufacturer Info 5", 38: "Manufacturer Info 4", 39: "Manufacturer Info3",
    40: "Manufacturer Info 2", 41: "Manufacturer Info 1", 42: "bfailsafeEn", 43: "DTC", 44: "TP", 45: "Sys Year", 46: "Sys Month", 47: "Sys Day", 48: "Sys Hour", 49: "Sys Min",
    50: "Sys Sec", 51: "Sys Weekly", 52: "Vac low", 53: "Vac high", 54: "Fac low", 55: "Fac high", 56: "Vac low 2", 57: "Vac high 2", 58: "Fac low 2", 59: "Fac high 2",
    60: "Vac low 3", 61: "Vac high 3", 62: "Fac low 3", 63: "Fac high 3", 64: "Vac low C", 65: "Vac high C", 66: "Fac low C", 67: "Fac high C", 68: "Vac time", 69: "Vac time",
    70: "Vac time", 71: "Vac time", 72: "Fac time", 73: "Fac time", 74: "Fac time", 75: "Fac time", 76: "Vac time", 77: "Vac time", 78: "Fac time", 79: "Fac time",
    80: "U10min", 81: "PV Voltage High Fault", 82: "FW Build No. 5", 83: "FW Build No. 4", 84: "FW Build No. 3", 85: "FW Build No. 2", 86: "FW Build No. 1", 87: "FW Build No. 0", 88: "ModbusVersion", 89: "PFModel",
    90: "GPRS IP Flag", 91: "FreqDerateStart", 92: "FLrate", 93: "V1S", 94: "V2S", 95: "V1L", 96: "V2L", 97: "QlockInpower", 98: "QlockOutpower", 99: "LIGridV",
    100: "LOGridV", 101: "PFAdj1", 102: "PFAdj2", 103: "PFAdj3", 104: "PFAdj4", 105: "PFAdj5", 106: "PFAdj6", 107: "QVRPDelayTimeEE", 108: "OverFDeratDelayTimeEE", 109: "QpercentMax",
    110: "PFLineP1_LP", 111: "PFLineP1_PF", 112: "PFLineP2_LP", 113: "PFLineP2_PF", 114: "PFLineP3_LP", 115: "PFLineP3_PF", 116: "PFLineP4_LP", 117: "PFLineP4_PF", 118: "Inverter Model SxxBxx", 119: "Inverter Model DxxTxx",
    120: "Inverter Model PxxUxx", 121: "Inverter Model Mxxxx (Wp/100)", 122: "ExportLimit_En/dis", 123: "ExportLimitPowerRate", 124: "TrakerModel", 125: "INV Type-1", 126: "INV Type-2", 127: "INV Type-3", 128: "INV Type-4", 129: "INV Type-5",
    130: "INV Type-6", 131: "INV Type-7", 132: "INV Type-8", 133: "BLVersion1", 134: "BLVersion2", 135: "BLVersion3", 136: "BLVersion4", 137: "Reactive P ValueH", 138: "Reactive P ValueL", 139: "ReactiveOut putPriorityEnable",
    140: "Reactive P Value(Ratio)", 141: "SvgFunction Enable", 142: "uwUnderFU ploadPoint", 143: "uwOFDerate RecoverPoint", 144: "uwOFDerate RecoverDelayTime", 145: "ZeroCurrent Enable", 146: "uwZeroCurrentStaticlowVolt", 147: "uwZeroCurrentStaticHighVolt", 148: "uwHVoltDerateHighPoint", 149: "uwHVoltDerateLowPoint",
    150: "uwQVPowerStableTime", 151: "uwUnderFUploadStopPoint", 152: "fUnderFreqPoint", 153: "fUnderFreqEndPoint", 154: "fOverFreqPoint", 155: "fOverFreqEndPoint", 156: "fUnderVoltPoint", 157: "fUnderVoltEndPoint", 158: "fOverVoltPoint", 159: "fOverVoltEndPoint",
    160: "uwNominalGridVolt", 161: "uwGridWattDelay", 162: "uwReconnectStartSlope", 163: "uwLFRTEE", 164: "uwLFRTTimeEE", 165: "uwLFRT2EE", 166: "uwLFRTTime2EE", 167: "uwHFRTEE", 168: "uwHFRTTim eEE", 169: "uwHFRT2EE",
    170: "uwHFRTTim e2EE", 171: "uwHVRTEE", 172: "uwHVRTTim eEE", 173: "uwHVRT2EE", 174: "uwHVRTTim e2EE", 175: "uwUnderFUploadDelayTime", 176: "uwUnderFUploadRateEE", 177: "uwGridRestart_H_Freq", 178: "OverFDeratResponseTime", 179: "UnderFUploadResponseTime",
    180: "MeterLink", 181: "OPT Number", 182: "OPT ConfigOK Flag", 183: "PvStrScan", 184: "BDCLinkNum", 185: "PackNum", 186: "Reserved", 187: "VPP function enable status", 188: "dataLog Connect Server status",
    200: "Reserved", 201: "PID Working Model", 202: "PID On/Off Ctrl", 203: "PID Option", 209: "New Serial",
    210: "New Serial", 211: "New Serial", 212: "New Serial", 213: "New Serial", 214: "New Serial", 215: "New Serial", 216: "New Serial", 217: "New Serial", 218: "New Serial", 219: "New Serial",
    220: "New Serial", 221: "New Serial", 222: "New Serial", 223: "New Serial", 229: "EnergyAdjust",
    230: "IslandDisable", 231: "FanCheck", 232: "EnableNLine", 233: "wCheckHardware", 234: "wCheckHardware2", 235: "ubNToGNDDetect", 236: "NonStdVacEnable", 237: "uwEnableSpecSet", 238: "Fast MPPT enable",
    240: "Check Step", 241: "INV-Lng", 242: "INV-Lat",
    304: "uwAntiBackflowFailPowerLimitEE", 305: "Qloadspeed", 306: "bParallelAntiBackflowEnable", 307: "uwAntiBackflowFailureResponseTime", 308: "uwParallelAntiBackflowPowerLimitEE", 309: "bISOCheckCmd",
    310: "bGPRSStatus", 311: "uwQmax_Inductive", 312: "uwQmax_Capactive", 313: "uwReactivePowerAdjustFailureResponseTime", 314: "bSuperAntiBackflowEnable", 315: "uwReactivePowerStableTime", 316: "uwQpStableTime", 317: "uwPuDerateTime", 318: "uwQVModelQ2Point", 319: "uwQVModelQ3Point",
    320: "bVrefModelEnable", 321: "uwVrefModelFilterTime", 322: "uwUserQPM odeP1Krate", 323: "uwUserQPModeP2Krate", 324: "uwUserQPModeP3Krate", 325: "uwUserQPModeQ1Krate", 326: "uwUserQPModeQ2Krate", 327: "uwUserQPModeQ3Krate", 328: "uwAcVoltHighDeratPowerLimit", 329: "BackflowSingleCtrl",
    330: "bAntiBackflowProtectMode", 331: "uwUnderFUploadZeroPowerPoint", 332: "FreqDerateZeroPowerPoint", 333: "bFreqDeratingStopModeEnable", 334: "bFreqIncreasingEnable", 335: "uwFreqIncreasingRecoverTime", 336: "uwFreqIncreasingEndLowPoint", 337: "bFreqIncreasingStopModeEnable", 338: "uwUserQpChrP1Krate", 339: "uwUserQpChrP2Krate",
    340: "uwUserQpChrP3Krate", 341: "wUserQpChrQ1Krate", 342: "wUserQpChrQ2Krate", 343: "wUserQpChrQ3Krate", 344: "uwFreqDeratingRecoverLowPoint", 345: "uwFreqIncreasingRecoverHighPoint",
    532: "TurnOffUnloadSpeed", 533: "LimitDevice", 534: "PowerSetOnDCSourceMode", 535: "OUFreqGrade1En", 536: "Country Set", 538: "InterlockEnable", 539: "OvTemperDeratePoint",
    540: "SafetySetPassword", 541: "AFCIOnoff", 542: "AfciSelfCheck", 543: "AfciReset", 544: "AFCIValue1", 545: "AFCIValue2", 546: "AFCIValue3", 547: "OverThresholdValueMaxCnt", 548: "AFCIScanTypeEnable", 549: "PowerVoltStopModeEn",
    550: "VoltWattRecoverTime", 551: "HVoltDerateStopPower", 552: "QVTimeExponent", 553: "Volt-Watt Watt1", 554: "Volt-Watt Watt2",
    600: "Volt-Var Var1", 601: "Volt-Var Var2", 602: "Volt-Var Var3", 603: "Volt-Var Var4", 605: "OPModEnergize", 608: "OneKeySetBDCMode", 609: "PowerOutputEnable",
    610: "DealDebugParaFlag", 612: "bAcCoupleEn",
    660: "ReloadCmd",
    1000: "Float charge current limit", 1001: "PF CMD memory state", 1002: "VbatStartForDischarge", 1003: "VbatlowWarnClr", 1004: "Vbatstopfordischarge", 1005: "Vbat stop for charge", 1006: "Vbat start for discharge", 1007: "Vbat constant charge", 1008: "EESysInfo.SysSetEn", 1009: "Battemp lower limit d",
    1010: "Bat temp upper limit d", 1011: "Bat temp lower limit c", 1012: "Bat temp upper limit c", 1013: "uwUnderFreDischargeDelyTime", 1014: "BatMdlSerialNum", 1015: "BatMdlParallNum", 1016: "DRMS_EN", 1017: "Bat First Start Time 4", 1018: "Bat First Stop Time 4", 1019: "Bat First on/off Switch 4",
    1020: "Bat First Start Time 5", 1021: "Bat First Stop Time 5", 1022: "Bat First on/off Switch 5", 1023: "Bat First Start Time 6", 1024: "Bat First Stop Time 6", 1025: "Bat First on/off Switch 6", 1026: "Grid First Start Time  4", 1027: "Grid First Stop Time 4", 1028: "Grid First Stop Switch 4", 1029: "Grid First Start Time 5",
    1030: "Grid First Stop Time 5", 1031: "Grid First Stop Switch 5", 1032: "Grid First Start Time 6", 1033: "Grid First Stop Time 6", 1034: "Grid First Stop Switch 6", 1035: "Bat First Start Time 4", 1037: "bCTMode", 1038: "CTAdjust",
    1044: "Priority", 1047: "AgingTestStepCmd", 1048: "BatteryType",
    1060: "BuckUpsFunEn", 1061: "BuckUPSVoltSet", 1062: "UPSFreqSet",
    1070: "GridFirstDischargePowerRate", 1071: "Grid First Stop SOC",
    1080: "Grid First Start Time 1", 1081: "Grid First Stop Time 1", 1082: "Grid First Stop Switch 1", 1083: "Grid First Start Time 2", 1084: "Grid First Stop Time 2", 1085: "Grid First Stop Switch 2", 1086: "Grid First Start Time 3", 1087: "Grid First Stop Time 3", 1088: "Grid First Stop Switch 3",
    1090: "Bat First Power Rate", 1091: "wBat First stop SOC", 1092: "AC charge Switch",
    1100: "Bat First Start Time 1", 1101: "Bat First Stop Time 1", 1102: "Bat First on/off Switch 1", 1103: "Bat First Start Time 2", 1104: "Bat First Stop Time 2", 1105: "Bat Firston/off Switch 2", 1106: "Bat First Start Time 3", 1107: "Bat First Stop Time 3", 1108: "Bat First on/off Switch 3",
    1110: "Load First Start Time 1", 1111: "Load First Stop Time 1", 1112: "Load First Switch 1", 1113: "Load First Start Time2", 1114: "Load First Stop Time 2", 1115: "Load First Switch 2", 1116: "Load First Start Time 3", 1117: "Load First Stop Time 3", 1118: "Load First Switch 3", 1119: "NewEPowerCalcFlag",
    1120: "BackUpEn", 1121: "SGIPEn", 1125: "BatSerialNO. 8 (pack 1)", 1126: "BatSerialNO. 7 (pack 1)", 1127: "BatSerialNO. 6 (pack 1)", 1128: "BatSerialNO. 5 (pack 1)", 1129: "BatSerialNO. 4 (pack 1)",
    1130: "BatSerialNO. 3 (pack 1)", 1131: "BatSerialNO. 2 (pack 1)", 1132: "BatSerialNO. 1 (pack 1)", 1133: "BatSerialNO. 8 (pack 2)", 1134: "BatSerialNO. 7 (pack 2)", 1135: "BatSerialNO. 6 (pack 2)", 1136: "BatSerialNO. 5 (pack 2)", 1137: "BatSerialNO. 4 (pack 2)", 1138: "BatSerialNO. 3 (pack 2)", 1139: "BatSerialNO. 2 (pack 2)",
    1140: "BatSerialNO. 1 (pack 2)", 1141: "BatSerialNO. 8 (pack 3)", 1142: "BatSerialNO. 7 (pack 3)", 1143: "BatSerialNO. 6 (pack 3)", 1144: "BatSerialNO. 5 (pack 3)", 1145: "BatSerialNO. 4 (pack 3)", 1146: "BatSerialNO. 3 (pack 3)", 1147: "BatSerialNO. 2 (pack 3)", 1148: "BatSerialNO. 1 (pack 3)", 1149: "BatSerialNO. 8 (pack 4)",
    1150: "BatSerialNO. 7 (pack 4)", 1151: "BatSerialNO. 6 (pack 4)", 1152: "BatSerialNO. 5 (pack 4)", 1153: "BatSerialNO. 4 (pack 4)", 1154: "BatSerialNO. 3 (pack 4)", 1155: "BatSerialNO. 2 (pack 4)", 1156: "BatSerialNO. 1 (pack 4)", 1157: "BatSerialNO. 8 (pack 5)", 1158: "BatSerialNO. 7 (pack 5)", 1159: "BatSerialNO. 6 (pack 5)",
    1160: "BatSerialNO. 5 (pack 5)", 1161: "BatSerialNO. 4 (pack 5)", 1162: "BatSerialNO. 3 (pack 5)", 1163: "BatSerialNO. 2 (pack 5)", 1164: "BatSerialNO. 1 (pack 5)", 1165: "BatSerialNO. 8 (pack 6)", 1166: "BatSerialNO. 7 (pack 6)", 1167: "BatSerialNO. 6 (pack 6)", 1168: "BatSerialNO. 5 (pack 6)", 1169: "BatSerialNO. 4 (pack 6)",
    1170: "BatSerialNO. 3 (pack 6)", 1171: "BatSerialNO. 2 (pack 6)", 1172: "BatSerialNO. 1 (pack 6)", 1173: "BatSerialNO. 8 (pack 7)", 1174: "BatSerialNO. 7 (pack 7)", 1175: "BatSerialNO. 6 (pack 7)", 1176: "BatSerialNO. 5 (pack 7)", 1177: "BatSerialNO. 4 (pack 7)", 1178: "BatSerialNO. 3 (pack 7)", 1179: "BatSerialNO. 2 (pack 7)",
    1180: "BatSerialNO. 1 (pack 7)", 1181: "BatSerialNO. 8 (pack 8)", 1182: "BatSerialNO. 7 (pack 8)", 1183: "BatSerialNO. 6 (pack 8)", 1184: "BatSerialNO. 5 (pack 8)", 1185: "BatSerialNO. 4 (pack 8)", 1186: "BatSerialNO. 3 (pack 8)", 1187: "BatSerialNO. 2 (pack 8)", 1188: "BatSerialNO. 1 (pack 8)", 1189: "BatSerialNO. 8 (pack 9)",
    1190: "BatSerialNO. 7 (pack 9)", 1191: "BatSerialNO. 6 (pack 9)", 1192: "BatSerialNO. 5 (pack 9)", 1193: "BatSerialNO. 4 (pack 9)", 1194: "BatSerialNO. 3 (pack 9)", 1195: "BatSerialNO. 2 (pack 9)", 1196: "BatSerialNO. 1 (pack 9)", 1197: "BatSerialNO. 8 (pack 10)", 1198: "BatSerialNO. 7 (pack 10)", 1199: "BatSerialNO. 6 (pack 10)",
    1200: "BatSerialNO. 5 (pack 10)", 1201: "BatSerialNO. 4 (pack 10)", 1202: "BatSerialNO. 3 (pack 10)", 1203: "BatSerialNO. 2 (pack 10)", 1204: "BatSerialNO. 1 (pack 10)",
    1244: "Com version NameH", 1245: "Com version NameL", 1246: "Com version No", 1247: "Com version NameH", 1248: "Com version NameL", 1249: "Com version No",
    3000: "ExportLimitFailedPowerRate", 3001: "New Serial", 3002: "New Serial", 3003: "New Serial", 3004: "New Serial", 3005: "New Serial", 3006: "New Serial", 3007: "New Serial", 3008: "New Serial", 3009: "New Serial NO",
    3010: "New Serial NO", 3011: "New Serial NO", 3012: "New Serial NO", 3013: "New Serial NO", 3014: "New Serial NO", 3015: "New Serial NO", 3016: "DryContactFuncEn", 3017: "DryContactOnRate", 3018: "bWorkMode", 3019: "DryContactOffRate",
    3020: "BoxCtrlInvOrder", 3021: "ExterCommOffGridEn", 3022: "uwBdcStopWorkOfBusVolt", 3023: "bGridType", 3024: "Float charge current limit", 3025: "VbatWarning", 3026: "VbatlowWarnClr", 3027: "Vbat stop for discharge", 3028: "Vbat stop for charge", 3029: "Vbat start for discharge",
    3030: "Vbat constant charge", 3031: "Battemp lower limit d", 3032: "Bat temp upper limit d", 3033: "Bat temp lower limit c", 3034: "Bat temp upper limit c", 3035: "uwUnderFreDischargeDelyTime", 3036: "GridFirstDischargePowerRate", 3037: "GridFirstStopSOC", 3038: "Time 1(xh) start", 3039: "Time 1(xh) end",
    3040: "Time 2(xh) start", 3041: "Time 2(xh) end", 3042: "Time 3(xh) start", 3043: "Time 3(xh) end", 3044: "Time 4(xh) start", 3045: "Time 4(xh) end", 3047: "Bat First Power Rate", 3048: "wBat First stop SOC", 3049: "AcChargeEnable",
    3050: "Time 5(xh) start", 3051: "Time 5(xh) end", 3052: "Time 6(xh) start", 3053: "Time 6(xh) end", 3054: "Time 7(xh) start", 3055: "Time 7(xh) end", 3056: "Time 8(xh) start", 3057: "Time 8(xh) end", 3058: "Time 9(xh) start", 3059: "Time 9(xh) end",
    3070: "BatteryType", 3071: "BatMdlSeria/ParalNum", 3079: "UpsFunEn",
    3080: "UPSVoltSet", 3081: "UPSFreqSet", 3082: "bLoadFirstStopSocSet", 3085: "Com Address", 3086: "BaudRate", 3087: "Serial NO. 1", 3088: "Serial NO. 2", 3089: "Serial NO. 3",
    3090: "Serial NO. 4", 3091: "Serial No. 5", 3092: "Serial No.6", 3093: "Serial No. 7", 3094: "Serial No. 8", 3095: "BdcResetCmd", 3096: "ARKM3 Code", 3097: "ARKM3 Code 2", 3098: "DTC", 3099: "FW Code",
    3100: "FW Code", 3101: "Processor1 FW Vision", 3102: "BusVoltRef", 3103: "ARKM3Ver", 3104: "BMS_MCUVersion", 3105: "BMS_FW", 3106: "BMS_Info", 3107: "BMSCommType", 3108: "Module 4", 3109: "Module 3",
    3110: "Module 2", 3111: "Module 1", 3112: "Reserved", 3113: "unProtocolVer", 3114: "uwCertificationVer",
    3125: "Time Month1", 3126: "Time Month2", 3127: "Time Month3", 3128: "Time Month4", 3129: "Time 1 (us) start",
    3130: "Time 1 (us) end", 3131: "Time 2 (us) start", 3132: "Time 2 (us) end", 3133: "Time 3 (us) start", 3134: "Time 3 (us) start", 3135: "Time 4 (us) end", 3136: "Time 4 (us) start", 3137: "Time 5 (us) start", 3138: "Time 5 (us) end", 3139: "Time 6 (us) start",
    3140: "Time 6 (us) start", 3141: "Time 7 (us) end", 3142: "Time 7 (us) start", 3143: "Time 8 (us) start", 3144: "Time 8 (us) end", 3145: "Time 9 (us) start", 3146: "Time 9 (us) start", 3147: "Time 10 (us) end", 3148: "Time 10 (us) start", 3149: "Time 11 (us) start",
    3150: "Time 11 (us) end", 3151: "Time 12 (us) start", 3152: "Time 12 (us) start", 3153: "Time 13 (us) end", 3154: "Time 13 (us) start", 3155: "Time 14 (us) start", 3156: "Time 14 (us) end", 3157: "Time 15 (us) start", 3158: "Time 15 (us) start", 3159: "Time 16 (us) end",
    3160: "Time 16 (us) start", 3161: "Time 17 (us) start", 3162: "Time 17 (us) end", 3163: "Time 18 (us) start", 3164: "Time 18 (us) start", 3165: "Time 19 (us) end", 3166: "Time 19 (us) start", 3167: "Time 20 (us) start", 3168: "Time 20 (us) end", 3169: "Time 21 (us) start",
    3170: "Time 21 (us) start", 3171: "Time 22 (us) end", 3172: "Time 22 (us) start", 3173: "Time 23 (us) start", 3174: "Time 23 (us) end", 3175: "Time 24 (us) start", 3176: "Time 24 (us) start", 3177: "Time 25 (us) end", 3178: "Time 25 (us) start", 3179: "Time 26 (us) start",
    3180: "Time 26 (us) end", 3181: "Time 27 (us) start", 3182: "Time 27 (us) start", 3183: "Time 28 (us) end", 3184: "Time 28 (us) start", 3185: "Time 29 (us) start", 3186: "Time 29 (us) end", 3187: "Time 30 (us) start", 3188: "Time 30 (us) start", 3189: "Time 31 (us) end",
    3190: "Time 31 (us) start", 3191: "Time 32 (us) start", 3192: "Time 32 (us) end", 3193: "Time 33 (us) start", 3194: "Time 33 (us) start", 3195: "Time 34 (us) end", 3196: "Time 34 (us) start", 3197: "Time 35 (us) start", 3198: "Time 35 (us) end", 3199: "Time 36 (us) start",
    3200: "Time 36 (us) start", 3201: "SpecialDay1", 3202: "SpecialDay1_Time1 start", 3203: "SpecialDay1_Time1 end", 3204: "SpecialDay1_Time2 start", 3205: "SpecialDay1_Time2 end", 3206: "SpecialDay1_Time3 start", 3207: "SpecialDay1_Time3 end", 3208: "SpecialDay1_Time4 start", 3209: "SpecialDay1_Time4 end",
    3210: "SpecialDay1_Time5 start", 3211: "SpecialDay1_Time5 end", 3212: "SpecialDay1_Time6 start", 3213: "SpecialDay1_Time6 end", 3214: "SpecialDay1_Time7 start", 3215: "SpecialDay1_Time7 end", 3216: "SpecialDay1_Time8 start", 3217: "SpecialDay1_Time8 end", 3218: "SpecialDay1_Time9 start", 3219: "SpecialDay1_Time9 end",
    3220: "SpecialDay2", 3221: "SpecialDay2_Time1 start", 3222: "SpecialDay2_Time1 end", 3223: "SpecialDay2_Time2 start", 3224: "SpecialDay2_Time2 end", 3225: "SpecialDay2_Time3 start", 3226: "SpecialDay2_Time3 end", 3227: "SpecialDay2_Time4 start", 3228: "SpecialDay2_Time4 end", 3229: "SpecialDay2_Time5 start",
    3230: "SpecialDay2_Time5 end", 3231: "SpecialDay2_Time6 start", 3232: "SpecialDay2_Time6 end", 3233: "SpecialDay2_Time7 start", 3234: "SpecialDay2_Time7 end", 3235: "SpecialDay2_Time8 start", 3236: "SpecialDay2_Time8 end", 3237: "SpecialDay2_Time9 start", 3238: "SpecialDay2_Time9 end",
}
# fmt: on

print("\nWeb settings -> Read register")
print(
    f"""
+=================================================================================+
|                                  Register dump                                  |
+---------------------------------------------------------------------------------+
|                                                                                 |
""".strip()
)

if register_read_error:
    print(f"|  {register_read_error}")
else:
    # NEW
    print("| Register |  Hex   | Decimal | ASCII | Register name                             |")
    print("+---------------------------------------------------------------------------------+")
    # print register values in int, hex and ascii
    for num_, str_ in register_result.items():
        int_ = int(str_)
        hex_ = f"{int_:04x}".upper()
        try:
            if num_ == 0:  # OnOff
                ascii_ = ["Off", "On", "BDC Off", "BDC On"][int_]
            elif num_ == 3:  # Power limit
                ascii_ = f"{int_}%"
            elif num_ in [6, 7]:  # Watt peak
                int_h = int(register_result.get(6, 0))
                int_l = int(register_result.get(7, 0))
                dword_ = f"{int_h:04x}{int_l:04x}".upper()
                ascii_ = f"{int(dword_, 16) // 10}Wp"
            elif num_ == 118:
                ascii_ = f"S{hex_[:2]}B{hex_[2:]}"
            elif num_ == 119:
                ascii_ = f"D{hex_[:2]}T{hex_[2:]}"
            elif num_ == 120:
                ascii_ = f"P{hex_[:2]}U{hex_[2:]}"
            elif num_ == 121:
                ascii_ = f"M{hex_}"
            else:
                ascii_ = bytes.fromhex(hex_).decode("ascii")
                ascii_ = "".join(c if c.isprintable() else "·" for c in ascii_)
        except ValueError:
            ascii_ = "··"
        print(f"|   {num_:04d}   |  {hex_:4s}  |  {int_:05d}  |{ascii_:^10s}| {register_names.get(num_, ''):38s} | ")

print(
    f"""
+=================================================================================+
""".lstrip()
)


"""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
> Change inverter settings
> ! These are just examples !
> ! Do not execute the code unless you are 100% sure what you are doing !
> ! You might brick your inverter !
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""


def update_setting(name, params: dict):
    # read and log value before overwriting
    if (name == "set_any_reg") and ("param1" in params):
        before: dict = api.read_inverter_setting(
            inverter_id=INVERTER_SN,
            device_type="tlx",
            register_address=params["param1"],
        )
        print(
            f"Changing inverter register '{params['param1']}'\n from {before.get('param1') or before.get('error_message')}\n to {params.get('param2')}\nGOOD LUCK"
        )
    else:
        before: dict = api.read_inverter_setting(
            inverter_id=INVERTER_SN,
            device_type="tlx",
            setting_name=name,
        )
        print(f"Changing inverter setting '{name}'\n from {before}\n to {params}\nGOOD LUCK")
    upd_result = api.update_tlx_inverter_setting(serial_number=INVERTER_SN, setting_type=name, parameter=params)
    print(f"Update returned {upd_result}")
    return upd_result


# #########################################################################
# # If you know what you are doing, uncomment according to your needs

# # Set active power to 100%
# result = update_setting(
#     "pv_active_p_rate", {
#         "param1": 100,  # 100 %
#         "param2": 0,    # "Whether_to_remember": No=0, Yes=1
#         "param3": None})
# # Set reactive power to "PF fixed"
# result = update_setting(
#     "pv_reactive_p_rate", {
#         "param1": 1,    # fixed at 1
#         "param2": 0,    # "PF fixed"
#         "param3": 0})   # "Whether_to_remember": No=0, Yes=1
# # Set reactive power to "Set power factor" with factor 1
# result = update_setting(
#     "pv_reactive_p_rate", {
#         "param1": 1,    # factor 1
#         "param2": 1,    # "Set power factor"
#         "param3": 0})   # "Whether_to_remember": No=0, Yes=1
# # Set reactive power to "Default PF Curve"
# result = update_setting(
#     "pv_reactive_p_rate", {
#         "param1": None,
#         "param2": 2,    # "Default PF Curve"
#         "param3": 0})   # "Whether_to_remember": No=0, Yes=1
# # Set reactive power to "Inductive reactive power ratio" with 100%
# result = update_setting(
#     "pv_reactive_p_rate", {
#         "param1": 100,  # 100%
#         "param2": 5,    # "Inductive reactive power ratio"
#         "param3": 0})   # "Whether_to_remember": No=0, Yes=1
# # Set reactive power to "Conductive reactive power ratio" with 100%
# result = update_setting(
#     "pv_reactive_p_rate", {
#         "param1": 100,  # 100%
#         "param2": 4,    # "Conductive reactive power ratio"
#         "param3": 0})   # "Whether_to_remember": No=0, Yes=1
# # Set reactive power to "QV mode"
# result = update_setting(
#     "pv_reactive_p_rate", {
#         "param1": None,
#         "param2": 6,    # "QV mode"
#         "param3": 0})   # "Whether_to_remember": No=0, Yes=1
# # Set reactive power to "Set reactive power percentage" to 0%
# result = update_setting(
#     "pv_reactive_p_rate", {
#         "param1": 0,    # 0%
#         "param2": 7,    # "Set reactive power percentage"
#         "param3": 0})   # "Whether_to_remember": No=0, Yes=1
# # Set reactive power to "Customize PF Curve"
# result = update_setting(
#     "tlx_custom_pf_curve", {
#         "param1": 255,   # Point 1: Power percentage = 255
#         "param2": 1.0,   # Point 1: Power factor point = 1.0
#         "param3": 255,   # Point 2: Power percentage = 255
#         "param4": 1.0,   # Point 2: Power factor point = 1.0
#         "param5": 255,   # Point 3: Power percentage = 255
#         "param6": 1.0,   # Point 3: Power factor point = 1.0
#         "param7": 255,   # Point 4: Power percentage = 255
#         "param8": 1.0})  # Point 4: Power factor point = 1.0
# # Set "Inverter time" to current local time
# result = update_setting(
#     "pf_sys_year", {
#         "param1": datetime.datetime.now().isoformat(sep=" ")})
# # Set "Over voltage / High Grid Voltage Limit" to 253.1
# result = update_setting(
#     "pv_grid_voltage_high", {
#         "param1": 253.1})
# # Set "Under voltage / Low Grid Voltage Limit" to 195.5
# result = update_setting(
#     "pv_grid_voltage_low", {
#         "param1": 195.5})
# # Set "Overfrequency / High Grid Frequency Limit" to 50.1
# result = update_setting(
#     "pv_grid_frequency_high", {
#         "param1": 50.1})
# # Set "Underfrequency / High Grid Frequency Limit" to 47.65
# result = update_setting(
#     "pv_grid_frequency_low", {
#         "param1": 47.65})
# # Set "Export Limitation" to "Disabled"
# result = update_setting(
#     "backflow_setting", {
#         "param1": 0,   # Disabled
#         "param2": 0,   # W Power (0 for Disabled)
#         "param3": 1})  # unknown - recorded from App
# # Set "Export Limitation" to "Enable meter" with 200W
# result = update_setting(
#     "backflow_setting", {
#         "param1": 1,    # Meter
#         "param2": 200,  # 200W Power
#         "param3": 1})   # unknown - recorded from App
# # Set "Failsafe power limit" to 0
# result = update_setting(
#     "backflow_setting", {
#         "param1": 0.0,  # 0
#         "param2": None,
#         "param3": None})
# # Set "Power Sensor" to "do not connected to power collection" (sic!)
# result = update_setting(
#     "tlx_limit_device", {
#         "param1": 0,  # 0="no device connected", 2="Meter", 3="CT"
#         "param2": None,
#         "param3": None})
# # Set "Operating mode" to "Default"
# result = update_setting(
#     "system_work_mode", {
#         "param1": 0,  # 0="Default", 1="System retrofit", 2="Multi-parallel", 3="System retrofit-simplification"
#         "param2": None,
#         "param3": None})
# # Perform Factory rest
# result = update_setting(
#     "tlx_reset_to_factory", {
#         "param1": None,
#         "param2": None,
#         "param3": None})
# # Set "Regulation parameter setting" -> "Low Frequency Setting"
# result = update_setting(
#     "l_1_freq", {
#         "param1": 47.5,   # AC Frequency Low 1
#         "param2": 47.5})  # AC Frequency Low 2
# # Set "Regulation parameter setting" -> "High Frequency Setting"
# result = update_setting(
#     "h_1_freq", {
#         "param1": 51.5,   # AC Frequency High 1
#         "param2": 51.5})  # AC Frequency High 2
# # Set "Regulation parameter setting" -> "Low Voltage Setting"
# result = update_setting(
#     "l_1_freq", {
#         "param1": 47.5,   # AC Voltage Low 1
#         "param2": 47.5})  # AC Voltage Low 2
# # Set "Regulation parameter setting" -> "High Voltage Setting"
# result = update_setting(
#     "h_1_freq", {
#         "param1": 51.5,   # AC Voltage High 1
#         "param2": 51.5})  # AC Voltage High 2
# # Set "Regulation parameter setting" -> "Loading rate"
# result = update_setting(
#     "loading_rate", {
#         "param1": 9.0})  # 9 %
# # Set "Regulation parameter setting" -> "Restart loading rate"
# result = update_setting(
#     "restart_loading_rate", {
#         "param1": 9.0})  # 9 %
# # Set "Regulation parameter setting" -> Over-frequency start point(f)"
# result = update_setting(
#     "over_fre_drop_point", {
#         "param1": 50.2})  # 50.2 Hz
# # Set "Regulation parameter setting" -> "Over-frequency load reduction Gradient(f)"
# result = update_setting(
#     "over_fre_lored_slope", {
#         "param1": 40.0})  # 40 %
# # Set "Regulation parameter setting" -> "Over-frequency load reduction delay time"
# result = update_setting(
#     "over_fre_lored_delaytime", {
#         "param1": 0.0})  # 0 ms
# # Set "Q (V)" -> "Cut out high Voltage"
# result = update_setting(
#     "qv_h1", {
#         "param1": 236.9})  # 236.9 V
# # Set "Q (V)" -> "Cut into high Voltage"
# result = update_setting(
#     "qv_h1", {
#         "param1": 246.1})  # 246.1 V
# # Set "Q (V)" -> "Cut out low Voltage"
# result = update_setting(
#     "qv_h1", {
#         "param1": 223.1})  # 223.1 V
# # Set "Q (V)" -> "Cut into low Voltage"
# result = update_setting(
#     "qv_h1", {
#         "param1": 213.9})  # 213.9 V
# # Set "Q (V)" -> "Delay time"
# result = update_setting(
#     "qv_h1", {
#         "param1": 10000.0})  # 10000 ms
# # Set "Q (V)" -> "Reactive power percentage"
# result = update_setting(
#     "qv_h1", {
#         "param1": 43.0})  # 43 %
# # Turn inverter on / off
# result = update_setting(
#     "tlx_on_off", {
#         "param1": '0001'})  # '0001'=On, '0000'=Off
# # Turn inverter on / off
# result = update_setting(
#     "tlx_on_off", {
#         "param1": '0001'})  # '0001'=On, '0000'=Off
#
# # Set any register to the desired value
# result = update_setting(
#     "set_any_reg", {
#         "param1": '0',   # register to modify
#         "param2": '1'})  # value to set
#
#
# # # Set inverter output power to 600 Wp
# # #  first we need to enter standby mode to unlock the setting
# # result = update_setting(
# #     "set_any_reg", {
# #         "param1": '0',   # register 0 = On/Off
# #         "param2": '0'})  # 0 = Off
# # #  now change to 800Wp
# # result = update_setting(
# #     "set_any_reg", {
# #         "param1": '121',  # register 121 = Inverter Model ...Mxxxx (xxxx = max power)
# #         "param2": '6'})   # 6 = 600Wp (Watts/100)
# # #  return to On(line) mode
# # result = update_setting(
# #     "set_any_reg", {
# #         "param1": '0',   # register 0 = On/Off
# #         "param2": '1'})  # 1 = On

print("DONE")
