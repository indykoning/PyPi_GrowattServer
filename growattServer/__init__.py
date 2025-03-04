import datetime
from enum import IntEnum
from typing import Optional, Dict, Any, Union, Literal, List

import requests
from random import randint
import warnings
import hashlib

from requests import HTTPError

name = "growattServer"

BATT_MODE_LOAD_FIRST = 0
BATT_MODE_BATTERY_FIRST = 1
BATT_MODE_GRID_FIRST = 2


def hash_password(password: str) -> str:
    """
    Normal MD5, except add c if a byte of the digest is less than 10.

    Args:
        password (str):
            api password in clear text

    Returns:
        str:
            MD5-hashed password
    """
    password_md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
    for i in range(0, len(password_md5), 2):
        if password_md5[i] == "0":
            password_md5 = password_md5[0:i] + "c" + password_md5[i + 1 :]

    return password_md5


class Timespan(IntEnum):
    """
    Many endpoints require a Timespan to be defined.
    Use this enum to provide the data in a convenient way.

    Some endpoints may only support a subset of the Timespan values.
    """

    hour = 0
    day = 1
    month = 2
    year = 3
    total = 4


class TlxDataTypeNeo(IntEnum):
    """
    Enum for the type of data to get from the TLX inverter (tlx_data).

    Following data types have been recorded for a "NEO 800M-X".
    Other inverters might use different values/mappings.
    In that case, define a new data type enum similar to this one
     and extend the Union[] in the tlx_data() method's parameter list.
    """

    power_ac = 6
    power_pv = 1
    voltage_pv1 = 2
    current_pv1 = 3
    voltage_pv2 = 4
    current_pv2 = 5
    # other values will return PV power


class LanguageCode(IntEnum):
    """
    Enum for the language code required by some endpoints

    Values have been reverse-engineered. Feel free to add more if you know more values.
    """

    # Chinese
    cn = 0
    # English
    en = 1
    uk = 1
    us = 1
    # German
    de = 19
    gm = 19
    # Add more if you know any...


class GrowattApi:
    server_url: str = "https://openapi.growatt.com/"
    agent_identifier: str = "Dalvik/2.1.0 (Linux; U; Android 12; https://github.com/indykoning/PyPi_GrowattServer)"

    session: requests.Session

    def __init__(self, add_random_user_id: bool = False, agent_identifier: Optional[str] = None):
        if agent_identifier is not None:
            self.agent_identifier = agent_identifier

        # If a random user id is required, generate a 5-digit number and add it to the user agent
        if add_random_user_id:
            self.agent_identifier += f" - {randint(0, 99999):05d}"

        self.session = requests.Session()
        self.session.hooks = {"response": lambda response, *args, **kwargs: response.raise_for_status()}

        headers = {"User-Agent": self.agent_identifier}
        self.session.headers.update(headers)

    @staticmethod
    def __get_date_string(
        timespan: Optional[Timespan] = None,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
    ) -> str:
        """
        create a date string matching to the Timespan supplied.
        e.g. Timespan.month will create "YYYY-MM" while Timespan.day will create "YYYY-MM-DD"

        By default, this will method return current date in day format

        Args:
            timespan (Optional[Timespan]) = None:
                Timespan definition to use. defaults to Timespan.day if unset
            date (Optional[Union[datetime.datetime, datetime.date]]) = datetime.date.today():
                date to format. defaults to today's date.

        Returns:
            str:
                string of today's date in "YYYY-MM-DD" / "YYYY-MM" / "YYYY" format
        """

        if timespan is not None:
            assert timespan in Timespan

        if date is None:
            date = datetime.datetime.now()

        if timespan == Timespan.total:
            date_str = date.strftime("%Y")
        elif timespan == Timespan.year:
            date_str = date.strftime("%Y")
        elif timespan == Timespan.month:
            date_str = date.strftime("%Y-%m")
        else:
            date_str = date.strftime("%Y-%m-%d")

        return date_str

    def get_url(self, page: str) -> str:
        """
        Simple helper function to get the page URL.

        Args:
            page (str):
                Api endpoint name

        Returns:
            str:
                Api endpoint prefixed with server base url
        """

        return f"{self.server_url.rstrip('/')}/{page}"

    def login(self, username: str, password: str, is_password_hashed: bool = False) -> Dict[str, Any]:
        """
        Authenticate user.

        Args:
            username (str):
                your username
            password (str):
                your password - cleartext or hashed
            is_password_hashed (bool) = False:
                set to True if passing a hashed password

        Returns:
            Dict[str, Any]
                e.g.
                {
                    'app_code': '1',
                    'data': [{'plantId': '{PLANT_ID}', 'plantName': 'My plant name'}],
                    'deviceCount': '1',
                    'isCheckUserAuth': True,
                    'isEicUserAddSmartDevice': True,
                    'isOpenDeviceList': 1,
                    'isOpenDeviceParams': 0,
                    'isOpenSmartFamily': 0,
                    'isViewDeviceInfo': False,
                    'msg': '',
                    'quality': '0',
                    'service': '1',
                    'success': True,
                    'totalData': {},
                    'user': {
                        'accountName': '{USER_NAME}',
                        'accountNameOss': '{USER_NAME}',
                        'activeName': '',
                        'agentCode': '{INSTALLER_CODE}',
                        'appAlias': '',
                        'appType': 'c',
                        'approved': False,
                        'area': 'Europe',
                        'codeIndex': 1,
                        'company': '',
                        'counrty': 'Germany',
                        'cpowerAuth': 'ey...UM',
                        'cpowerToken': '01234567890abcdef000000000000000',
                        'createDate': '2024-11-30 17:00:00',
                        'customerCode': '',
                        'dataAcqList': [],
                        'distributorEnable': '1',
                        'email': '{USER_EMAIL}',
                        'enabled': True,
                        'id': '{USER_ID}',
                        'installerEnable': '1',
                        'inverterGroup': [],
                        'inverterList': [],
                        'isAgent': 0,
                        'isBigCustomer': 0,
                        'isPhoneNumReg': 0,
                        'isValiEmail': 0,
                        'isValiPhone': 0,
                        'kind': 0,
                        'lastLoginIp': '12.3.4.56',
                        'lastLoginTime': '2025-01-31 00:00:00',
                        'lat': '',
                        'lng': '',
                        'mailNotice': True,
                        'nickName': '',
                        'noticeType': '',
                        'parentUserId': 0,
                        'password': '{PASSWORD_HASH}',
                        'phoneNum': '030123456',
                        'registerType': '0',
                        'rightlevel': 1,
                        'roleId': 0,
                        'serverUrl': '',
                        'smsNotice': False,
                        'timeZone': 8,
                        'token': '',
                        'type': 2,
                        'uid': '',
                        'userDeviceType': -1,
                        'userIconPath': '',
                        'userLanguage': 'gm',
                        'vipPoints': 10,
                        'workerCode': '',
                        'wxOpenid': ''
                    },
                    'userId': '{USER_ID}',
                    'userLevel': 1
                }
        """

        if not is_password_hashed:
            password = hash_password(password)

        response = self.session.post(
            self.get_url("newTwoLoginAPI.do"), data={"userName": username, "password": password}
        )
        data = response.json()["back"]

        if data["success"]:
            data.update({"userId": data["user"]["id"], "userLevel": data["user"]["rightlevel"]})

        return data

    def login_v2(
        self,
        username: str,
        password: str,
        is_password_hashed: bool = False,
        language_code: Union[LanguageCode, int] = LanguageCode.en,
        app_type: Optional[str] = "ShinePhone",
        ipvcpc: Optional[str] = None,
        phone_model: Optional[str] = None,
        phone_sn: Optional[str] = None,
        phone_type: Optional[str] = None,
        shine_phone_version: Optional[str] = None,
        system_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Authenticate user to API

        Most parameters are optional (except username and password) and are not needed to set in normal operation.
         Thus they might come in handy for debugging.

        Args:
            username (str):
                your username
            password (str):
                your password - cleartext or hashed
            is_password_hashed (bool) = False:
                set to True if passing a hashed password
            app_type (Optional[str]) = "ShinePhone"
                e.g. "ShinePhone"
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode
            ipvcpc (Optional[str]) = None:
                e.g. "ffffffff-000-0000-0000-000000000000"
            phone_model (Optional[str]= = None:
                e.g. "AB-00000"
            phone_sn (Optional[str]) = None:
                e.g. "ffffffff-0000-0000-00000000000000000"
            phone_type (Optional[str]) = None:
                e.g. "pad"
            shine_phone_version (Optional[str]) = None:
                e.g. "8.2.7.0"
            system_version: (Optional[int]) = None:
                e.g. 9

        Returns:
            Dict[str, Any]
                e.g.
                {
                    'app_code': '1',
                    'data': [{'plantId': '{PLANT_ID}', 'plantName': 'My plant name'}],
                    'deviceCount': '1',
                    'isCheckUserAuth': True,
                    'isEicUserAddSmartDevice': True,
                    'isOpenDeviceList': 1,
                    'isOpenDeviceParams': 0,
                    'isOpenSmartFamily': 0,
                    'isViewDeviceInfo': False,
                    'msg': '',
                    'quality': '0',
                    'service': '1',
                    'success': True,
                    'totalData': {},
                    'user': {
                        'accountName': '{USER_NAME}',
                        'accountNameOss': '{USER_NAME}',
                        'activeName': '',
                        'agentCode': '{INSTALLER_CODE}',
                        'appAlias': '',
                        'appType': 'c',
                        'approved': False,
                        'area': 'Europe',
                        'codeIndex': 1,
                        'company': '',
                        'counrty': 'Germany',
                        'cpowerAuth': 'ey...UM',
                        'cpowerToken': '01234567890abcdef000000000000000',
                        'createDate': '2024-11-30 17:00:00',
                        'customerCode': '',
                        'dataAcqList': [],
                        'distributorEnable': '1',
                        'email': '{USER_EMAIL}',
                        'enabled': True,
                        'id': '{USER_ID}',
                        'installerEnable': '1',
                        'inverterGroup': [],
                        'inverterList': [],
                        'isAgent': 0,
                        'isBigCustomer': 0,
                        'isPhoneNumReg': 0,
                        'isValiEmail': 0,
                        'isValiPhone': 0,
                        'kind': 0,
                        'lastLoginIp': '12.3.4.56',
                        'lastLoginTime': '2025-01-31 00:00:00',
                        'lat': '',
                        'lng': '',
                        'mailNotice': True,
                        'nickName': '',
                        'noticeType': '',
                        'parentUserId': 0,
                        'password': '{PASSWORD_HASH}',
                        'phoneNum': '030123456',
                        'registerType': '0',
                        'rightlevel': 1,
                        'roleId': 0,
                        'serverUrl': '',
                        'smsNotice': False,
                        'timeZone': 8,
                        'token': '',
                        'type': 2,
                        'uid': '',
                        'userDeviceType': -1,
                        'userIconPath': '',
                        'userLanguage': 'gm',
                        'vipPoints': 10,
                        'workerCode': '',
                        'wxOpenid': ''
                    },
                    'userId': '{USER_ID}',
                    'userLevel': 1
                }
        """

        if not is_password_hashed:
            password = hash_password(password)

        url = self.get_url("newTwoLoginAPI.do")
        data = {
            key: value
            for key, value in {
                "userName": username,
                "password": password,
                "newLogin": 1,
                "loginTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": int(datetime.datetime.now().timestamp() * 1000),
                "appType": app_type,
                "ipvcpc": ipvcpc,
                "language": int(language_code),
                "phoneModel": phone_model,
                "phoneSn": phone_sn,
                "phoneType": phone_type,
                "shinephoneVersion": shine_phone_version,
                "systemVersion": system_version,
            }.items()
            if value is not None
        }

        try:
            response = self.session.post(url=url, data=data)
        except HTTPError as e:
            if e.response.status_code == 403:
                # extend error message, to inform about user agent
                e_args = list(e.args)  # cannot edit tuple
                e_args[0] += " (User agent seems to be blocked - see README)"
                e.args = tuple(e_args)
            raise e

        data = response.json().get("back", {})

        # check login successful
        if not data.get("success"):
            error_msg = f"Login failed: Error {data.get('msg')} \"{data.get('error')}\""
            print(error_msg)
            raise Exception(error_msg)

        # stay compatible with login()
        data["userId"] = data.get("user", {}).get("id")
        data["userLevel"] = data.get("user", {}).get("rightlevel")

        return data

    def plant_list(self, user_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get a list of plants connected to this account.

        Args:
            user_id (Union[str,int]):
                The ID of the user.

        Returns:
            Dict[str, Any]:
                "data": A list of plants connected to the account.
                "totalData": Accumulated energy data for all plants connected to the account.
                e.g.
                {
                    'success': True,
                    'data': [
                        {
                            'currentPower': '0 W',
                            'isHaveStorage': 'false',
                            'plantId': '{PLANT_ID}',
                            'plantMoneyText': '1.2 ',
                            'plantName': '{PLANT_NAME}',
                            'todayEnergy': '0 kWh',
                            'totalEnergy': '12.3 kWh'
                        }
                    ],
                    'totalData': {
                        'CO2Sum': '12.34 T',
                        'currentPowerSum': '0 W',
                        'eTotalMoneyText': '1.2 ',
                        'isHaveStorage': 'false',
                        'todayEnergySum': '0 kWh',
                        'totalEnergySum': '12.3 kWh'
                    }
                }
        """

        response = self.session.get(self.get_url("PlantListAPI.do"), params={"userId": user_id}, allow_redirects=False)

        return response.json().get("back", {})

    def plant_detail(
        self,
        plant_id: Union[str, int],
        timespan: Literal[Timespan.day, Timespan.month, Timespan.year, Timespan.total] = Timespan.day,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
    ) -> Dict[str, Any]:
        """
        Get plant details for specified timespan.

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            timespan (Timespan) = Timespan.day:
                The ENUM value conforming to the time window you want
                * day: return daily values for one month
                * month: return monthly values for one year
                * year: return yearly values for six years
            date (Union[datetime.datetime, datetime.date]) = datetime.date.today():
                The date you are interested in.

        Returns:
            Dict[str, Any]:
                A dictionary containing the plant energy metrics for specified timespan.
                e.g.
                {
                    'success': True,
                    'data': {
                        '01': '0.5',
                        '02': '0',
                        #...
                        '31': '0.0',
                    },
                    'plantData': {
                        'currentEnergy': '1 kWh',
                        'plantId': '{PLANT_ID}',
                        'plantMoneyText': '1.2 ',
                        'plantName': '{PLANT_NAME}'
                    },
                }
        """

        date_str = self.__get_date_string(timespan, date)

        response = self.session.get(
            self.get_url("PlantDetailAPI.do"), params={"plantId": plant_id, "type": timespan.value, "date": date_str}
        )

        return response.json().get("back", {})

    def plant_list_two(
        self,
        language_code: Union[LanguageCode, int] = LanguageCode.en,
        page_size: int = 20,
        page_num: int = 1,
        nominal_power: Optional[str] = None,
        plant_name: Optional[str] = None,
        plant_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get a list of all plants with detailed information.

        Args:
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode
            page_size (int) = 20:
                Number of items per page
            page_num (int) = 1:
                Page number
            nominal_power (Optional[str]) = None:
                query by plant peak power
            plant_name (Optional[str]) = None:
                query by plant name
            plant_status (Optional[str]) = None:
                query by plant status

        Returns:
            List[Dict[str, Any]]:
                A list of plants with detailed information.
                e.g.
                [
                    {
                        "alarmValue": 0,
                        "alias": "{PLANT_NAME}",
                        "children": [],
                        "city": "{CITY}",
                        "companyName": "",
                        "country": "",
                        "createDate": {
                            "year": 124,  # 2024 is returned as 124 (sic!)
                            "month": 12,
                            "day": 1,     # weekday
                            "date": 27,
                            "hours": 0,
                            "minutes": 0,
                            "seconds": 0,
                            "timezoneOffset": -480,
                            "time": 1700000000000,
                        },
                        "createDateText": "2024-12-01",
                        "createDateTextA": "",
                        "currentPac": 0,
                        "currentPacStr": "0kW",
                        "currentPacTxt": "0",
                        "dataLogList": [],
                        "defaultPlant": False,
                        "designCompany": "",
                        "deviceCount": 1,
                        "emonthCo2Text": "0",
                        "emonthCoalText": "0",
                        "emonthMoneyText": "0",
                        "emonthSo2Text": "0",
                        "energyMonth": 0,
                        "energyYear": 0,
                        "envTemp": 0,
                        "eToday": 0,
                        "etodayCo2Text": "0",
                        "etodayCoalText": "0",
                        "etodayMoney": 0,
                        "etodayMoneyText": "0",
                        "etodaySo2Text": "0",
                        "eTotal": 12.345678,
                        "etotalCo2Text": "27",
                        "etotalCoalText": "10.8",
                        "etotalFormulaTreeText": "1.49",
                        "etotalMoney": 8.13,
                        "etotalMoneyText": "8.1",
                        "etotalSo2Text": "0.8",
                        "eventMessBeanList": [],
                        "EYearMoneyText": "0",
                        "fixedPowerPrice": 0,
                        "flatPeriodPrice": 0,
                        "formulaCo2": 0,
                        "formulaCoal": 0,
                        "formulaMoney": 0.30,
                        "formulaMoneyStr": "",
                        "formulaMoneyUnitId": "EUR",
                        "formulaSo2": 0,
                        "formulaTree": 0,
                        "gridCompany": "",
                        "gridLfdi": "",
                        "gridPort": "",
                        "gridServerUrl": "",
                        "hasDeviceOnLine": 0,
                        "hasStorage": 0,
                        "id": {PLANT_ID},
                        "imgPath": "css/img/plant.gif",
                        "installMapName": "",
                        "irradiance": 0,
                        "isShare": None,
                        "latitude_d": "",
                        "latitude_f": "",
                        "latitude_m": "",
                        "latitudeText": "null°null?null?",
                        "level": 1,
                        "locationImgName": "",
                        "logoImgName": "",
                        "longitude_d": "",
                        "longitude_f": "",
                        "longitude_m": "",
                        "longitudeText": "null°null?null?",
                        "map_areaId": 0,
                        "map_cityId": 0,
                        "map_countryId": 0,
                        "map_provinceId": 0,
                        "mapCity": "",
                        "mapLat": "",
                        "mapLng": "",
                        "moneyUnitText": "€",
                        "nominalPower": 800,
                        "nominalPowerStr": "0.8kWp",
                        "onLineEnvCount": 0,
                        "pairViewUserAccount": "",
                        "panelTemp": 0,
                        "paramBean": None,
                        "parentID": "",
                        "peakPeriodPrice": 0,
                        "phoneNum": "",
                        "plant_lat": "",
                        "plant_lng": "",
                        "plantAddress": "{STREET}",
                        "plantFromBean": None,
                        "plantImgName": "",
                        "plantName": "{PLANT_NAME}"
                        "plantNmi": "",
                        "plantType": 0,
                        "prMonth": "",
                        "protocolId": "",
                        "prToday": "",
                        "remark": "",
                        "status": 0,
                        "storage_BattoryPercentage": 0,
                        "storage_eChargeToday": 0,
                        "storage_eDisChargeToday": 0,
                        "storage_TodayToGrid": 0,
                        "storage_TodayToUser": 0,
                        "storage_TotalToGrid": 0,
                        "storage_TotalToUser": 0,
                        "tempType": 0,
                        "timezone": 1,
                        "timezoneText": "GMT+1",
                        "timezoneValue": "+1:00",
                        "treeID": "PLANT_{PLANT_ID}",
                        "treeName": "{PLANT_NAME}",
                        "unitMap": None,
                        "userAccount": "{USER_NAME}",
                        "userBean": None,
                        "valleyPeriodPrice": 0,
                        "windAngle": 0,
                        "windSpeed": 0,
                    }
                ]
        """

        response = self.session.post(
            self.get_url("newTwoPlantAPI.do"),
            params={"op": "getAllPlantListTwo"},
            data={
                k: v
                for k, v in {
                    "language": int(language_code),
                    "pageSize": page_size,
                    "toPageNum": page_num,
                    "nominalPower": nominal_power,
                    "plantName": plant_name,
                    "plantStatus": plant_status,
                    "order": 1,
                }.items()
                if v is not None
            },
        )

        return response.json().get("PlantList", [])

    def inverter_data(
        self, inverter_id: str, date: Optional[Union[datetime.datetime, datetime.date]] = None
    ) -> Dict[str, Any]:
        """
        Get inverter data for specified date or today.

        Args:
            inverter_id (str):
                The ID of the inverter.
            date (Optional[Union[datetime.datetime, datetime.date]]) = datetime.date.today():
                date to format. defaults to today's date.

        Returns:
            Dict[str, Any]:
                A dictionary containing the inverter data.
                Might not work for all inverter types.
                e.g. NEO inverter returns {'msg': '501', 'success': False}
        """
        date_str = self.__get_date_string(date=date)
        response = self.session.get(
            self.get_url("newInverterAPI.do"),
            params={"op": "getInverterData", "id": inverter_id, "type": 1, "date": date_str},
        )

        return response.json()

    def inverter_detail(
        self,
        inverter_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed data from PV inverter.
        If you're missing a specific attribute, consider trying inverter_detail_two()

        Args:
            inverter_id (str):
                The ID of the inverter.

        Returns:
            Dict[str, Any]:
                A dictionary containing the inverter details.
                e.g.
                {
                    'again': False,
                    'bigDevice': False,
                    'currentString1': 0,
                    'currentString2': 0,
                    'currentString3': 0,
                    'currentString4': 0,
                    'currentString5': 0,
                    'currentString6': 0,
                    'currentString7': 0,
                    'currentString8': 0,
                    'dwStringWarningValue1': 0,
                    'eRacToday': 0,
                    'eRacTotal': 0,
                    'epv1Today': 0,
                    'epv1Total': 0,
                    'epv2Today': 0,
                    'epv2Total': 0,
                    'epvTotal': 0,
                    'fac': 0,
                    'faultType': 0,
                    'iPidPvape': 0,
                    'iPidPvbpe': 0,
                    'iacr': 0,
                    'iacs': 0,
                    'iact': 0,
                    'id': 0,
                    'inverterBean': None,
                    'inverterId': '',
                    'ipmTemperature': 0,
                    'ipv1': 0,
                    'ipv2': 0,
                    'ipv3': 0,
                    'nBusVoltage': 0,
                    'opFullwatt': 0,
                    'pBusVoltage': 0,
                    'pac': 0,
                    'pacr': 0,
                    'pacs': 0,
                    'pact': 0,
                    'pf': 0,
                    'pidStatus': 0,
                    'powerToday': 0,
                    'powerTotal': 0,
                    'ppv': 0,
                    'ppv1': 0,
                    'ppv2': 0,
                    'ppv3': 0,
                    'rac': 0,
                    'realOPPercent': 0,
                    'status': 0,
                    'statusText': 'Waiting',
                    'strFault': 0,
                    'temperature': 0,
                    'time': '2025-01-02 03:04:05',
                    'timeCalendar': None,
                    'timeTotal': 0,
                    'timeTotalText': '0',
                    'vPidPvape': 0,
                    'vPidPvbpe': 0,
                    'vString1': 0,
                    'vString2': 0,
                    'vString3': 0,
                    'vString4': 0,
                    'vString5': 0,
                    'vString6': 0,
                    'vString7': 0,
                    'vString8': 0,
                    'vacr': 0,
                    'vacs': 0,
                    'vact': 0,
                    'vpv1': 0,
                    'vpv2': 0,
                    'vpv3': 0,
                    'wPIDFaultValue': 0,
                    'wStringStatusValue': 0,
                    'warnCode': 0,
                    'warningValue1': 0,
                    'warningValue2': 0
                }
        """

        response = self.session.get(
            self.get_url("newInverterAPI.do"), params={"op": "getInverterDetailData", "inverterId": inverter_id}
        )

        return response.json()

    def inverter_detail_two(
        self,
        inverter_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed data from PV inverter (alternative endpoint).
        Returns more attributes than inverter_detail()

        Args:
            inverter_id (str):
                The ID of the inverter.

        Returns:
            Dict[str, Any]:
            dict: A dictionary containing the inverter details.
            e.g.
            {
                'data': {
                    'e_rac_today': 0.0,
                    'e_rac_total': 0.0,
                    'e_today': 0.0,
                    'e_total': 0.0,
                    'fac': 0.0,
                    'iacr': 0.0,
                    'iacs': 0.0,
                    'iact': 0.0,
                    'ipv1': 0.0,
                    'ipv2': 0.0,
                    'ipv3': 0.0,
                    'istring1': 0.0,
                    'istring2': 0.0,
                    'istring3': 0.0,
                    'istring4': 0.0,
                    'istring5': 0.0,
                    'istring6': 0.0,
                    'istring7': 0.0,
                    'istring8': 0.0,
                    'pac': 0.0,
                    'pacr': 0.0,
                    'pacs': 0.0,
                    'pact': 0.0,
                    'pidwarning': 0,
                    'ppv': 0.0,
                    'ppv1': 0.0,
                    'ppv2': 0.0,
                    'ppv3': 0.0,
                    'rac': 0.0,
                    'strbreak': 0,
                    'strfault': 0,
                    'strwarning': 0,
                    't_total': 0.0,
                    'vacr': 0.0,
                    'vacs': 0.0,
                    'vact': 0.0,
                    'vpv1': 0.0,
                    'vpv2': 0.0,
                    'vpv3': 0.0,
                    'vstring1': 0.0,
                    'vstring2': 0.0,
                    'vstring3': 0.0,
                    'vstring4': 0.0,
                    'vstring5': 0.0,
                    'vstring6': 0.0,
                    'vstring7': 0.0,
                    'vstring8': 0.0
                },
                'parameterName': 'Fac(Hz),Pac(W),E_Today(kWh),E_Total(kWh),Vpv1(V),Ipv1(A),'
                                 'Ppv1(W),Vpv2(V),Ipv2(A),Ppv2(W),Vpv3(V),Ipv3(A),Ppv3(W),'
                                 'Ppv(W),VacR(...V),Istring5(A),Vstring6(V),Istring6(A),'
                                 'Vstring7(V),Istring7(A),Vstring8(V),Istring8(A),StrFault,'
                                 'StrWarning,StrBreak,PIDWarning'
            }
        """

        response = self.session.get(
            self.get_url("newInverterAPI.do"), params={"op": "getInverterDetailData_two", "inverterId": inverter_id}
        )

        return response.json()

    def inverter_energy_chart(
        self,
        plant_id: Union[str, int],
        inverter_id: str,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
        timespan: Literal[Timespan.day, Timespan.month, Timespan.year, Timespan.total] = Timespan.day,
        filter_type: Literal["all", "ac", "pv1", "pv2", "pv3", "pv4"] = "all",
    ) -> Dict[str, Any]:
        """
        Get energy chart data.

        Values can be seen in the Web frontend at "Module" -> "Module data"
         -> "Daily energy curve"
         -> "Electricity"

        Values can be seen in the App at "Plant" -> "Panel Data"
         -> "Daily performance curve"
         -> "Production"

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            inverter_id (str):
                The ID of the inverter.
            timespan (Timespan) = Timespan.day:
                The ENUM value conforming to the time window you want e.g. hours from today, days, or months.
            date (Union[datetime.datetime, datetime.date]) = datetime.date.today():
                The date you are interested in.
            filter_type (Literal["all", "ac", "pv1", "pv2", "pv3", "pv4"]) = "all":
                Restrict output to
                * "all": all data
                * "ac": AC (W/F/V/I), T (°C), AP (W)
                * "pv{1..4}": PV{1..4} (W/V/I)

        Returns:
            Dict[str, Any]:
                A dictionary containing the energy chart data.
                    If timespan == Timespan.day:
                        return daily energy curve (e.g. PV1/2/3/4 (W/V/A), AC(W/V/A/Hz), Temp (°C))
                    Else:
                        return energy history (e.g. PV1/2/3/4 (kWh), AC(kWH))

        Example response:
            * Timespan.day
            {
                'time': ['08:35', ..., '15:40'],
                'ppv1': ['14.8', ..., '1.9'],
                'vpv1': ['29.0', ..., '29.7'],
                'ipv1': ['0.5', ..., '0'],
                'ppv2': ['0', ..., '0'],
                'vpv2': ['10.0', ..., '9.9'],
                'ipv2': ['0', '..., '0'],
                'ppv3': ['0', ..., '0'],
                'vpv3': ['0', ..., '0'],
                'ipv3': ['0', ..., '0'],
                'ppv4': ['0', ..., '0'],
                'vpv4': ['0', ..., '0']
                'ipv4': ['0', ..., '0'],
                'pac': ['10.4', ..., '7.0'],
                'vac1': ['231.1', ..., '233.0'],
                'iac1': ['0.2', ..., '0.2'],
                'fac': ['50.0', ..., '50.0'],
                'temp1': ['5.7', ..., '9.6'],
            }
            * Timespan.month
                {
                    'time': ['1', ..., '31'],
                    'eacChargeEnergy': ['0', ..., '0'],
                    'epv1Energy': ['0.4', ..., '12.0'],
                    'epv2Energy': ['0.3', ..., '12.3'],
                    'epv3Energy': ['0', ..., '0'],
                    'epv4Energy': ['0', ..., '0']
                }
            * Timespan.year
                {
                    'time': ['1', ..., '12'],
                    '...': see Timespan.month
                }
            * Timespan.total
                {
                    'time': ['2020', ..., '2025'],
                    '...': see Timespan.month
                }
        """

        # dataType:
        # 0: Daily performance curve (supports YYYY-MM-DD)
        # 1: Production              (supports YYYY-MM / YYYY)
        if timespan == Timespan.day:  # 5min performance
            data_type = 0
        else:  # daily/monthly/yearly production
            data_type = 1

        # in contrast to other endpoints, this one always expects a full date string
        date = date or datetime.date.today()
        date_str = date.strftime("%Y-%m-%d")

        # in contrast to other endpoints, this uses a different logic mapping timespan to int
        # 0: Daily performance curve     - day
        # 1: Production (daily values)   - month
        # 2: Production (monthly values) - year
        # 3: Production (yearly values)  - total
        date_type = {
            Timespan.total: 3,
            Timespan.year: 2,
            Timespan.month: 1,
            Timespan.day: 0,
        }[timespan]

        # filter for desired data
        data_level = {
            "all": 0,
            "ac": 1,
            "pv1": 2,
            "pv2": 3,
            "pv3": 4,
            "pv4": 5,
        }.get(filter_type, 0)

        url = self.get_url("componentsApi/getData")
        data = {
            "plantId": plant_id,
            "sn": inverter_id,
            # dataType:
            # 0: Daily energy curve (supports YYYY-MM-DD)
            # 1: Electricity        (supports YYYY-MM / YYYY)
            "dataType": data_type,
            # dateStr
            # YYYY-MM-DD (always)
            "dateStr": date_str,
            # dateType:
            # 0: day (5min values)
            # 1: month (daily values)
            # 2: year (monthly values)
            # 3: total (yearly values)
            "dateType": date_type,
            # dataLevel:
            # 0: All
            # 1: Output
            # 2: PV1
            # 3: PV2
            # 4: PV3
            # 5: PV4
            "dataLevel": data_level,
        }

        response = self.session.post(url=url, data=data)

        return response.json().get("obj") or {}

    def inverter_panel_energy_chart(
        self,
        plant_id: str,
        inverter_id: Optional[str] = None,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
        timespan: Literal[Timespan.day, Timespan.month, Timespan.year, Timespan.total] = Timespan.day,
    ) -> Dict[str, Any]:
        """
        Get energy chart data.
        * for each panel separately (see "box" in response)
        * total for all panels

        Values can be seen in the Web frontend at "Module" -> "Module view"
         -> "Panel power (W)"
         -> "Module power (W)"

        Values can be seen in the App at "Plant" -> "Panel View"
         -> "Panel power"
         -> "Panel production"

        Args:
            plant_id (str):
                The ID of the plant.
            inverter_id (Optional[str]) = None:
                set to filter for a specific inverter
            timespan (Timespan):
                The ENUM value conforming to the time window you want e.g. hours from today, days, or months.
            date (Union[datetime.datetime, datetime.date]) = Timespan.day:
                The date you are interested in.

        Returns:
            Dict[str, Any]:
                A dictionary containing the energy chart data.
                    If timespan == Timespan.day:
                        return daily energy curve (e.g. PV1/2/3/4 (W/V/A), AC(W/V/A/Hz), Temp (°C))
                    Else:
                        return energy history (e.g. PV1/2/3/4 (kWh), AC(kWH))

        Example response:
            * Timespan.day
                {
                    'box': {
                        '09:25': [
                            {
                                'current': '0',
                                'datalogSn': '{DATALOGGER_ID}',
                                'energy': '0',
                                'id': '{INVERTER_ID}-PV1',
                                'name': '{INVERTER_ID_LAST_3_DIGITS}-PV1',
                                'power': '1.2',
                                'voltage': '0',
                                'x': 0,
                                'y': 0
                            },
                            {
                                'current': '0',
                                'datalogSn': '{DATALOGGER_ID}',
                                'energy': '0',
                                'id': '{INVERTER_ID}-PV2',
                                'name': '{INVERTER_ID_LAST_3_DIGITS}-PV2',
                                'power': '0.0',
                                'voltage': '0',
                                'x': 1,
                                'y': 0
                            }
                        ],
                        '09:30': [
                            {'current': '0', ...},
                            {'current': '0', ...}
                        ],
                        ...
                    },
                    'chart': {
                        'power': ['1.2', '3.4', '5.6', ...],
                        'time': ['09:25', '09:30', '09:35', ...]
                    },
                    'checkNeoNum': False
                }
            * Timespan.month
                {
                    'box': {
                        '1': [
                            {
                                'current': '0',
                                'datalogSn': '{DATALOGGER_ID}',
                                'energy': '1.3',
                                'id': '{INVERTER_ID}-PV1',
                                'name': '{INVERTER_ID_LAST_3_DIGITS}-PV1',
                                'power': '0',
                                'voltage': '0',
                                'x': 0,
                                'y': 0
                            },
                            {'current': '0',
                             'datalogSn': '{DATALOGGER_ID}',
                             'energy': '0',
                             'id': '{INVERTER_ID}-PV2',
                             'name': '{INVERTER_ID_LAST_3_DIGITS}-PV2',
                             'power': '0',
                             'voltage': '0',
                             'x': 1,
                             'y': 0
                             }
                        ],
                        '10': [
                            {
                                'current': '0',
                                # ...
                            },
                            {
                                'current': '0',
                                # ...
                            }
                        ],
                        # ...
                    },
                    'chart': {
                        'energy': ['1.2', '0.1', '1.1', ...],
                        'time': ['1', '2', '3', ..., '31']
                    },
                    'checkNeoNum': False
                }
            * Timespan.year
                same as month but with
                'time': ['1', '2', '3', ..., '12']
            * Timespan.total
                same as month but with
                'time': ['2020', '2021', '2022', '2023', '2024', '2025']
        """

        # dataType:
        # 0: panel power (today power)
        # 1: panel production (historical energy)
        if timespan == Timespan.day:  # 5min performance
            data_type = 0
        else:  # daily/monthly/yearly production
            data_type = 1

        # in contrast to other endpoints, this one always expects a full date string
        date = date or datetime.date.today()
        date_str = date.strftime("%Y-%m-%d")

        # in contrast to other endpoints, this uses a different logic mapping timespan to int
        #  and yes, also different from inverter_energy_chart
        # 0: Daily performance curve     - day
        # 1: Production (daily values)   - month
        # 2: Production (monthly values) - year
        # 3: Production (yearly values)  - total
        date_type = {
            Timespan.total: 2,  # historical energy (yearly values)
            Timespan.year: 1,  # historical energy (monthly values)
            Timespan.month: 0,  # historical energy (daily values)
            Timespan.day: 0,  # panel power (today power)
        }[timespan]

        url = self.get_url("componentsApi/getViewData")
        data = {
            "plantId": plant_id,
            # snList:
            # inverter id
            # or 'all'
            "snList": inverter_id or "all",
            # dataType:
            # 0: 5min power (panel power)
            # 1: daily/monthly/yearly energy (panel production)
            "dataType": data_type,
            # dateStr
            # YYYY-MM-DD (always)
            "dateStr": date_str,
            # dateType:
            # 0: day (5min values)
            # 1: month (daily values)
            # 2: year (monthly values)
            # 3: total (yearly values)
            "dateType": date_type,
        }

        response = self.session.post(url=url, data=data)

        return response.json().get("obj") or {}

    def tlx_system_status(self, plant_id: Union[str, int], tlx_id: str) -> Dict[str, Any]:
        """
        Get status of the system

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            tlx_id (str):
                The ID of the TLX inverter.

        Returns:
            Dict[str, Any]:
                A dictionary containing system status.
                e.g.
                {
                    'bMerterConnectFlag': '0',
                    'bdcStatus': '0',
                    'bmsBatteryEnergy': '0kWh',
                    'chargePower': '0.02',
                    'chargePower1': '0',
                    'chargePower2': '0',
                    'dType': '5',
                    'deviceType': '2',
                    'fAc': '50',
                    'invStatus': '-10',
                    'isMasterOne': '0',
                    'lost': 'tlx.status.checking',
                    'operatingMode': '0',
                    'pLocalLoad': '0',
                    'pPv1': '0.02',
                    'pPv2': '0',
                    'pPv3': '0',
                    'pPv4': '0',
                    'pac': '0.01',
                    'pactogrid': '0',
                    'pactouser': '0',
                    'pdisCharge': '0',
                    'pdisCharge1': '0',
                    'pdisCharge2': '0',
                    'pex': '0',
                    'pmax': '0.8',
                    'ppv': '0.02',
                    'prePto': '-1',
                    'priorityChoose': '0',
                    'SOC': '0',
                    'soc1': '0',
                    'SOC2': '0',
                    'soc2': '0',
                    'socType': '1',
                    'status': '1',
                    'tbModuleNum': '0',
                    'tips': '2',
                    'unit': 'kW',
                    'upsFac': '0',
                    'upsVac1': '0',
                    'uwSysWorkMode': '1',
                    'vAc1': '232.1',
                    'vBat': '0',
                    'vPv1': '29.5',
                    'vPv2': '10',
                    'vPv3': '0',
                    'vPv4': '0',
                    'vac1': '232.1',
                    'wBatteryType': '0'
                }
        """

        response = self.session.post(
            self.get_url("newTlxApi.do"), params={"op": "getSystemStatus_KW"}, data={"plantId": plant_id, "id": tlx_id}
        )

        return response.json().get("obj", {})

    def tlx_energy_overview(self, plant_id: Union[str, int], tlx_id: str) -> Dict[str, Any]:
        """
        Get energy overview

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            tlx_id (str):
                The ID of the TLX inverter.

        Returns:
            Dict[str, Any]:
                A dictionary containing energy data.
                e.g.
                {
                    'echargetoday': '0',
                    'echargetotal': '0',
                    'edischargeToday': '0',
                    'edischargeTotal': '0',
                    'elocalLoadToday': '0',
                    'elocalLoadTotal': '0',
                    'epvToday': '0',
                    'epvTotal': '12.3',
                    'etoGridToday': '0',
                    'etogridTotal': '0',
                    'isMasterOne': '0'
                }
        """

        response = self.session.post(
            self.get_url("newTlxApi.do"), params={"op": "getEnergyOverview"}, data={"plantId": plant_id, "id": tlx_id}
        )

        return response.json().get("obj", {})

    def tlx_energy_prod_cons(
        self,
        plant_id: Union[str, int],
        tlx_id: str,
        timespan: Literal[Timespan.hour, Timespan.day, Timespan.month, Timespan.year] = Timespan.hour,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
        language_code: Union[LanguageCode, int] = LanguageCode.en,
    ):
        """
        Get energy production and consumption (KW)

        Note: output format for "hour" differs from other timespans

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            tlx_id (str):
                The ID of the TLX inverter.
            timespan (Timespan):
                The ENUM value conforming to the time window you want
                * hour  => one day, 5min values      (power)
                * day   => one month, daily values   (energy)
                * month => one year,  monthly values (energy)
                * year  => six years, yearly values  (energy)
            date (Optional[Union[datetime.datetime, datetime.date]]) = datetime.date.today():
                The date you are interested in.
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode

        Returns:
            dict: A dictionary containing energy data.
                e.g. (Timespan.hour)
                {
                    'chartData': {
                        '00:00': {'chargePower': 0, 'outP': 0, 'pacToGrid': 0, 'pacToUser': 0, 'pex': 0, 'ppv': 0, 'pself': 0, 'sysOut': 0, 'userLoad': 0},
                        '00:05': {'chargePower': 0, 'outP': 0, 'pacToGrid': 0, 'pacToUser': 0, 'pex': 0, 'ppv': 0, 'pself': 0, 'sysOut': 0, 'userLoad': 0},
                        ...
                        '23:55': {'chargePower': 0, 'outP': 0, 'pacToGrid': 0, 'pacToUser': 0, 'pex': 0, 'ppv': 0, 'pself': 0, 'sysOut': 0, 'userLoad': 0},
                    },
                    'eAcCharge': '0',
                    'eCharge': '0',
                    'eChargeToday': '0',
                    'eChargeToday1': '0',
                    'eChargeToday2': '0',
                    'echarge1': '0',
                    'echargeToat': '0',
                    'elocalLoad': '0',
                    'etouser': '0',
                    'isMasterOne': '0',
                    'keyNames': ['Photovoltaic Output', 'Load Consumption', 'Imported From Grid', 'From Battery'],
                    'newBean': {
                        'dryContactStatus': 0,
                        'exportLimit': 0,
                        'exportLimitPower2': '0kW',
                        'pac': '0kW'
                    },
                    'photovoltaic': '0',
                    'ratio1': '0%',
                    'ratio2': '0%',
                    'ratio3': '0%',
                    'ratio4': '0%',
                    'ratio5': '0%',
                    'ratio6': '0%',
                    'unit': 'kWh',
                    'unit2': 'kW'
                }
                e.g. (Timespan.day)
                {
                    'chartData': {
                        'date': '2020-01-02',
                        'acCharge': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'charge': [0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'eac': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'echarge': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'epv3': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'pacToGrid': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'pex': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'pself': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'sysOut': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    },
                    for other attributes, see "hour" example
                }
                e.g. (Timespan.month)
                {
                    'chartData': {
                        'date': '2025-02',
                        'acCharge': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'charge': [19.8, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'eac': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'echarge': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'epv3': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'pacToGrid': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'pex': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'pself': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'sysOut': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    },
                    for other attributes, see "hour" example
                }
                e.g. (Timespan.year)
                {
                    'chartData': {
                        'date': '2025',
                        'acCharge': [0, 0, 0, 0, 0, 0],
                        'charge': [0, 0, 0, 0, 12.3, 45.6],
                        'eac': [0, 0, 0, 0, 0, 0],
                        'echarge': [0, 0, 0, 0, 0, 0],
                        'epv3': [0, 0, 0, 0, 0, 0],
                        'pacToGrid': [0, 0, 0, 0, 0, 0],
                        'pex': [0, 0, 0, 0, 0, 0],
                        'pself': [0, 0, 0, 0, 0, 0],
                        'sysOut': [0, 0, 0, 0, 0, 0]
                    },
                    for other attributes, see "hour" example
                }
        """

        date_str = self.__get_date_string(timespan, date)

        response = self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getEnergyProdAndCons_KW"},
            data={
                "plantId": plant_id,
                "id": tlx_id,
                "type": timespan.value,
                "date": date_str,
                "language": int(language_code),
            },
        )

        return response.json().get("obj", {})

    def tlx_data(
        self,
        tlx_id: str,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
        tlx_data_type: Union[TlxDataTypeNeo, int] = 1,
    ) -> Dict[str, Any]:
        """
        Get TLX inverter data for specified date or today.

        Args:
            tlx_id (str):
                The ID of the TLX inverter.
            date (Union[datetime.datetime, datetime.date]) = datetime.date.today():
                The date for which to retrieve the chart data.
            tlx_data_type (Union[TlxDataTypeNeo, int]) = 1:
                The type of data to get from the TLX inverter.
                see TlxDataTypeNeo

        Returns:
            Dict[str, Any]:
                A dictionary containing chart data and current energy.
                e.g.
                {
                    'date': '2025-01-31',
                    'dryContactStatus': 0,
                    'eToday': '0',
                    'eTotal': '12.1',
                    'exportLimit': 0,
                    'exportLimitPower': '0',
                    'exportLimitPower2': '0',
                    'invPacData': {
                        '2025-01-31 08:50': 0,
                        '2025-01-31 09:20': 7.3,
                        ...
                        '2025-01-31 23:25': 0
                    },
                    'nominalPower': '800',
                    'power': '0'
                }
        """

        date_str = self.__get_date_string(date=date)
        response = self.session.get(
            self.get_url("newTlxApi.do"),
            params={"op": "getTlxData", "id": tlx_id, "type": int(tlx_data_type), "date": date_str},
        )

        return response.json()

    def tlx_energy_chart(
        self,
        tlx_id: str,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
        timespan: Literal[Timespan.month, Timespan.year, Timespan.total] = Timespan.month,
    ) -> Dict[str, Optional[float]]:
        """
        Get monthly/yearly/total AC-Power values as shown in App->Inverter->"Real time data" chart.

        These values differ from the ones shown in tlx_energy_prod_cons().
        This is not an API issue but differing values can also be seen in the App and Web frontends.

        Info: API might not return all days/months/years as days without data are not returned.

        Args:
            tlx_id (str):
                The ID of the TLX inverter.
            date (Union[datetime.datetime, datetime.date]) = datetime.date.today():
                The date for which to retrieve the chart data.
            timespan (Timespan):
                The ENUM value conforming to the time window you want
                * Timespan.month: month overview providing daily values
                * Timespan.year: year overview providing monthly values
                * Timespan.total: total overview providing yearly values

        Returns:
            Dict[str, Optional[float]]:
                A dictionary containing the energy data.
                e.g.
                {'2024': 9.1, '2025': 18.7}
        """

        date_str = self.__get_date_string(timespan=timespan, date=date)

        # API uses different actions for different timespans
        # Parameters as recorded from App
        if timespan == Timespan.total:
            params = {"op": "getTotalPac", "id": tlx_id}
        elif timespan == Timespan.year:
            params = {"op": "getYearPac", "id": tlx_id, "date": date_str}
        elif timespan == Timespan.month:
            params = {"op": "getMonthPac", "id": tlx_id, "date": date_str}
        else:
            raise ValueError(f"Unsupported timespan: {timespan}")

        response = self.session.get(self.get_url("newTlxApi.do"), params=params)

        return response.json()

    def tlx_detail(self, tlx_id: str) -> Dict[str, Any]:
        """
        Get detailed data from TLX inverter.

        Args:
            tlx_id (str):
                The ID of the TLX inverter.

        Returns:
            Dict[str, Any]:
                A dictionary containing the detailed TLX inverter data.
                e.g.
                {
                    'data': {
                        'address': 0, 'again': False, 'alias': None,
                        'bMerterConnectFlag': 0, 'batSn': None, 'batteryNo': 0,
                        'batterySN': None, 'bdc1ChargePower': 0, 'bdc1ChargeTotal': 0,
                        'bdc1DischargePower': 0, 'bdc1DischargeTotal': 0,
                        'bdc1FaultType': 0, 'bdc1Ibat': 0, 'bdc1Ibb': 0, 'bdc1Illc': 0,
                        'bdc1Mode': 0, 'bdc1Soc': 0, 'bdc1Status': 0, 'bdc1Temp1': 0,
                        'bdc1Temp2': 0, 'bdc1Vbat': 0, 'bdc1Vbus1': 0, 'bdc1Vbus2': 0,
                        'bdc1WarnCode': 0, 'bdc2ChargePower': 0, 'bdc2ChargeTotal': 0,
                        'bdc2DischargePower': 0, 'bdc2DischargeTotal': 0, 'bdc2FaultType': 0,
                        'bdc2Ibat': 0, 'bdc2Ibb': 0, 'bdc2Illc': 0, 'bdc2Mode': 0,
                        'bdc2Soc': 0, 'bdc2Status': 0, 'bdc2Temp1': 0, 'bdc2Temp2': 0,
                        'bdc2Vbat': 0, 'bdc2Vbus1': 0, 'bdc2Vbus2': 0, 'bdc2WarnCode': 0,
                        'bdcBusRef': 0, 'bdcDerateReason': 0, 'bdcFaultSubCode': 0,
                        'bdcStatus': 0, 'bdcVbus2Neg': 0, 'bdcWarnSubCode': 0, 'bgridType': 0,
                        'bmsCommunicationType': 0, 'bmsCvVolt': 0, 'bmsError2': 0,
                        'bmsError3': 0, 'bmsError4': 0, 'bmsFaultType': 0, 'bmsFwVersion': '',
                        'bmsIbat': 0, 'bmsIcycle': 0, 'bmsInfo': 0, 'bmsIosStatus': 0,
                        'bmsMaxCurr': 0, 'bmsMcuVersion': '', 'bmsPackInfo': 0, 'bmsSoc': 0,
                        'bmsSoh': 0, 'bmsStatus': 0, 'bmsTemp1Bat': 0, 'bmsUsingCap': 0,
                        'bmsVbat': 0, 'bmsVdelta': 0, 'bmsWarn2': 0, 'bmsWarnCode': 0,
                        'bsystemWorkMode': 0,
                        'calendar': None,
                        'dataLogSn': None, 'day': None, 'dcVoltage': 0, 'dciR': 0, 'dciS': 0,
                        'dciT': 0, 'debug1': None, 'debug2': None, 'deratingMode': 0,
                        'dryContactStatus': 0,
                        'eacChargeToday': 0, 'eacChargeTotal': 0, 'eacToday': 0, 'eacTotal': 0,
                        'echargeToday': 0, 'echargeTotal': 0, 'edischargeToday': 0,
                        'edischargeTotal': 0, 'eex1Today': 0, 'eex1Total': 0, 'eex2Today': 0,
                        'eex2Total': 0, 'elocalLoadToday': 0, 'elocalLoadTotal': 0, 'epsFac': 0,
                        'epsIac1': 0, 'epsIac2': 0, 'epsIac3': 0, 'epsPac': 0, 'epsPac1': 0,
                        'epsPac2': 0, 'epsPac3': 0, 'epsPf': 0, 'epsVac1': 0, 'epsVac2': 0,
                        'epsVac3': 0, 'epv1Today': 0, 'epv1Total': 0, 'epv2Today': 0,
                        'epv2Total': 0, 'epv3Today': 0, 'epv3Total': 0, 'epv4Today': 0,
                        'epv4Total': 0, 'epvTotal': 0, 'errorText': 'Unknown',
                        'eselfToday': 0, 'eselfTotal': 0, 'esystemToday': 0, 'esystemTotal': 0,
                        'etoGridToday': 0, 'etoGridTotal': 0, 'etoUserToday': 0,
                        'etoUserTotal': 0,
                        'fac': 0, 'faultType': 0, 'faultType1': 0,
                        'gfci': 0,
                        'iac1': 0, 'iac2': 0, 'iac3': 0, 'iacr': 0, 'invDelayTime': 0,
                        'ipv1': 0, 'ipv2': 0, 'ipv3': 0, 'ipv4': 0, 'isAgain': False,
                        'iso': 0, 'loadPercent': 0, 'lost': True,
                        'mtncMode': 0, 'mtncRqst': 0,
                        'nBusVoltage': 0, 'newWarnCode': 0, 'newWarnSubCode': 0,
                        'opFullwatt': 0, 'operatingMode': 0,
                        'pBusVoltage': 0, 'pac': 0, 'pac1': 0, 'pac2': 0, 'pac3': 0,
                        'pacToGridTotal': 0, 'pacToLocalLoad': 0, 'pacToUserTotal': 0,
                        'pacr': 0, 'pex1': 0, 'pex2': 0, 'pf': 0, 'ppv': 0, 'ppv1': 0,
                        'ppv2': 0, 'ppv3': 0, 'ppv4': 0, 'pself': 0, 'psystem': 0,
                        'realOPPercent': 0,
                        'serialNum': None, 'soc1': 0, 'soc2': 0, 'status': 0,
                        'statusText': 'Standby', 'sysFaultWord': 0, 'sysFaultWord1': 0,
                        'sysFaultWord2': 0, 'sysFaultWord3': 0, 'sysFaultWord4': 0,
                        'sysFaultWord5': 0, 'sysFaultWord6': 0, 'sysFaultWord7': 0,
                        'tMtncStrt': None, 'tWinEnd': None, 'tWinStart': None,
                        'temp1': 0, 'temp2': 0, 'temp3': 0, 'temp4': 0, 'temp5': 0,
                        'time': '', 'timeTotal': 0, 'tlxBean': None,
                        'totalWorkingTime': 0,
                        'uwSysWorkMode': 0,
                        'vac1': 0, 'vac2': 0, 'vac3': 0, 'vacRs': 0, 'vacSt': 0,
                        'vacTr': 0, 'vacr': 0, 'vacrs': 0, 'vpv1': 0, 'vpv2': 0,
                        'vpv3': 0, 'vpv4': 0,
                        'warnCode': 0, 'warnCode1': 0, 'warnText': 'Unknown',
                        'winMode': 0, 'winOffGridSOC': 0, 'winOnGridSOC': 0,
                        'winRequest': 0, 'withTime': False
                    },
                    'parameterName': 'Fac(Hz),Pac(W),Ppv(W),Ppv1(W),Ppv2(W),Vpv1(V),Ipv1(A),Vpv2(V),Ipv2(A),Vac1(V),Iac1(A),Pac1(W),VacRs(V),EacToday(kWh),EacTotal
                                      ...GridTotal(kWh),ElocalLoadToday(kWh),ElocalLoadTotal(kWh),Epv1Total(kWh),Epv2Total(kWh),EpvTotal(kWh),BsystemWorkMode,BgridType'
                }
        """

        response = self.session.get(self.get_url("newTlxApi.do"), params={"op": "getTlxDetailData", "id": tlx_id})

        return response.json()

    def tlx_params(self, tlx_id: str) -> Dict[str, Any]:
        """
        Get parameters for TLX inverter.

        Args:
            tlx_id (str):
                The ID of the TLX inverter.

        Returns:
            Dict[str, Any]:
                A dictionary containing the TLX inverter parameters.
                e.g.
                {
                    'inverterType': 'NEO 800M-X',
                    'region': '',
                    'newBean': {
                        'addr': 1,
                        'alias': '',
                        'bagingTestStep': 0,
                        'batParallelNum': 0,
                        'batSeriesNum': 0,
                        'batSysEnergy': 0,
                        'batTempLowerLimitC': 0,
                        'batTempLowerLimitD': 0,
                        'batTempUpperLimitC': 0,
                        'batTempUpperLimitD': 0,
                        'batteryType': 0,
                        'bctAdjust': 0,
                        'bctMode': 0,
                        'bcuVersion': '',
                        'bdc1Model': '0',
                        'bdc1Sn': '',
                        'bdc1Version': '\x00\x00\x00\x00-0',
                        'bdcAuthversion': 0,
                        'bdcMode': 0,
                        'bmsCommunicationType': 0,
                        'bmsSoftwareVersion': '',
                        'children': [],
                        'comAddress': 1,
                        'communicationVersion': 'GJAA-0003',
                        'countrySelected': 1,
                        'dataLogSn': '{DATALOGGER_SN}',
                        'deviceType': 5,
                        'dtc': 5203,
                        'eToday': 0,
                        'eTotal': 12.3456789,
                        'energyDayMap': {},
                        'energyMonth': 0,
                        'energyMonthText': '0',
                        'fwVersion': 'GJ1.0',
                        'groupId': -1,
                        'hwVersion': '',
                        'id': 0,
                        'imgPath': './css/img/status_gray.gif',
                        'innerVersion': 'GJAA03xx',
                        'lastUpdateTime': {
                            'year': 125,   # 2015 is 125 (sic!)
                            'month': 0,
                            'date': 30,
                            'day': 4,  # weekday
                            'hours': 17,
                            'minutes': 11,
                            'seconds': 23,
                            'time': 1738228283000,
                            'timezoneOffset': -480,
                        },
                        'lastUpdateTimeText': '2025-01-02 03:04:05',
                        'level': 4,
                        'liBatteryFwVersion': '',
                        'liBatteryManufacturers': '',
                        'location': '',
                        'lost': True,
                        'manufacturer': '   PV Inverter  ',
                        'modbusVersion': 307,
                        'model': 123456789012345678,
                        'modelText': 'S00B00D00T00P0FU00M0000',
                        'monitorVersion': '',
                        'mppt': 0,
                        'optimezerList': [],
                        'pCharge': 0,
                        'pDischarge': 0,
                        'parentID': 'LIST_{DATALOGGER_SN}_22',
                        'plantId': 0,
                        'plantname': '',
                        'pmax': 800,
                        'portName': 'port_name',
                        'power': 0,
                        'powerMax': '',
                        'powerMaxText': '',
                        'powerMaxTime': '',
                        'priorityChoose': 0,
                        'record': None,
                        'restartTime': 65,
                        'safetyVersion': 0,
                        'serialNum': '{INVERTER_SN}',
                        'startTime': 65,
                        'status': -1,
                        'statusText': 'tlx.status.lost',
                        'strNum': 0,
                        'sysTime': '',
                        'tcpServerIp': '12.123.123.12',
                        'timezone': 8,
                        'tlxSetbean': None,
                        'trakerModel': 0,
                        'treeID': 'ST_{INVERTER_SN}',
                        'treeName': '',
                        'updating': False,
                        'userName': '',
                        'vbatStartForDischarge': 0,
                        'vbatStopForCharge': 0,
                        'vbatStopForDischarge': 0,
                        'vbatWarnClr': 0,
                        'vbatWarning': 0,
                        'vnormal': 280,
                        'vppOpen': 0,
                        'wselectBaudrate': 0
                    }
                }
        """

        response = self.session.get(self.get_url("newTlxApi.do"), params={"op": "getTlxParams", "id": tlx_id})

        return response.json()

    def tlx_all_settings(self, tlx_id: str, kind: int = 0) -> Dict[str, Any]:
        """
        Get all possible settings from TLX inverter.

        Args:
            tlx_id (str):
                The ID of the TLX inverter.
            kind (int) = 0:
                Unknown parameter seen in App's HTTP traffic

        Returns:
            Dict[str, Any]: A dictionary containing all possible settings for the TLX inverter.
            e.g.
            {
                'acChargeEnable': '0', 'ac_charge': '0', 'activeRate': '100',
                'afci_enabled': '-1', 'afci_reset': '-1', 'afci_self_check': '-1',
                'afci_thresholdd': '-1', 'afci_thresholdh': '-1',
                'afci_thresholdl': '-1',
                'brazilRule': '0',
                'chargePowerCommand': '0', 'charge_power': '0', 'charge_stop_soc': '0',
                'compatibleFlag': '0', 'delay_time': '10000.0',
                'demand_manage_enable': '0', 'disChargePowerCommand': '0',
                'discharge_power': '0', 'discharge_stop_soc': '0', 'dtc': '5203',
                'exportLimit': '0', 'exportLimitPowerRateStr': '0.0',
                'fail_safe_curr': '0', 'fft_threshold_count': '-1',
                'forcedStopSwitch1': '0', 'forcedStopSwitch2': '0',
                'forcedStopSwitch3': '0', 'forcedStopSwitch4': '0',
                'forcedStopSwitch5': '0', 'forcedStopSwitch6': '0',
                'forcedStopSwitch7': '0', 'forcedStopSwitch8': '0',
                'forcedStopSwitch9': '0', 'forcedTimeStart1': '0:0',
                'forcedTimeStart2': '0:0', 'forcedTimeStart3': '0:0',
                'forcedTimeStart4': '0:0', 'forcedTimeStart5': '0:0',
                'forcedTimeStart6': '0:0', 'forcedTimeStart7': '0:0',
                'forcedTimeStart8': '0:0', 'forcedTimeStart9': '0:0',
                'forcedTimeStop1': '0:0', 'forcedTimeStop2': '0:0',
                'forcedTimeStop3': '0:0', 'forcedTimeStop4': '0:0',
                'forcedTimeStop5': '0:0', 'forcedTimeStop6': '0:0',
                'forcedTimeStop7': '0:0', 'forcedTimeStop8': '0:0',
                'forcedTimeStop9': '0:0',
                'gen_charge_enable': '0', 'gen_ctrl': '0', 'gen_rated_power': '0',
                'grid_type': '0',
                'h_1_freq_1': '51.5', 'h_1_freq_2': '51.5', 'h_1_volt_1': '287.5',
                'h_1_volt_2': '287.5',
                'isLGBattery': '0',
                'l_1_freq': '47.5', 'l_1_freq_1': '47.5', 'l_1_freq_2': '47.5',
                'l_1_volt_1': '184.0', 'l_1_volt_2': '103.5', 'l_2_freq': '47.5',
                'loading_rate': '9.0',
                'max_allow_curr': '0', 'modbusVersion': '307',
                'normalPower': '800',
                'off_net_box': '0', 'onGridMode': '-1', 'onGridStatus': '-1',
                'on_grid_discharge_stop_soc': '0',
                'peak_shaving_enable': '0', 'pf_sys_year': '2025-01-02 03:04:05',
                'power_down_enable': '0', 'pre_pto': '0', 'priorityChoose': '0',
                'prot_enable': '0', 'pvPfCmdMemoryState': '0',
                'pv_grid_frequency_high': '50.1', 'pv_grid_frequency_low': '47.65',
                'pv_grid_voltage_high': '253.0', 'pv_grid_voltage_low': '195.5',
                'q_percent_max': '43.0', 'qv_h1': '236.9', 'qv_h2': '246.1',
                'qv_l1': '223.1', 'qv_l2': '213.9',
                'restart_loading_rate': '9.0',
                'safetyCorrespondNumList': [], 'safetyNum': '0',
                'safety_correspond_num': '0', 'season1MonthTime': '0_0_0',
                'season1Time1': '0_0_0_0_0_0_0', 'season1Time2': '0_0_0_0_0_0_0',
                'season1Time3': '0_0_0_0_0_0_0', 'season1Time4': '0_0_0_0_0_0_0',
                'season1Time5': '0_0_0_0_0_0_0', 'season1Time6': '0_0_0_0_0_0_0',
                'season1Time7': '0_0_0_0_0_0_0', 'season1Time8': '0_0_0_0_0_0_0',
                'season1Time9': '0_0_0_0_0_0_0', 'season2MonthTime': '0_0_0',
                'season2Time1': '0_0_0_0_0_0_0', 'season2Time2': '0_0_0_0_0_0_0',
                'season2Time3': '0_0_0_0_0_0_0', 'season2Time4': '0_0_0_0_0_0_0',
                'season2Time5': '0_0_0_0_0_0_0', 'season2Time6': '0_0_0_0_0_0_0',
                'season2Time7': '0_0_0_0_0_0_0', 'season2Time8': '0_0_0_0_0_0_0',
                'season2Time9': '0_0_0_0_0_0_0', 'season3MonthTime': '0_0_0',
                'season3Time1': '0_0_0_0_0_0_0', 'season3Time2': '0_0_0_0_0_0_0',
                'season3Time3': '0_0_0_0_0_0_0', 'season3Time4': '0_0_0_0_0_0_0',
                'season3Time5': '0_0_0_0_0_0_0', 'season3Time6': '0_0_0_0_0_0_0',
                'season3Time7': '0_0_0_0_0_0_0', 'season3Time8': '0_0_0_0_0_0_0',
                'season3Time9': '0_0_0_0_0_0_0', 'season4MonthTime': '0_0_0',
                'season4Time1': '0_0_0_0_0_0_0', 'season4Time2': '0_0_0_0_0_0_0',
                'season4Time3': '0_0_0_0_0_0_0', 'season4Time4': '0_0_0_0_0_0_0',
                'season4Time5': '0_0_0_0_0_0_0', 'season4Time6': '0_0_0_0_0_0_0',
                'season4Time7': '0_0_0_0_0_0_0', 'season4Time8': '0_0_0_0_0_0_0',
                'season4Time9': '0_0_0_0_0_0_0', 'seasonYearTime': '0_0_0',
                'showPeakShaving': '0', 'special1MonthTime': '0_0_0',
                'special1Time1': '0_0_0_0_0_0', 'special1Time2': '0_0_0_0_0_0',
                'special1Time3': '0_0_0_0_0_0', 'special1Time4': '0_0_0_0_0_0',
                'special1Time5': '0_0_0_0_0_0', 'special1Time6': '0_0_0_0_0_0',
                'special1Time7': '0_0_0_0_0_0', 'special1Time8': '0_0_0_0_0_0',
                'special1Time9': '0_0_0_0_0_0', 'special2MonthTime': '0_0_0',
                'special2Time1': '0_0_0_0_0_0', 'special2Time2': '0_0_0_0_0_0',
                'special2Time3': '0_0_0_0_0_0', 'special2Time4': '0_0_0_0_0_0',
                'special2Time5': '0_0_0_0_0_0', 'special2Time6': '0_0_0_0_0_0',
                'special2Time7': '0_0_0_0_0_0', 'special2Time8': '0_0_0_0_0_0',
                'special2Time9': '0_0_0_0_0_0', 'sysMtncAvail': '0',
                'system_work_mode': '0',
                'time1Mode': '0', 'time2Mode': '0', 'time3Mode': '0', 'time4Mode': '0',
                'time5Mode': '0', 'time6Mode': '0', 'time7Mode': '0', 'time8Mode': '0',
                'time9Mode': '0', 'time_segment1': '0_0:0_0:0_0',
                'time_segment2': '0_0:0_0:0_0', 'time_segment3': '0_0:0_0:0_0',
                'time_segment4': '0_0:0_0:0_0', 'time_segment5': '0_0:0_0:0_0',
                'time_segment6': '0_0:0_0:0_0', 'time_segment7': '0_0:0_0:0_0',
                'time_segment8': '0_0:0_0:0_0', 'time_segment9': '0_0:0_0:0_0',
                'tlx_ac_discharge_frequency': '0', 'tlx_ac_discharge_voltage': '0',
                'tlx_backflow_default_power': '0.0', 'tlx_cc_current': '0.0',
                'tlx_cv_voltage': '0.0', 'tlx_dry_contact_enable': '0',
                'tlx_dry_contact_off_power': '0.0', 'tlx_dry_contact_power': '0.0',
                'tlx_exter_comm_Off_GridEn': '0', 'tlx_lcd_Language': '0',
                'tlx_limit_device': '0', 'tlx_off_grid_enable': '0', 'tlx_on_off': '1',
                'tlx_one_key_set_bdc_mode': '0', 'tlx_pf': '0.0',
                'tlx_pflinep1_lp': '255', 'tlx_pflinep1_pf': '1.0',
                'tlx_pflinep2_lp': '255', 'tlx_pflinep2_pf': '1.0',
                'tlx_pflinep3_lp': '255', 'tlx_pflinep3_pf': '1.0',
                'tlx_pflinep4_lp': '255', 'tlx_pflinep4_pf': '1.0',
                'ub_ac_charging_stop_soc': '0', 'ub_peak_shaving_backup_soc': '0',
                'usBatteryType': '0', 'uw_ac_charging_max_power_limit': '0.0',
                'uw_demand_mgt_downstrm_power_limit': '0.0',
                'uw_demand_mgt_revse_power_limit': '0.0',
                'wchargeSOCLowLimit': '0', 'wdisChargeSOCLowLimit': '0',
                'winModeEndTime': '', 'winModeFlag': '0',
                'winModeOffGridDischargeStopSOC': '10',
                'winModeOnGridDischargeStopSOC': '10', 'winModeStartTime': '',
                'winterOrMaintain': '0',
                'yearSettingFlag': '0', 'year_time1': '0_0_0_0_0_0_0', 'year_time2': '',
                'year_time3': '', 'year_time4': '', 'year_time5': '', 'year_time6': '',
                'year_time7': '', 'year_time8': '', 'year_time9': ''
            }
        """

        response = self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getTlxSetData"},
            data={
                "serialNum": tlx_id,
                "kind": kind,
            },
        )

        return response.json().get("obj", {}).get("tlxSetBean")

    def tlx_enabled_settings(
        self,
        tlx_id: str,
        language_code: Union[LanguageCode, int] = LanguageCode.en,
        device_type_id: int = 5,  # see docstring
    ) -> Dict[str, Any]:
        """
        Get "Enabled settings" from TLX inverter.
        Also retrieves the password required to change settings.

        Args:
            tlx_id (str):
                The ID of the TLX inverter.
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode
            device_type_id (int) = 5:
                device type id as returned by e.g.
                - device_list()[0]["type2"]
                - plant_info()["invList"][0]["type2"]
                - tlx_params()["newBean"]["deviceType"]
                - tlx_system_status()["dType"]
                e.g. 5 = TLX inverter (NEO)

        Returns:
            Dict[str, Any]:
                A dictionary containing the enabled settings.
                e.g.
                {
                    'haveAfci': False,
                    'settings_password': 'growatt********',
                    'switch': True,
                    'enable': {
                        'ac_charge': '1',
                        'backflow_setting': '1',
                        'charge_power': '1', 'charge_stop_soc': '1',
                        'discharge_power': '1', 'discharge_stop_soc': '1',
                        'pf_sys_year': '1','pv_active_p_rate': '1',
                        'pv_grid_frequency_high': '1', 'pv_grid_frequency_low': '1',
                        'pv_grid_voltage_high': '1', 'pv_grid_voltage_low': '1',
                        'pv_reactive_p_rate': '1',
                        'time_segment1': '1', 'time_segment2': '1', 'time_segment3': '1',
                        'time_segment4': '1', 'time_segment5': '1', 'time_segment6': '1',
                        'time_segment7': '1', 'time_segment8': '1', 'time_segment9': '1',
                        'tlx_ac_discharge_frequency': '1',
                        'tlx_ac_discharge_time_period': '1', 'tlx_ac_discharge_voltage': '1',
                        'tlx_backflow_default_power': '1', 'tlx_cc_current': '1',
                        'tlx_custom_pf_curve': '1', 'tlx_cv_voltage': '1',
                        'tlx_dry_contact_enable': '1', 'tlx_dry_contact_off_power': '1',
                        'tlx_dry_contact_power': '1', 'tlx_exter_comm_Off_GridEn': '1',
                        'tlx_lcd_Language': '1', 'tlx_limit_device': '1',
                        'tlx_off_grid_enable': '1', 'tlx_on_off': '0',
                        'tlx_optimezer_set_param_multi': '1', 'tlx_reset_to_factory': '1'
                    },
                }
        """

        string_time = datetime.datetime.now().strftime("%Y-%m-%d")

        url = self.get_url("newLoginAPI.do")
        params = {"op": "getSetPass"}
        data = {
            "deviceSn": tlx_id,
            "type": device_type_id,
            "stringTime": string_time,
            "language": int(language_code),
        }

        response = self.session.post(url=url, params=params, data=data)

        response_json = response.json()

        if response_json.get("result") == 1:  # extract settings pw
            settings_pw = response_json.get("msg")
        else:
            settings_pw = datetime.date.today().strftime("growatt%Y%m%d")

        data = response_json.get("obj") or {}
        data["settings_password"] = settings_pw  # include settings pw

        return data

    def tlx_battery_info(
        self,
        serial_num: str,
        language_code: Union[LanguageCode, int] = LanguageCode.en,
    ) -> Dict[str, Any]:
        """
        Get battery information.

        Args:
            serial_num (str):
                The serial number of the battery.
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode

        Returns:
            Dict[str, Any]:
                A dictionary containing the battery information.
        """
        response = self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getBatInfo"},
            data={"lan": int(language_code), "serialNum": serial_num},
        )

        return response.json().get("obj", {})

    def tlx_battery_info_detailed(
        self,
        plant_id: Union[str, int],
        serial_num: str,
        language_code: Union[LanguageCode, int] = LanguageCode.en,
    ) -> Dict[str, Any]:
        """
        Get detailed battery information.

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            serial_num (str):
                The serial number of the battery.
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode

        Returns:
            Dict[str, Any]:
                A dictionary containing the detailed battery information.
                e.g.
                {
                    'data': {
                        'bmNum': '0',
                        'chargeOrDisPower': '0',
                        'dischargeTotal': '0',
                        'errorCode': '0',
                        'errorSubCode': '0',
                        'soc': '0',
                        'status': '0',
                        'systemWorkStatus': '0',
                        'warnCode': '0',
                        'warnSubCode': '0'
                    },
                    'parameterName': ''
                }
        """

        response = self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getBatDetailData"},
            data={
                "plantId": plant_id,
                "id": serial_num,
                "lan": int(language_code),
            },
        )

        return response.json()

    def mix_info(
        self,
        mix_id: str,
        plant_id: Optional[Union[int, str]] = None,
    ) -> Dict[str, Any]:
        """
        Returns high level values from Mix device

        Args:
            mix_id (str):
                The serial number (device_sn) of the inverter
            plant_id (Optional[Union[int, str]]) = None:
                The ID of the plant
                Note: the mobile app uses this but it does not appear to be necessary

        Returns:
            Dict[str, Any]:
                battery energy data
                e.g. (NEO inverter, no battery attached)
                {
                    'ibat': '0.0',
                    'iGuid': '+0.0',
                    'ipv': '0.0',
                    'pbat': '0.0',
                    'pGuid': '+0.0',
                    'ppv': '0.0',
                    'upsPac1': '0.0',
                    'upsPac2': '0.0',
                    'upsPac3': '0.0',
                    'vbat': '0.0',
                    'vGuid': '0.0',
                    'vpv': '0.0'
                }
                e.g. (MIX)
                {
                    'acChargeEnergyToday': 2.7,
                    'acChargeEnergyTotal': 25.3,
                    'acChargePower': 0,
                    'capacity': '45',         # The current remaining capacity of the batteries (same as soc but without the % sign)
                    'eBatChargeToday': 0,     # Battery charged today in kWh
                    'eBatChargeTotal': 0,     # Battery charged total (all time) in kWh
                    'eBatDisChargeToday': 0,  # Battery discharged today in kWh
                    'eBatDisChargeTotal': 0,  # Battery discharged total (all time) in kWh
                    'epvToday': 0,            # Energy generated from PVs today in kWh
                    'epvTotal': 0,            # Energy generated from PVs total (all time) in kWh
                    'isCharge': 0,            # Possible a 0/1 based on whether the battery is charging
                    'pCharge1': 0,
                    'pDischarge1': 0,         # Battery discharging rate in W
                    'soc': '45%',             # State of charge including % symbol
                    'upsPac1': 0,
                    'upsPac2': 0,
                    'upsPac3': 0,
                    'vbat': 0,                # Battery Voltage
                    'vbatdsp': 51.8,
                    'vpv1': 0,                # Voltage PV1
                    'vpv2': 0                 # Voltage PV2
                }
        """

        params = {"op": "getMixInfo", "mixId": mix_id}

        if plant_id is not None:
            params["plantId"] = plant_id

        response = self.session.get(self.get_url("newMixApi.do"), params=params)

        return response.json().get("obj", {})

    def mix_totals(
        self,
        mix_id: str,
        plant_id: Union[int, str],
    ) -> Dict[str, Any]:
        """
        Returns "Totals" values from Mix device

        Args:
            mix_id (str):
                The serial number (device_sn) of the inverter
            plant_id (Union[int, str]):
                The ID of the plant

        Returns:
            Dict[str, Any]:
                mix energy metrics
                e.g.
                {
                    'echargetoday': 0,              # Battery charged today in kWh (same as eBatChargeToday from mix_info)
                    'echargetotal': 0,              # Battery charged total (all time) in kWh (same as eBatChargeTotal from mix_info)
                    'edischarge1Today': 0,          # Battery discharged today in kWh (same as eBatDisChargeToday from mix_info)
                    'edischarge1Total': 0,          # Battery discharged total (all time) in kWh (same as eBatDisChargeTotal from mix_info)
                    'elocalLoadToday': 0,           # Load consumption today in kWh
                    'elocalLoadTotal': 0,           # Load consumption total (all time) in kWh
                    'epvToday': 0,                  # Energy generated from PVs today in kWh (same as epvToday from mix_info)
                    'epvTotal': 0,                  # Energy generated from PVs total (all time) in kWh (same as epvTotal from mix_info)
                    'etoGridToday': 0,              # Energy exported to the grid today in kWh
                    'etogridTotal': 0,              # Energy exported to the grid total (all time) in kWh
                    'photovoltaicRevenueToday': 0,  # Revenue earned from PV today in 'unit' currency
                    'photovoltaicRevenueTotal': 0,  # Revenue earned from PV total (all time) in 'unit' currency
                    'unit': '',                     # Unit of currency for 'Revenue'
                }
        """

        response = self.session.post(
            self.get_url("newMixApi.do"), params={"op": "getEnergyOverview", "mixId": mix_id, "plantId": plant_id}
        )

        return response.json().get("obj", {})

    def mix_system_status(
        self,
        mix_id: str,
        plant_id: Union[int, str],
    ) -> Dict[str, Any]:
        """
        Returns current "Status" from Mix device

        Args:
            mix_id (str):
                The serial number (device_sn) of the inverter
            plant_id (Union[int, str]):
                The ID of the plant

        Returns:
            Dict[str, Any]:
                mix power metrics
                e.g.
                {
                    'SOC': 0,  # State of charge (remaining battery %)
                    'chargePower': 0,  # Battery charging rate in kw
                    'fAc': 0,  # Frequency (Hz)
                    'lost': 'mix.status.normal',  # System status
                    'pLocalLoad': 0,  # Load conumption in kW
                    'pPv1': 0,  # PV1 Wattage in W
                    'pPv2': 0,  # PV2 Wattage in W
                    'pactogrid': 0,  # Export to grid rate in kW
                    'pactouser': 0,  # Import from grid rate in kW
                    'pdisCharge1': 0,  # Discharging batteries rate in kW
                    'pmax': 6,  # PV Maximum kW?
                    'ppv': 0,  # PV combined Wattage in kW
                    'priorityChoose': 0,  # Priority setting - 0=Local load
                    'status': 0,  # System statue - ENUM - Unknown values
                    'unit': 'kW',  # Unit of measurement
                    'upsFac': 0,
                    'upsVac1': 0,
                    'uwSysWorkMode': 6,
                    'vAc1': 0,  # Grid voltage in V
                    'vBat': 0,  # Battery voltage in V
                    'vPv1': 0,  # PV1 voltage in V
                    'vPv2': 0,  # PV2 voltage in V
                    'vac1': 0,  # Grid voltage in V (same as vAc1)
                    'wBatteryType': 1,
                }
        """

        response = self.session.post(
            self.get_url("newMixApi.do"), params={"op": "getSystemStatus_KW", "mixId": mix_id, "plantId": plant_id}
        )

        return response.json().get("obj", {})

    def mix_detail(
        self,
        mix_id: str,
        plant_id: Union[int, str],
        timespan: Timespan = Timespan.month,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
    ) -> Dict[str, Any]:
        """
        Get Mix details for specified timespan

        Note: It is possible to calculate the PV generation that went into charging the batteries by performing
              the following calculation:
              Solar to Battery = Solar Generation         - Export to Grid - Load consumption from solar
                                 epvToday (from mix_info) - eAcCharge      - eChargeToday

        Args:
            mix_id (str):
                The serial number (device_sn) of the inverter
            plant_id (Union[int, str]):
                The ID of the plant
            timespan (Timespan):
                The ENUM value conforming to the time window you want
            date (Union[datetime.datetime, datetime.date]) = datetime.date.today():
                The date for which to retrieve the chart data.

        Returns:
            Dict[str, Any]:
                A chartData object where each entry is for a specific 5 minute window e.g. 00:05 and 00:10 respectively (below)
                e.g.
                {
                    'chartData': {
                        '00:05': {
                            'pacToGrid': 0,  # Export rate to grid in kW
                            'pacToUser': 0,  # Import rate from grid in kW
                            'pdischarge': 0,  # Battery discharge in kW
                            'ppv': 0,  # Solar generation in kW
                            'sysOut': 0,  # Load consumption in kW
                        },
                        '00:10': {
                            'pacToGrid': '0',
                            'pacToUser': '0.93',
                            'pdischarge': '0',
                            'ppv': '0',
                            'sysOut': '0.93',
                        },
                        ...
                    },
                    'eAcCharge': 0,  # Exported to grid in kWh
                    'eCharge': 0,  # System production in kWh = Self-consumption + Exported to Grid
                    'eChargeToday': 0,  # Load consumption from solar in kWh
                    'eChargeToday1': 0,  # Self-consumption in kWh
                    'eChargeToday2': 0,  # Self-consumption in kWh (eChargeToday + echarge1)
                    'echarge1': 0,  # Load consumption from battery in kWh
                    'echargeToat': 0,  # Total battery discharged (all time) in kWh
                    'elocalLoad': 0,  # Load consumption in kW (battery + solar + imported)
                    'etouser': 0,  # Load consumption imported from grid in kWh
                    'photovoltaic': 0,  # Load consumption from solar in kWh (same as eChargeToday)
                    'ratio1': 0,  # % of system production that is self-consumed
                    'ratio2': 0,  # % of system production that is exported
                    'ratio3': 0,  # % of Load consumption that is "self consumption"
                    'ratio4': 0,  # % of Load consumption that is "imported from grid"
                    'ratio5': 0,  # % of Self consumption that is directly from Solar
                    'ratio6': 0,  # % of Self consumption that is from batteries
                    'unit': 'kWh',  # Unit of measurement
                    'unit2': 'kW',  # Unit of measurement
                }
        """

        date_str = self.__get_date_string(timespan, date)

        response = self.session.post(
            self.get_url("newMixApi.do"),
            params={
                "op": "getEnergyProdAndCons_KW",
                "plantId": plant_id,
                "mixId": mix_id,
                "type": timespan.value,
                "date": date_str,
            },
        )

        return response.json().get("obj", {})

    def dashboard_data(
        self,
        plant_id: Union[str, int],
        timespan: Timespan = Timespan.hour,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
    ) -> Dict[str, Any]:
        """
        Get 'dashboard' data for specified timespan

        Note:
            * Does not return any data for a tlx system. Use plant_energy_data() instead.
            * All numerical values returned by this api call include units e.g. kWh or %
            * Many of the 'total' values that are returned for a Mix system are inaccurate on the system this was tested against.
              However, the statistics that are correct are not available on any other interface, plus these values may be accurate for
              non-mix types of system. Where the values have been proven to be inaccurate they are commented below.

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            timespan (Timespan) = Timespan.hour:
                The ENUM value conforming to the time window you want e.g. hours from today, days, or months.
            date (Union[datetime.datetime, datetime.date]) = datetime.date.today():
                The date for which to retrieve the chart data.

        Returns:
            Dict[str, Any]
                A chartData object where each entry is for a specific 5 minute window e.g. 00:05 and 00:10 respectively.
                Note: The keys are interpreted differently, the examples below describe what they are used for in a 'Mix' system
                e.g.
                {
                    'chartData': {
                        '00:05': {
                            'pacToUser': 0,  # Power from battery in kW
                            'ppv': '0',  # Solar generation in kW
                            'sysOut': '0',  # Load consumption in kW
                            'userLoad': '0',  # Export in kW
                        },
                        '00:10': {
                            'pacToUser': '0',
                            'ppv': '0',
                            'sysOut': '0.7',
                            'userLoad': '0',
                        },
                        # ...
                    },
                    'chartDataUnit': 'kW',              # Unit of measurement
                    'eAcCharge': '20.5kWh',             # Energy exported to the grid in kWh (not accurate for Mix systems)
                    'eCharge': '23.1kWh',               # System production in kWh = Self-consumption + Exported to Grid (not accurate for Mix systems - actually showing the total 'load consumption')
                    'eChargeToday1': '2.6kWh',          # Self-consumption of PPV (possibly including excess diverted to batteries) in kWh (not accurate for Mix systems)
                    'eChargeToday2': '10.1kWh',         # Total self-consumption (PPV consumption(eChargeToday2Echarge1) + Battery Consumption(echarge1)) (not accurate for Mix systems)
                    'eChargeToday2Echarge1': '0.8kWh',  # Self-consumption of PPV only (not accurate for Mix systems)
                    'echarge1': '9.3kWh',               # Self-consumption from Battery only
                    'echargeToat': '152.1kWh',          # Not used on Dashboard view, likely to be total battery discharged
                    'elocalLoad': '20.3kWh',            # Total load consumption (etouser + eChargeToday2) (not accurate for Mix systems)
                    'etouser': '10.2kWh',               # Energy imported from grid today (includes both directly used by load and AC battery charging)
                    'keyNames': ['Solar', 'Load Consumption', 'Export To Grid', 'From Battery'],  # Keys to be used for the graph data
                    'photovoltaic': '0.8kWh',           # Same as eChargeToday2Echarge1
                    'ratio1': '11.3%',                  # % of 'Solar production' that is self-consumed (not accurate for Mix systems)
                    'ratio2': '88.7%',                  # % of 'Solar production' that is exported (not accurate for Mix systems)
                    'ratio3': '49.8%',                  # % of 'Load consumption' that is self consumption (not accurate for Mix systems)
                    'ratio4': '50.2%',                  # % of 'Load consumption' that is imported from the grid (not accurate for Mix systems)
                    'ratio5': '92.1%',                  # % of Self consumption that is from batteries (not accurate for Mix systems)
                    'ratio6': '7.9%',                   # % of Self consumption that is directly from Solar (not accurate for Mix systems)
                }
        """

        date_str = self.__get_date_string(timespan, date)

        response = self.session.post(
            self.get_url("newPlantAPI.do"),
            params={"action": "getEnergyStorageData", "date": date_str, "type": timespan.value, "plantId": plant_id},
        )

        return response.json()

    def plant_settings(
        self,
        plant_id: Union[str, int],
    ) -> Dict[str, Any]:
        """
        Returns a dictionary containing the settings for the specified plant

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.

        Returns:
            Dict[str, Any]
                settings for the specified plant
                e.g.
                {
                    'EYearMoneyText': '0',
                    'alarmValue': 0,
                    'alias': '',
                    'children': [],
                    'city': '{CITY}',
                    'companyName': '',
                    'country': '{COUNTRY}',
                    'createDate': {
                        'year': 124,  # 124 = 2024
                        'month': 1,
                        'date': 1,   # day
                        'day': 5,     # weekday
                        'hours': 0,
                        'minutes': 0,
                        'seconds': 0,
                        'time': 1732000000000,
                        'timezoneOffset': -480,
                    },
                    'createDateText': '2024-01-01',
                    'createDateTextA': '',
                    'currentPac': 0,
                    'currentPacStr': '',
                    'currentPacTxt': '0',
                    'dataLogList': [],
                    'defaultPlant': False,
                    'designCompany': '0',
                    'deviceCount': 0,
                    'eToday': 0,
                    'eTotal': 0,
                    'emonthCo2Text': '0',
                    'emonthCoalText': '0',
                    'emonthMoneyText': '0',
                    'emonthSo2Text': '0',
                    'energyMonth': 0,
                    'energyYear': 0,
                    'envTemp': 0,
                    'etodayCo2Text': '0',
                    'etodayCoalText': '0',
                    'etodayMoney': 0,
                    'etodayMoneyText': '0',
                    'etodaySo2Text': '0',
                    'etotalCo2Text': '0',
                    'etotalCoalText': '0',
                    'etotalFormulaTreeText': '0',
                    'etotalMoney': 0,
                    'etotalMoneyText': '0',
                    'etotalSo2Text': '0',
                    'eventMessBeanList': [],
                    'fixedPowerPrice': 0.30,
                    'flatPeriodPrice': 0.30,
                    'formulaCo2': 0.40,
                    'formulaCoal': 0.40,
                    'formulaMoney': 0.30,
                    'formulaMoneyStr': '0.3',
                    'formulaMoneyUnitId': 'EUR',
                    'formulaSo2': 0,
                    'formulaTree': 0.055,
                    'gridCompany': '',
                    'gridLfdi': '',
                    'gridPort': '',
                    'gridServerUrl': '',
                    'hasDeviceOnLine': 0,
                    'hasStorage': 0,
                    'id': {PLANT_ID},
                    'imgPath': 'css/img/plant.gif',
                    'installMapName': '',
                    'irradiance': 0,
                    'isShare': False,
                    'latitudeText': 'null°null′null″',
                    'latitude_d': '',
                    'latitude_f': '',
                    'latitude_m': '',
                    'level': 1,
                    'locationImgName': '',
                    'logoImgName': '',
                    'longitudeText': 'null°null′null″',
                    'longitude_d': '',
                    'longitude_f': '',
                    'longitude_m': '',
                    'mapCity': '',
                    'mapLat': '',
                    'mapLng': '',
                    'map_areaId': 0,
                    'map_cityId': 0,
                    'map_countryId': 0,
                    'map_provinceId': 0,
                    'moneyUnitText': '€',
                    'nominalPower': 800,
                    'nominalPowerStr': '0.8kWp',
                    'onLineEnvCount': 0,
                    'pairViewUserAccount': '',
                    'panelTemp': 0,
                    'paramBean': None,
                    'parentID': '',
                    'peakPeriodPrice': 0.30,
                    'phoneNum': '',
                    'plantAddress': '',
                    'plantFromBean': None,
                    'plantImgName': '',
                    'plantName': '{PLANT_NAME}',
                    'plantNmi': '',
                    'plantType': 0,
                    'plant_lat': '48.00000',
                    'plant_lng': '9.00000',
                    'prMonth': '',
                    'prToday': '',
                    'protocolId': '',
                    'remark': '',
                    'status': 0,
                    'storage_BattoryPercentage': 0,
                    'storage_TodayToGrid': 0,
                    'storage_TodayToUser': 0,
                    'storage_TotalToGrid': 0,
                    'storage_TotalToUser': 0,
                    'storage_eChargeToday': 0,
                    'storage_eDisChargeToday': 0,
                    'tempType': 0,
                    'timezone': 1,
                    'timezoneText': 'GMT+1',
                    'timezoneValue': '+1:00',
                    'treeID': 'PLANT_{PLANT_ID}',
                    'treeName': '{PLANT_NAME}',
                    'unitMap': {
                        'AED': 'AED', ..., 'EUR': 'EUR', ..., 'ZMW': 'ZMW'
                    },
                    'userAccount': '{USER_NAME}',
                    'userBean': None,
                    'valleyPeriodPrice': 0.30,
                    'windAngle': 0,
                    'windSpeed': 0
                }
        """

        response = self.session.get(self.get_url("newPlantAPI.do"), params={"op": "getPlant", "plantId": plant_id})

        return response.json()

    def storage_detail(self, storage_id: str) -> Dict[str, Any]:
        """
        Get "All parameters" from battery storage.

        Args:
            storage_id (str):
                The ID of the storage.

        Returns:
            Dict[str, Any]:
                battery storage data
                e.g.
                {
                    'batSn': '',
                    'iGuid': '+0.0',
                    'ibat': '0.0',
                    'ipv': '0.0',
                    'pGuid': '+0.0',
                    'pbat': '0.0',
                    'ppv': '0.0',
                    'vGuid': '0.0',
                    'vbat': '0.0',
                    'vpv': '0.0'
                }
        """

        response = self.session.get(
            self.get_url("newStorageAPI.do"), params={"op": "getStorageInfo_sacolar", "storageId": storage_id}
        )

        return response.json()

    def storage_params(self, storage_id: str) -> Dict[str, Any]:
        """
        Get much more detail from battery storage.

        Args:
            storage_id (str):
                The ID of the storage.

        Returns:
            Dict[str, Any]:
                battery storage details
        """
        response = self.session.get(
            self.get_url("newStorageAPI.do"), params={"op": "getStorageParams_sacolar", "storageId": storage_id}
        )

        return response.json()

    def storage_energy_overview(self, plant_id: Union[str, int], storage_id: str) -> Dict[str, Any]:
        """
        Get some energy/generation overview data.

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            storage_id (str):
                The ID of the storage.

        Returns:
            Dict[str, Any]:
                battery energy data
        """
        response = self.session.post(
            self.get_url("newStorageAPI.do?op=getEnergyOverviewData_sacolar"),
            params={"plantId": plant_id, "storageSn": storage_id},
        )

        return response.json().get("obj", {})

    def inverter_list(
        self,
        plant_id: Union[str, int],
    ) -> List[Dict[str, Any]]:
        """
        Use device_list, it's more descriptive since the list contains more than inverters.

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.

        Returns:
            List[Dict[str, Any]]:
                settings for the specified plant
                e.g.
                [
                    {
                        'bMerterConnectFlag': 0,
                        'bdc1Soc': 0,
                        'bdc2Soc': 0,
                        'datalogSn': '{DATALOGGER_ID}',
                        'deviceAilas': '{INVERTER_ID}',
                        'deviceSn': '{INVERTER_ID}',
                        'deviceStatus': '1',
                        'deviceType': 'tlx',
                        'eToday': '0',
                        'eTodayStr': '0kWh',
                        'energy': '29.3',
                        'isParallel': 'false',
                        'location': '',
                        'lost': False,
                        'power': '7.1',
                        'powerStr': '0.01kW',
                        'prePto': '-1',
                        'type': 0,
                        'type2': '5',
                        'xe_ct': '0'
                    }
                ]
        """
        warnings.warn(
            "This function may be deprecated in the future because naming is not correct, use device_list instead",
            DeprecationWarning,
        )
        return self.device_list(plant_id)

    def _get_all_devices(
        self,
        plant_id: Union[str, int],
        language_code: Union[LanguageCode, int] = LanguageCode.en,
    ) -> List[Dict[str, Any]]:
        """
        Get basic plant information with device list.

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode

        Returns:
            List[Dict[str, Any]]
                list of devices assigned to plant
                e.g.
                [
                    {
                        'bMerterConnectFlag': 0,
                        'bdc1Soc': 0,
                        'bdc2Soc': 0,
                        'datalogSn': '{DATALOGGER_ID}',
                        'deviceAilas': '{INVERTER_ID}',
                        'deviceSn': '{INVERTER_ID}',
                        'deviceStatus': '1',
                        'deviceType': 'tlx',
                        'eToday': '0',
                        'eTodayStr': '0kWh',
                        'energy': '29.3',
                        'isParallel': 'false',
                        'location': '',
                        'lost': False,
                        'power': '7.1',
                        'powerStr': '0.01kW',
                        'prePto': '-1',
                        'type': 0,
                        'type2': '5',
                        'xe_ct': '0'
                    }
                ]
        """

        response = self.session.get(
            self.get_url("newTwoPlantAPI.do"),
            params={"op": "getAllDeviceList", "plantId": plant_id, "language": int(language_code)},
        )

        return response.json().get("deviceList", {})

    def device_list(
        self,
        plant_id: Union[str, int],
        language: str = "en",
    ) -> List[Dict[str, Any]]:
        """
        Get a list of all devices connected to plant.

        Args:
            plant_id (Union[str, int]):
                The ID of the plant.
            language (str) = "en":
                language to use for query, e.g. "en"

        Returns:
            List[Dict[str, Any]]
                list of devices assigned to plant
                e.g.
                [
                    {
                        'bMerterConnectFlag': 0,
                        'bdc1Soc': 0,
                        'bdc2Soc': 0,
                        'datalogSn': '{DATALOGGER_ID}',
                        'deviceAilas': '{INVERTER_ID}',
                        'deviceSn': '{INVERTER_ID}',
                        'deviceStatus': '1',
                        'deviceType': 'tlx',
                        'eToday': '0',
                        'eTodayStr': '0kWh',
                        'energy': '29.3',
                        'isParallel': 'false',
                        'location': '',
                        'lost': False,
                        'power': '7.1',
                        'powerStr': '0.01kW',
                        'prePto': '-1',
                        'type': 0,
                        'type2': '5',
                        'xe_ct': '0'
                    }
                ]
        """

        device_list = self.plant_info(
            plant_id=plant_id,
            language=language,
        ).get("deviceList", [])

        if not device_list:
            # for tlx systems, the device_list in plant is empty, so use __get_all_devices() instead
            device_list = self._get_all_devices(
                plant_id=plant_id,
                language_code=int(
                    getattr(LanguageCode, language, LanguageCode.en)
                ),  # look up language code, default to english
            )

        return device_list

    def device_detail(
        self,
        device_id: str,
        device_type: Literal["tlx", "mix", "storage"] = "tlx",
    ) -> Dict[str, Any]:
        """
        Get detailed data from TLX inverter.
        Data is visible in App->Plant->Inverter->All parameters->Important data

        Args:
            device_id (str):
                The ID of the (TLX/MIX) inverter (device_id, tlx_id, mix_id).
            device_type (Literal["tlx", "mix", "storage"]) = "tlx":
                The type of device to get the data from.

        Returns:
            Dict[str, Any]:
                A dictionary containing the current Voltage/Current/Power values.
                e.g.
                {
                    'parameterGreat': [
                        ['', 'Voltage(V)', 'Current(A)', 'Power(W)'],
                        ['PV1', '0', '0', '0'],
                        ['PV2', '0', '0', '0'],
                        ['AC',  '0', '0', '0']
                    ]
                }
        """

        response = self.session.post(
            self.get_url("newTwoDeviceAPI.do"),
            params={"op": "getDeviceDetailData"},
            data={"deviceType": f"{device_type.lower()}", "sn": f"{device_id}"},
        )

        return response.json().get("obj", {})

    def device_event_logs(
        self,
        device_id: str,
        device_type: Literal["pcs", "bms", "jlinv", "min", "mic", "mod", "neo", "tlx"] = "tlx",
        language_code: Union[LanguageCode, int] = LanguageCode.en,
        page_num: int = 1,
    ) -> Dict[str, Any]:
        """
        Returns a dictionary containing events/alarms logged for specified device (e.g. inverter).

        Data is visible in App->Plant->Inverter->All parameters->Important data

        Args:
            device_id (str):
                The ID of the (TLX/MIX) inverter (device_id, tlx_id, mix_id).
            device_type (Literal["pcs", "bms", "jlinv", "min", "mic", "mod", "neo", "tlx"]) = "tlx":
                The type of device to get the data from.
                Supported values (so far):
                * "pcs"   (PCS)
                * "bms"   (BMS - Battery Management System)
                * "jlinv" (Solis Inverter)
                * "min"   (MIN Inverter)
                * "mic"   (MIC Inverter)
                * "mod"   (MOD Inverter)
                * "neo"   (NEO Inverter)
                * "tlx"   (MIN/MIC/MOD/NEO)
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode
            page_num (int) = 1:
                Page number

        Returns:
            Dict[str, Any]:
                A dictionary containing the current Voltage/Current/Power values.
                e.g.
                {
                    'city': '{PLANT_CITY}',
                    'country': '{PLANT_COUNTRY}',
                    'deviceType': 'MIN/MIC/MOD/NEO',
                    'eventList': [
                        {
                            'description': 'No AC Connection',
                            'deviceAlias': '',
                            'deviceSerialNum': '{INVERTER_SN}',
                            'event': 'ERROR_302',
                            'eventCode': '302',
                            'language': '19',
                            'lcdid': '',
                            'occurTime': '2024-01-02 03:04:05',
                            'solution': '1.After shutdown,Check AC wiring. 2.If error message still exists,contact manufacturer.'
                        }
                    ],
                    'pageSize': 1,
                    'plantAddress': '{PLANT_ADDRESS}',
                    'plantId': {PLANT_ID},
                    'plantName': '{PLANT_NAME}',
                    'plant_lat': '40.123456',
                    'plant_lng': '9.123456',
                    'toPageNum': 1
                }
        """

        device_type_id = {
            "pcs": 5,
            "bms": 6,
            "jlinv": 7,
            "min": 8,
            "mic": 8,
            "mod": 8,
            "neo": 8,
            "tlx": 8,
        }[device_type.lower()]

        url = self.get_url("newPlantAPI.do")
        params = {"action": "getDeviceEvent"}
        data = {
            "deviceSn": device_id,
            "deviceType": device_type_id,
            "language": int(language_code),
            "toPageNum": page_num,
        }
        response = self.session.post(
            url=url,
            params=params,
            data=data,
        )

        # # device_type values have been reverse-engineered
        # #  by running this request with different device_type values
        # #  and checking response data's attribute "deviceType"
        # # to check for allowed values, run this code:
        # from time import sleep
        # for device_type_id in range(20):
        #     data["deviceType"] = device_type_id
        #     response = self.session.post(url=url, params=params, data=data)
        #     print(f"{device_type_id:3} | {response.json().get('obj') or {}.get('deviceType') or None}")
        #     sleep(0.5)
        # # => 5 | pcs
        # # => 6 | bms
        # # => 7 | jlinv
        # # =>  8 | MIN/MIC/MOD/NEO

        data = response.json().get("obj") or {}

        return data

    def plant_info(
        self,
        plant_id: Union[int, str],
        language: str = "en",
    ):
        """
        Get basic plant information with device list.

        Args:
            plant_id (Union[int, str]):
                The ID of the plant
            language (str) = "en":
                e.g. en=English, de=German (None=Chinese)

        Returns:
            Dict[str, Any]
                e.g.
                {
                    'ammeterType': '0',
                    'batList': [],
                    'boostList': [],
                    'chargerList': [],
                    'Co2Reduction': '10.92',
                    'invTodayPpv': '0',
                    'isHaveOptimizer': 0,
                    'isHavePumper': '0',
                    'meterList': [],
                    'nominalPower': 800,
                    'nominal_Power': 800,
                    'ogbList': [],
                    'optimizerType': 0,
                    'pidList': [],
                    'plantMoneyText': '0.1/€',
                    'sphList': [],
                    'storageList': [],
                    'storagePgrid': '0',
                    'storagePuser': '0',
                    'storageTodayPpv': '0',
                    'todayDischarge': '0',
                    'todayEnergy': '0.2',
                    'totalEnergy': '27.3',
                    'totalMoneyText': '8.19',
                    'useEnergy': '0',
                    'datalogList': [{
                        'alias': '{DATALOGGER_SN}',
                        'client_url': '/10.10.0.100:12345',  # internal IP
                        'datalog_sn': '{DATALOGGER_SN}',     # e.g. QMN0000000000000
                        'deviceTypeIndicate': '55',
                        'device_type': 'ShineWeFi',
                        'isGprs4G': '0',
                        'keys': ['Signal', 'Connection Status', 'Last Update', 'Data Update Interval'],
                        'lfdi': '0',
                        'lost': True,
                        'meter': {},
                        'simInfo': None,
                        'type': '55',
                        'unit_id': '',
                        'update_interval': '5',
                        'update_time': '2020-01-02 03:04:05',
                        'values': ['Poor', 'Offline', '2020-01-02 03:04:05', '5']
                    }],
                    'deviceList': [],
                    'invList': [{
                        'bMerterConnectFlag': 0,
                        'bdc1Soc': 0,
                        'bdc2Soc': 0,
                        'datalogSn': '{DATALOGGER_SN}',
                        'deviceAilas': '',
                        'deviceSn': '{DEVICE_SN/INVERTER_ID/TLX_ID}',  # e.g. BZP0000000
                        'deviceStatus': '-1',
                        'deviceType': 'tlx',
                        'eToday': '0.2',
                        'eTodayStr': '0.2kWh',
                        'energy': '20.3',
                        'location': '',
                        'lost': True,
                        'plantId': {PLANT_ID},
                        'power': '0',
                        'powerStr': '0kW',
                        'prePto': '-1',
                        'type': 0,
                        'type2': '5'
                    }],
                    'witList': []
                }
        """

        response = self.session.get(
            url=self.get_url("newTwoPlantAPI.do"),
            params={
                "op": "getAllDeviceListTwo",
                "plantId": plant_id,
                "language": language,
                "pageNum": 1,
                "pageSize": 1,
            },
        )

        return response.json()

    def plant_energy_data(
        self,
        plant_id: Union[int, str],
        language_code: Union[LanguageCode, int] = LanguageCode.en,
    ) -> Dict[str, Any]:
        """
        Get the energy data used in the 'Plant' tab in the phone

        Args:
            plant_id (Union[int, str]):
                The ID of the plant
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode

        Returns:
            Dict[str, Any]
                e.g.
                {
                    'alarmValue': 0,
                    'eventMessBeanList': [],
                    'formulaCo2Str': '10.8kg',
                    'formulaCo2Vlue': '10.8',
                    'formulaCoalStr': '10.8kg',
                    'formulaCoalValue': '10.8',
                    'isHaveTigo': 0,
                    'monthStr': '18kWh',
                    'monthValue': '18.0',
                    'nominalPowerStr': '0.8kWp',
                    'nominalPowerValue': '800.0',
                    'optimezerMap': {'isHaveOptimezer': 0},
                    'plantNumber': 1,
                    'powerValue': '0.0',
                    'powerValueStr': '0kW',
                    'todayStr': '1.1kWh',
                    'todayValue': '1.1',
                    'totalStr': '12.1kWh',
                    'totalValue': '12.1',
                    'treeStr': '1',
                    'treeValue': '1.5',
                    'yearStr': '0kWh',
                    'yearValue': '0.0',
                    'weatherMap': {
                        'cond_code': '100',
                        'cond_txt': 'Sunny',
                        'msg': '',
                        'newTmp': '9.0°C',
                        'success': True,
                        'tmp': '9'
                    },
                    'plantBean': {
                        'alarmValue': 0,
                        'alias': None,
                        'children': None,
                        'city': 'Ulm',
                        'companyName': '',
                        'country': 'Germany',
                        'createDate': 1730000000000,
                        'createDateText': '2025-01-14',
                        'createDateTextA': None,
                        'currentPac': 0,
                        'currentPacStr': None,
                        'currentPacTxt': '0',
                        'dataLogList': None,
                        'defaultPlant': False,
                        'designCompany': '0',
                        'deviceCount': 0,
                        'eToday': 0,
                        'eTotal': 27.1,
                        'emonthCo2Text': '0',
                        'emonthCoalText': '0',
                        'emonthMoneyText': '0',
                        'emonthSo2Text': '0',
                        'energyMonth': 0,
                        'energyYear': 0,
                        'envTemp': 0,
                        'etodayCo2Text': '0',
                        'etodayCoalText': '0',
                        'etodayMoney': 0,
                        'etodayMoneyText': '0',
                        'etodaySo2Text': '0',
                        'etotalCo2Text': '10.8',
                        'etotalCoalText': '10.8',
                        'etotalFormulaTreeText': '1.49',
                        'etotalMoney': 0,
                        'etotalMoneyText': '8.1',
                        'etotalSo2Text': '0.8',
                        'eventMessBeanList': None,
                        'eyearMoneyText': '0',
                        'fixedPowerPrice': 0.3,
                        'flatPeriodPrice': 0.3,
                        'formulaCo2': 0.4,
                        'formulaCoal': 0.4,
                        'formulaMoney': 0.3,
                        'formulaMoneyStr': None,
                        'formulaMoneyUnitId': 'EUR',
                        'formulaSo2': 0,
                        'formulaTree': 0.055,
                        'gridCompany': None,
                        'gridLfdi': None,
                        'gridPort': None,
                        'gridServerUrl': None,
                        'hasDeviceOnLine': 0,
                        'hasStorage': 0,
                        'id': {PLANT_ID},
                        'imgPath': 'css/img/plant.gif',
                        'installMapName': None,
                        'irradiance': 0,
                        'isShare': False,
                        'latitudeText': 'null°null′null″',
                        'latitude_d': None,
                        'latitude_f': None,
                        'latitude_m': None,
                        'level': 1,
                        'locationImgName': None,
                        'logoImgName': '',
                        'longitudeText': 'null°null′null″',
                        'longitude_d': None,
                        'longitude_f': None,
                        'longitude_m': None,
                        'mapCity': None,
                        'mapLat': None,
                        'mapLng': None,
                        'map_areaId': 0,
                        'map_cityId': 0,
                        'map_countryId': 0,
                        'map_provinceId': 0,
                        'moneyUnitText': '€',
                        'nominalPower': 800,
                        'nominalPowerStr': '0.8kWp',
                        'onLineEnvCount': 0,
                        'pairViewUserAccount': None,
                        'panelTemp': 0,
                        'paramBean': None,
                        'parentID': None,
                        'peakPeriodPrice': 0.3,
                        'phoneNum': None,
                        'plantAddress': '{PLANT_ADDRESS}',
                        'plantFromBean': None,
                        'plantImgName': None,
                        'plantName': '{PLANT_NAME}',
                        'plantNmi': None,
                        'plantType': 0,
                        'plant_lat': '12.345678',
                        'plant_lng': '9.101112',
                        'prMonth': None,
                        'prToday': None,
                        'protocolId': None,
                        'remark': None,
                        'status': 0,
                        'storage_BattoryPercentage': 0,
                        'storage_TodayToGrid': 0,
                        'storage_TodayToUser': 0,
                        'storage_TotalToGrid': 0,
                        'storage_TotalToUser': 0,
                        'storage_eChargeToday': 0,
                        'storage_eDisChargeToday': 0,
                        'tempType': 0,
                        'timezone': 1,
                        'timezoneText': 'GMT+1',
                        'timezoneValue': '+1:00',
                        'treeID': 'PLANT_{PLANT_ID}',
                        'treeName': '{PLANT_NAME}',
                        'unitMap': None,
                        'userAccount': '{USER_NAME}',
                        'userBean': None,
                        'valleyPeriodPrice': 0.3,
                        'windAngle': 0,
                        'windSpeed': 0
                    }
                }
        """

        response = self.session.post(
            url=self.get_url("newTwoPlantAPI.do"),
            params={"op": "getUserCenterEnertyDataByPlantid"},
            data={"language": int(language_code), "plantId": plant_id},
        )

        return response.json()

    def plant_energy_data_v2(
        self,
        language_code: Union[LanguageCode, int] = LanguageCode.en,
    ) -> Dict[str, Any]:
        """
        Get the energy data used in the 'Dashboard' tab in the Android app
        Note: yearValue is always 0.0 (at least for NEO inverter)

        like plant_energy_data but with today/month/total profit

        Args:
            language_code (Union[LanguageCode, int]) = LanguageCode.en:
                see enum LanguageCode

        Returns:
            Dict[str, Any]
                e.g.
                {
                    "alarmValue": 0,
                    "deviceDetail": {},
                    "deviceTypeMap": {"STORAGE": 0, "SPA": 0, "MIX": 0, "TLXH": 0},
                    "eventMessBeanList": [],
                    "formulaCo2Str": "10.8kg",
                    "formulaCo2Vlue": "10.8",
                    "formulaCoalStr": "10.8kg",
                    "formulaCoalValue": "10.8",
                    "isHaveFormulaMoney": True,
                    "monthProfitStr": "€5.4"
                    "monthStr": "18kWh",
                    "monthValue": "18.0",
                    "nominalPowerStr": "0.8kWp",
                    "nominalPowerValue": 800,
                    "plantId": {PLANT_ID},
                    "plantNumber": 1,
                    "plantStatus": 0,
                    "plantType": 1,
                    "powerValue": "0.0",
                    "powerValueStr": "0kW",
                    "statusMap": {"onlineNum": 0, "offline": 1, "faultNum": 0},
                    "todayProfitStr": "€0.33",
                    "todayStr": "1.1kWh",
                    "todayUnit": "kWh",
                    "todayValue": "1.1",
                    "totalProfitStr": "€8.13",
                    "totalStr": "27.1kWh",
                    "totalValue": "27.1",
                    "treeStr": "1",
                    "treeValue": "1.5",
                    "yearStr": "0kWh",
                    "yearValue": "0.0",
                }

        """

        url = self.get_url("newPlantAPI.do")
        params = {"action": "getUserCenterEnertyDataTwo"}
        data = {"language": int(language_code)}

        response = self.session.post(url=url, params=params, data=data)
        response_json = response.json()

        return response_json

    def plant_power_chart(
        self,
        plant_id: Union[int, str],
        timespan: Literal[Timespan.day, Timespan.month, Timespan.year, Timespan.total] = Timespan.day,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
    ):
        """
        Retrieve data for Android app's "Power|Energy" chart available in "Plant" tab

        Args:
            plant_id (Union[int, str]):
                The ID of the plant
            timespan (Timespan) = Timespan.day:
                The ENUM value conforming to the time window you want
                * day   => one day, 5min values     (power pAC)
                * month => one month, daily values   (energy eAC)
                * year  => one year,  monthly values (energy eAC)
                * total => six years, yearly values  (energy eAC)
            date (Union[datetime.datetime, datetime.date]) = datetime.date.today():
                day/month/year for which to load the chart

        Returns:
            Dict[str, Any]: A dictionary containing the chart data
                e.g. (daily)

        """

        # API uses different actions for different timespans
        if timespan not in [Timespan.day, Timespan.month, Timespan.year, Timespan.total]:
            raise ValueError(f"Unsupported timespan: {timespan}")

        date_str = self.__get_date_string(timespan=timespan, date=date)

        url = self.get_url("newPlantDetailAPI.do")

        # parameter "type"
        # * type=1 returns power chart (5min values) for one day (App button "Hour")
        # * type=2 returns energy chart (daily values) for one month (App button "DAY")
        # * type=3 returns energy chart (monthly values) for one year (App button "MONTH")
        # * type=4 returns energy chart (yearly values) for six years (App button "YEAR")
        params = {
            "plantId": plant_id,
            "date": date_str,
            "type": timespan.value,
        }

        response = self.session.get(url=url, params=params)
        response_json = response.json()
        response_json = response_json.get("back", {}).get("data", {})

        return response_json

    def plant_energy_chart(
        self,
        timespan: Literal[Timespan.month, Timespan.year, Timespan.total] = Timespan.month,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
        id_: int = 0,
    ):
        """
        Retrieve data for Android app's "Power|Energy" chart available in "Dashboard" tab

        Args:
            timespan (Timespan) = Timespan.month:
                The ENUM value conforming to the time window you want
                * month => one month, daily values
                * year  => one year,  monthly values
                * total => six years, yearly values
            date (Union[datetime.datetime, datetime.date]) = datetime.date.today():
                month/year for which to load the chart
            id_ (int) = 0:
                Unknown parameter (but required)

        Returns:
            Dict[str, Any]: A dictionary containing the chart data
                e.g. (daily)
                {
                    "chartDataUnit": "kWh"
                    "chartData": {
                        "01": 1.2000000476837158,
                        "02": 0.10000000149011612,
                        ...
                        "12": 0.800000011920929
                }
        """

        # API uses different actions for different timespans
        if timespan == Timespan.total:
            action = "plantHistoryTotal"
        elif timespan == Timespan.year:
            action = "plantHistoryYear"
        elif timespan == Timespan.month:
            action = "plantHistoryMonth"
        else:
            raise ValueError(f"Unsupported timespan: {timespan}")

        date_str = self.__get_date_string(timespan=timespan, date=date)

        url = self.get_url("newTwoPlantAPI.do")
        params = {
            "action": action,
            "date": date_str,
            "id": id_,
        }

        response = self.session.get(url=url, params=params)
        response_json = response.json()
        response_json = response_json.get("obj", {})

        return response_json

    def plant_energy_chart_comparison(
        self,
        timespan: Literal[Timespan.year, Timespan.total] = Timespan.year,
        date: Optional[Union[datetime.datetime, datetime.date]] = None,
        id_: int = 0,
    ):
        """
        Retrieve data for Android app's "Power comparison" chart available in "Dashboard" tab

        comparison is available based on monthly or quarterly values

        Args:
            timespan (Timespan) = Timespan.year:
                The ENUM value conforming to the time window you want
                * year  => monthly values
                * total => quarterly values
            date (Union[datetime.datetime, datetime.date]) = datetime.date.today():
                year for which to load the comparison chart
            id_ (int) = 0:
                ???

        Returns:
            Dict[str, Any]: A dictionary containing the chart data
                e.g.
                {
                    "chartDataUnit": "kWh"
                    "chartData": {
                        "01": ["0", "18"],
                        "02": ["0", "0"],
                        ...
                        "12": ["9.1", "0"],
                    }
                }
        """

        if timespan == Timespan.total:
            month_or_quarter = 1  # quarterly values
        elif timespan == Timespan.year:
            month_or_quarter = 0  # monthly values
        else:
            raise ValueError(f"Unsupported timespan: {timespan}")

        date_str = self.__get_date_string(timespan=Timespan.year, date=date)

        url = self.get_url("newTwoPlantAPI.do")
        params = {
            "action": "dataComparison",
            "date": date_str,
            "type": month_or_quarter,
            "id": id_,
        }

        response = self.session.get(url=url, params=params)
        response_json = response.json()
        response_json = response_json.get("obj", {})

        return response_json

    def is_plant_noah_system(
        self,
        plant_id: Union[str, int],
    ) -> Dict[str, Any]:
        """
        Returns a dictionary containing if noah devices are configured for the specified plant

        Args:
            plant_id (Union[str, int]):
                The ID of the plant you want the noah devices of

        Returns:
                Dict[str, Any]:
                e.g.
                {
                    'msg': '',
                    'obj': {
                        'deviceSn': '',              # Serial number of the configured noah device
                        'isPlantHaveNexa': False,
                        'isPlantHaveNoah': False,    # Are noah devices configured in the specified plant (True or False)
                        'isPlantNoahSystem': False,  # Is the specified plant a noah system (True or False)
                        'plantId': '{PLANT_ID}',
                        'plantName': '{PLANT_NAME}'
                    },
                    'result': 1
                }
        """

        response = self.session.post(self.get_url("noahDeviceApi/noah/isPlantNoahSystem"), data={"plantId": plant_id})

        return response.json()

    def noah_system_status(self, serial_number: str) -> Dict[str, Any]:
        """
        Returns a dictionary containing the status for the specified Noah Device

        Args:
            serial_number (str):
                The Serial number of the noah device you want the status of

        Returns
            Dict[str, Any]
                NOAH device status
                e.g.
                {
                    'msg': '',
                    'result': 1,
                    'obj': {
                        'chargePower': '200Watt',       # Battery charging rate in Watt
                        'workMode': 0,                  # Workingmode of the battery (0 = Load First, 1 = Battery First)
                        'soc': None,                    # State of charge (remaining battery %)
                        'associatedInvSn': None,
                        'batteryNum': None,             # Numbers of batteries
                        'profitToday': None,            # Today generated profit through noah device
                        'plantId': '{PLANT_ID}',        # The ID of the plant
                        'disChargePower': '200Watt',    # Battery discharging rate in watt
                        'eacTotal': '20.5kWh',          # Total energy exported to the grid in kWh
                        'eacToday': '20.5kWh',          # Today energy exported to the grid in kWh
                        'pac': '200Watt',               # Export to grid rate in watt
                        'ppv': '200Watt',               # Solar generation in watt
                        'alias': {NOAH_NAME},           # Friendly name of the noah device
                        'profitTotal': 0.0,             # Total generated profit through noah device
                        'moneyUnit': '€',               # Unit of currency
                        'status': None,                 # Is the noah device online (True or False)
                    }
                }
        """

        response = self.session.post(
            self.get_url("noahDeviceApi/noah/getSystemStatus"), data={"deviceSn": serial_number}
        )

        return response.json()

    def noah_info(self, serial_number: str) -> Dict[str, Any]:
        """
        Returns a dictionary containing the information for the specified Noah Device

        Args:
            serial_number (str):
                The Serial number of the noah device you want the information of

        Returns
            Dict[str, Any]
                NOAH device info
        Returns
            Dict[str, Any]:
                e.g.
                {
                    'msg': '',
                    'result': 0,
                    'obj': {
                        'neoList': [],
                        'unitList': {"Euro": "euro", "DOLLAR": "dollar"},
                        'noah': {
                            'time_segment': {  # Note: The keys are generated numerical, the values are generated with folowing syntax "[workingmode (0 = Load First, 1 = Battery First)]_[starttime]_[endtime]_[output power]"
                                'time_segment1': "0_0:0_8:0_150",  # ([Load First]_[00:00]_[08:00]_[150 watt])
                                'time_segment2': "1_8:0_18:0_0",   # ([Battery First]_[08:00]_[18:00]_[0 watt])
                                # ...
                            },
                            'batSns': [],  # A list containing all battery Serial Numbers
                            'associatedInvSn': None,
                            'plantId': {PLANT_ID},
                            'chargingSocHighLimit': None,  # Configured "Battery Management" charging upper limit
                            'chargingSocLowLimit': None,  # Configured "Battery Management" charging lower limit
                            'defaultPower': None,  # Configured "System Default Output Power"
                            'version': None,  # The Firmware Version of the noah device
                            'deviceSn': '{NOAH_ID}',  # The Serial number of the noah device
                            'formulaMoney': '0.22',  # Configured "Select Currency" energy cost per kWh
                            'alias': '{NOAH_NAME}',  # Friendly name of the noah device
                            'model': None,  # Model Name of the noah device
                            'plantName': '{PLANT_NAME}',  # Friendly name of the plant
                            'tempType': None,
                            'moneyUnitText': "euro",  # Configured "Select Currency" (Value from the unitList)
                        },
                        'plantList': [
                            {
                                'plantId': {PLANT_ID},  #  The ID of the plant
                                'plantImgName': None,  # plant Image
                                'plantName': '{PLANT_NAME}',  # name of the plant
                            }
                        ]
                    }
                }
        """

        response = self.session.post(
            self.get_url("noahDeviceApi/noah/getNoahInfoBySn"), data={"deviceSn": serial_number}
        )
        return response.json()

    def update_plant_settings(
        self, plant_id: str, changed_settings: Dict[str, Any], current_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Applies settings to the plant e.g. ID, Location, Timezone
        See README for all possible settings options

        Args:
            plant_id (str):
                The id of the plant you wish to update the settings for
            changed_settings (Dict[str, Any]):
                settings to be changed and their value
            current_settings (Optional[Dict[str, Any]]) = None:
                current settings of the plant (use the response from plant_settings)
                will be fetched automatically if value is None

        Returns:
            Dict[str, Any]:
                A response from the server stating whether the configuration was successful or not
        """

        # If no existing settings have been provided then get them from the growatt server
        if current_settings is None:
            current_settings = self.plant_settings(plant_id=plant_id)

        # These are the parameters that the form requires, without these an error is thrown. Pre-populate their values with the current values
        form_settings = {
            "plantCoal": (None, str(current_settings["formulaCoal"])),
            "plantSo2": (None, str(current_settings["formulaSo2"])),
            "accountName": (None, str(current_settings["userAccount"])),
            "plantID": (None, str(current_settings["id"])),
            "plantFirm": (None, "0"),  # Hardcoded to 0 as I can't work out what value it should have
            "plantCountry": (None, str(current_settings["country"])),
            "plantType": (None, str(current_settings["plantType"])),
            "plantIncome": (None, str(current_settings["formulaMoneyStr"])),
            "plantAddress": (None, str(current_settings["plantAddress"])),
            "plantTimezone": (None, str(current_settings["timezone"])),
            "plantLng": (None, str(current_settings["plant_lng"])),
            "plantCity": (None, str(current_settings["city"])),
            "plantCo2": (None, str(current_settings["formulaCo2"])),
            "plantMoney": (None, str(current_settings["formulaMoneyUnitId"])),
            "plantPower": (None, str(current_settings["nominalPower"])),
            "plantLat": (None, str(current_settings["plant_lat"])),
            "plantDate": (None, str(current_settings["createDateText"])),
            "plantName": (None, str(current_settings["plantName"])),
        }

        # Overwrite the current value of the setting with the new value
        for setting, value in changed_settings.items():
            form_settings[setting] = (None, str(value))

        response = self.session.post(self.get_url("newTwoPlantAPI.do?op=updatePlant"), files=form_settings)

        return response.json()

    def update_device_alias(
        self,
        device_id: str,
        new_alias: str,
        device_type: Literal["tlx"] = "tlx",
    ) -> bool:
        """
        Change device (inverter) name/alias

        Args:
            device_id (str):
                Serial number of the inverter
            device_type (Literal["tlx"] = "tlx":
                Type of the device (inverter)
                ! until now, this setting has only be seen for TLX (NEO) inverter
            new_alias (str):
                New alias to be set

        Returns:
            bool
                True if change was successful
        """

        url = self.get_url("newTwoPlantAPI.do")
        params = {"op": "updAllDevice"}
        data = {
            "deviceType": device_type,
            "deviceSn": device_id,
            "content": new_alias,
            "updateType": 0,
        }

        response = self.session.post(url=url, params=params, data=data)

        return response.json().get("success") or False

    def read_inverter_registers(
        self,
        inverter_id: str,
        register_address_start: int,
        register_address_end: Optional[int] = None,
        device_type: Literal["pcs", "bms", "jlinv", "min", "mic", "mod", "neo", "tlx"] = "tlx",
    ) -> Dict[str, Any]:
        """
        Read inverter settings register

        seen in App -> Inverter -> Configure -> select any item -> press "Read" button

        Args:
            inverter_id (str):
                The ID of the (TLX) inverter.
            register_address_start (int):
                query registers from register_address_start to _end
            register_address_end (Optional[int]) = None
                query registers from register_address_start to _end
                defaults to register_address_start if not set
            device_type (Literal["pcs", "bms", "jlinv", "min", "mic", "mod", "neo", "tlx"]) = "tlx":
                The type of device to get the data from.
                Supported values (so far):
                * "pcs"   (PCS)
                * "bms"   (BMS - Battery Management System)
                * "jlinv" (Solis Inverter)
                * "min"   (MIN Inverter)
                * "mic"   (MIC Inverter)
                * "mod"   (MOD Inverter)
                * "neo"   (NEO Inverter)
                * "tlx"   (MIN/MIC/MOD/NEO)

        Returns:
            Dict[str, Any]
            e.g. (success)
            {
                'success': True,
                'error_message': '',
                'register': {
                    0: '1',
                    1: '413',
                    ...
                    100: '2300'
                }
            }
            e.g. (failure)
            {
                'success': False,
                'error_message': '501 inverter offline',
                'register': {}
            }
        """

        if register_address_end is None:
            register_address_end = register_address_start

        device_type_id = {
            "pcs": 5,
            "bms": 6,
            "jlinv": 7,
            "min": 8,
            "mic": 8,
            "mod": 8,
            "neo": 8,
            "tlx": 8,
        }[device_type.lower()]

        response = self.session.post(
            url=self.get_url("newTcpsetAPI.do"),
            params={"action": "readDeviceParam"},
            data={
                "serialNum": inverter_id,
                "deviceTypeStr": device_type_id,
                "startAddr": register_address_start,
                "endAddr": register_address_end,
                "paramId": "set_any_reg",
            },
        )
        response_json = response.json()

        success = response_json.get("result") == 1
        error_message = response_json.get("msg") or ""
        if error_message == "501":
            # 501 is returned if inverter is offline
            error_message += " inverter offline"
        elif error_message == "500":
            # 500 is returned in case of timeout
            # for my NEO800MX, the maximum range is between 50 and 100 registers at once
            error_message += " timeout or inverter offline"
            if register_address_end - register_address_start > 1:
                error_message += " - try querying less registers at once"

        # all registers are returned in 'param1' separated by "-"
        #  e.g. 'obj': {'param1': '1-413-0-'}
        if success:
            register_data = {
                register_nr: register_value
                for register_nr, register_value in zip(
                    range(register_address_start, register_address_end + 1), response_json["obj"]["param1"].split("-")
                )
            }
        else:
            register_data = {}

        result_dict = {
            "register": register_data,
            "success": success,
            "error_message": error_message,
        }

        return result_dict

    def read_inverter_setting(
        self,
        inverter_id: str,
        device_type: Literal["pcs", "bms", "jlinv", "min", "mic", "mod", "neo", "tlx"] = "tlx",
        setting_name: Optional[str] = None,
        register_address: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Read single inverter setting

        seen in App -> Inverter -> Configure -> select any item -> press "Read" button

        You must specify
        * either a setting name (e.g. "pv_active_p_rate")
        * or a register address (e.g. 90 for "Country & Regulation")

        Args:
            inverter_id (str):
                    The ID of the (TLX) inverter.
            device_type (Literal["pcs", "bms", "jlinv", "min", "mic", "mod", "neo", "tlx"]) = "tlx":
                The type of device to get the data from.
                Supported values (so far):
                * "pcs"   (PCS)
                * "bms"   (BMS - Battery Management System)
                * "jlinv" (Solis Inverter)
                * "min"   (MIN Inverter)
                * "mic"   (MIC Inverter)
                * "mod"   (MOD Inverter)
                * "neo"   (NEO Inverter)
                * "tlx"   (MIN/MIC/MOD/NEO)
            setting_name (Optional[str]) = None
                setting to query (e.g. "pv_active_p_rate")
            register_address (Optional[int]) = None
                register address to query (e.g. 90 for "Country & Regulation")

        Returns:
            Dict[str, Any]
                Info: JSON response from the server whether the configuration was successful
                * result==0 means success, result==1 means failure
                * msg "501" means inverter is offline
            e.g. (success)
            {
                "success": True,
                "error_message": "",
                "param1": "0",
            }
            e.g. (failure)
            {
                "success": False,
                "error_message": "501 inverter offline",
            }
        """

        assert (
            setting_name is not None or register_address is not None
        ), "You must specify either a setting name or a register address"
        # ensure only one is set
        assert (
            setting_name is None or register_address is None
        ), "You must specify either a setting name or a register address - not both"

        if setting_name:
            data = {
                "paramId": setting_name,
                "startAddr": -1,
                "endAddr": -1,
            }
        else:
            data = {
                "startAddr": register_address,
                "endAddr": register_address,
                "paramId": "set_any_reg",
            }

        device_type_id = {
            "pcs": 5,
            "bms": 6,
            "jlinv": 7,
            "min": 8,
            "mic": 8,
            "mod": 8,
            "neo": 8,
            "tlx": 8,
        }[device_type.lower()]
        data["deviceTypeStr"] = device_type_id

        # add inverter ID
        data["serialNum"] = inverter_id

        response = self.session.post(
            url=self.get_url("newTcpsetAPI.do"), params={"action": "readDeviceParam"}, data=data
        )
        response_json = response.json()

        success = response_json.get("result") == 1
        error_message = response_json.get("msg") or ""
        if error_message == "501":
            # 501 is returned if inverter is offline
            error_message += " inverter offline"
        elif error_message == "500":
            # 500 is returned if inverter did not respond
            error_message += " timeout or inverter offline"

        result_dict = response_json.get("obj") or {}
        result_dict["success"] = success
        result_dict["error_message"] = error_message

        return result_dict

    def _update_inverter_setting(
        self,
        default_parameters: Dict[str, Any],
        parameters: Union[Dict[str, Any], List[str]],
    ) -> Dict[str, Any]:
        """
        Applies settings for specified system based on serial number
        See README for known working settings

        Args:
            default_parameters (Dict[str, Any]):
                Default set of parameters for the setting call (dict)
            parameters (Union[Dict[str, Any], List[str]]):
                Parameters to be sent to the system

        Returns:
            Dict[str, Any]
                JSON response from the server whether the configuration was successful
        """
        settings_parameters = parameters

        # If we've been passed an array then convert it into a dictionary
        if isinstance(parameters, list):
            settings_parameters = {f"param{idx}": param for idx, param in enumerate(parameters, start=1)}

        settings_parameters = {**default_parameters, **settings_parameters}

        response = self.session.post(self.get_url("newTcpsetAPI.do"), params=settings_parameters)

        return response.json()

    def update_mix_inverter_setting(
        self,
        serial_number: str,
        setting_type: str,
        parameters: Union[Dict[str, Any], List[str]],
    ) -> Dict[str, Any]:
        """
        Alias for setting inverter parameters on a mix inverter
        See README for known working settings

        Args:
            serial_number (str):
                The ID of the (MIX) inverter
            setting_type (str):
                Setting to be configured
            parameters (Union[Dict[str, Any], List[str]]):
                Parameters to be sent to the system

        Returns:
            Dict[str, Any]:
                JSON response from the server whether the configuration was successful
        """

        default_parameters = {"op": "mixSetApiNew", "serialNum": serial_number, "type": setting_type}
        return self._update_inverter_setting(default_parameters=default_parameters, parameters=parameters)

    def update_ac_inverter_setting(
        self,
        serial_number: str,
        setting_type: str,
        parameters: Union[Dict[str, Any], List[str]],
    ) -> Dict[str, Any]:
        """
        Alias for setting inverter parameters on an AC-coupled inverter
        See README for known working settings

        Args:
            serial_number (str):
                The ID of the (SPA) inverter
            setting_type (str):
                Setting to be configured
            parameters (Union[Dict[str, Any], List[str]]):
                Parameters to be sent to the system

        Returns:
            Dict[str, Any]:
                JSON response from the server whether the configuration was successful

        """
        default_parameters = {"op": "spaSetApi", "serialNum": serial_number, "type": setting_type}
        return self._update_inverter_setting(default_parameters=default_parameters, parameters=parameters)

    def update_tlx_inverter_time_segment(
        self,
        serial_number: str,
        segment_id: int,
        batt_mode: int,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        enabled: bool,
    ) -> Dict[str, Any]:
        """
        Updates the time segment settings for a TLX hybrid inverter.

        Args:
            serial_number (str):
                The ID of the (TLX) inverter
            segment_id (int):
                ID of the time segment to be updated
            batt_mode (int):
                Battery mode
            start_time (datetime.time):
                Start time of the segment (datetime.time):
            end_time (datetime.time):
                End time of the segment
            enabled (bool):
                Whether the segment is enabled

        Returns:
            Dict[str, Any]:
                JSON response from the server whether the configuration was successful
        """

        params = {"op": "tlxSet"}
        data = {
            "serialNum": serial_number,
            "type": f"time_segment{segment_id}",
            "param1": batt_mode,
            "param2": start_time.strftime("%H"),
            "param3": start_time.strftime("%M"),
            "param4": end_time.strftime("%H"),
            "param5": end_time.strftime("%M"),
            "param6": "1" if enabled else "0",
        }

        response = self.session.post(self.get_url("newTcpsetAPI.do"), params=params, data=data)

        result = response.json()

        if not result.get("success", False):
            raise Exception(f"Failed to update TLX inverter time segment: {result.get('msg', 'Unknown error')}")

        return result

    def update_tlx_inverter_setting(
        self,
        serial_number: str,
        setting_type: str,
        parameter: Union[
            List[Any],
            Dict[str, Any],
            Any,  # bool, float, str,...
        ],
    ) -> Dict[str, Any]:
        """
        Alias for setting parameters on a tlx hybrid inverter
        See README for known working settings

        Args:
            serial_number (str):
                The ID (serial number/device_sn/tlx_id) of the TLX inverter.
            setting_type (str):
                Name of setting to be configured (e.g. "pv_active_p_rate")
            parameter (Union[str, List[Any], Dict[str, Any]]):
                Parameter(s) to be sent to the system
                * str/int will be converted to {"param1": parameter}
                * list  will be converted to {"param1": parameter[0], ...}
                * dict will be passed as is. Format must be {"param1": "value1", "param^2": "value2", ...}

        Returns:
            Dict[str, Any]
                JSON response from the server whether the configuration was successful
        """
        default_parameters = {"op": "tlxSet", "serialNum": serial_number, "type": setting_type}

        # If parameter is a single value or list of values, convert it to a dictionary
        if not isinstance(parameter, (dict, list)):
            parameter = {"param1": parameter}
        elif isinstance(parameter, list):
            parameter = {f"param{index+1}": param for index, param in enumerate(parameter)}

        return self._update_inverter_setting(default_parameters=default_parameters, parameters=parameter)

    def update_noah_settings(
        self, serial_number: str, setting_type: str, parameters: Union[Dict[str, str], List[str]]
    ) -> Dict[str, Any]:
        """
        Applies settings for specified noah device based on serial number
        See README for known working settings

        Args:
            serial_number (str):
                Serial number (device_sn) of the noah
            setting_type (str):
                Setting to be configured
            parameters (Union[Dict[str, str], List[str]]):
                Parameters to be sent to the system

        Returns:
            Dict[str, Any]:
                JSON response from the server whether the configuration was successful
        """

        default_parameters = {"serialNum": serial_number, "type": setting_type}
        settings_parameters = parameters

        # If we've been passed an array then convert it into a dictionary
        if isinstance(parameters, list):
            settings_parameters = {}
            for index, param in enumerate(parameters, start=1):
                settings_parameters["param" + str(index)] = param

        settings_parameters = {**default_parameters, **settings_parameters}

        response = self.session.post(self.get_url("noahDeviceApi/noah/set"), data=settings_parameters)

        return response.json()

    def weather(self, language: str = "en"):
        """
        Get weather data as shown in app dashboard

        Args:
            language (str) = "en":
                e.g. "en" / "de" / "cn" / ...

        Returns:
            Dict[str, Any]: A dictionary containing the weather data
                e.g.
                {
                    'city': '{CITY_NAME}',
                    'week': 'Thursday'
                    'radiant': '',
                    'tempType': 0,
                    'status': 'ok',
                    'basic': {
                        'admin_area': '{COUNTY_NAME}',
                        'cnty': 'Germany',
                        'location': '{CITY_NAME}',
                        'parent_city': '{CITY_NAME}',
                        'sr': '07:00',        # sunrise time
                        'ss': '17:30',        # sunset time
                        'toDay': '2025-01-30'
                    },
                    'now': {
                        'cloud': '11',        # cloudiness in percent
                        'cond_code': '100',   # weather condition code
                        'cond_txt': 'Sunny',
                        'fl': '7',            # feels like temperature, °C
                        'hum': '70',          # Relative humidity in percent
                        'newTmp': '9.0°C',
                        'pcpn': '0.0',        # Accumulated precipitation in the last hour, mm/h
                        'pres': '1017',       # Atmospheric pressure, hPa
                        'tmp': '9',           # Temperature, °C
                        'wind_deg': '180',    # Wind direction in azimuth degree, °
                        'wind_dir': 'S',      # Wind direction str. e.g. "ESE"
                        'wind_sc': '2',       # Wind scale, Beaufort scale 0-12(-17)
                        'wind_spd': '7'       # Wind speed, km/h
                    },
                    'update': {
                        'loc': '2025-01-30 22:06',
                        'utc': '2025-01-30 14:06'
                    },
                }
        """

        url = self.get_url("newPlantAPI.do")
        params = {"op": "getAPPWeattherTwo"}
        data = {"language": language}

        response = self.session.post(url=url, params=params, data=data)
        response_json = response.json()
        response_json = response_json.get("obj", {})
        response_json.update(response_json["data"]["HeWeather6"][0])
        response_json.pop("dataStr", None)
        response_json.pop("data", None)

        return response_json
