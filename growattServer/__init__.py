import datetime
from datetime import date, timedelta
from enum import IntEnum
import requests
from random import randint
import warnings
import hashlib

name = "growattServer"

BATT_MODE_LOAD_FIRST = 0
BATT_MODE_BATTERY_FIRST = 1
BATT_MODE_GRID_FIRST = 2

def hash_password(password):
    """
    Normal MD5, except add c if a byte of the digest is less than 10.
    """
    password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
    for i in range(0, len(password_md5), 2):
        if password_md5[i] == '0':
            password_md5 = password_md5[0:i] + 'c' + password_md5[i + 1:]
    return password_md5

class Timespan(IntEnum):
    hour = 0
    day = 1
    month = 2

class GrowattApi:
    server_url = 'https://openapi.growatt.com/'
    agent_identifier = "Dalvik/2.1.0 (Linux; U; Android 12; https://github.com/indykoning/PyPi_GrowattServer)"

    def __init__(self, add_random_user_id=False, agent_identifier=None, token=None):
        """
        Initialize the Growatt API client.
        
        Args:
            add_random_user_id (bool): Add a random user ID to the agent identifier.
            agent_identifier (str): Override the default agent identifier.
            token (str): API token for authentication (use this for V1 API access).
            username (str): Username for login-based authentication.
            password (str): Password for login-based authentication.
            is_password_hashed (bool): Whether the provided password is already hashed.
        """
        self.api_url = f"{self.server_url}v1/"
        self.token = token
        self.v1_api_enabled = token is not None
        self.session = requests.Session()
        self.session.hooks = {
            'response': lambda response, *args, **kwargs: response.raise_for_status()
        }

        # Set up authentication
        if token:
            print("Using token-based authentication")
            # Use token-based auth for V1 API
            self.session.headers.update({"token": token})
        else:
            print("Using password-based authentication")
            if agent_identifier is not None:
                self.agent_identifier = agent_identifier
            headers = {'User-Agent': self.agent_identifier}
            self.session.headers.update(headers)
            # If a random user id is required, generate a 5 digit number and add it to the user agent
            if add_random_user_id:
                random_number = ''.join(["{}".format(randint(0, 9)) for num in range(0, 5)])
                self.agent_identifier += " - " + random_number


    def __get_date_string(self, timespan=None, date=None):
        if timespan is not None:
            assert timespan in Timespan

        if date is None:
            date = datetime.datetime.now()

        date_str=""
        if timespan == Timespan.month:
            date_str = date.strftime('%Y-%m')
        else:
            date_str = date.strftime('%Y-%m-%d')

        return date_str

    def get_url(self, page):
        """
        Simple helper function to get the page URL.
        """
        return self.server_url + page

    def get_v1_url(self, page):
        """
        Simple helper function to get the page URL for v1 API.
        """
        return self.api_url + page
    
    def login(self, username, password, is_password_hashed=False):
        """
        Log the user in.

        Returns
        'data' -- A List containing Objects containing the folowing
            'plantName' -- Friendly name of the plant
            'plantId'   -- The ID of the plant
        'service'
        'quality'
        'isOpenSmartFamily'
        'totalData' -- An Object
        'success'   -- True or False
        'msg'
        'app_code'
        'user' -- An Object containing a lot of user information
            'uid'
            'userLanguage'
            'inverterGroup' -- A List
            'timeZone' -- A Number
            'lat'
            'lng'
            'dataAcqList' -- A List
            'type'
            'accountName' -- The username
            'password' -- The password hash of the user
            'isValiPhone'
            'kind'
            'mailNotice' -- True or False
            'id'
            'lasLoginIp'
            'lastLoginTime'
            'userDeviceType'
            'phoneNum'
            'approved' -- True or False
            'area' -- Continent of the user
            'smsNotice' -- True or False
            'isAgent'
            'token'
            'nickName'
            'parentUserId'
            'customerCode'
            'country'
            'isPhoneNumReg'
            'createDate'
            'rightlevel'
            'appType'
            'serverUrl'
            'roleId'
            'enabled' -- True or False
            'agentCode'
            'inverterList' -- A list
            'email'
            'company'
            'activeName'
            'codeIndex'
            'appAlias'
            'isBigCustomer'
            'noticeType'
        """
        if not is_password_hashed:
            password = hash_password(password)

        response = self.session.post(self.get_url('newTwoLoginAPI.do'), data={
            'userName': username,
            'password': password
        })

        data = response.json()['back']
        if data['success']:
            data.update({
                'userId': data['user']['id'],
                'userLevel': data['user']['rightlevel']
            })
        return data

    def plant_list(self, user_id):
        """
        Get a list of plants connected to this account.

        Args:
            user_id (str): The ID of the user.

        Returns:
            list: A list of plants connected to the account.

        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.get(
            self.get_url('PlantListAPI.do'),
            params={'userId': user_id},
            allow_redirects=False
        )

        return response.json().get('back', [])

    def plant_detail(self, plant_id, timespan, date=None):
        """
        Get plant details for specified timespan.

        Args:
            plant_id (str): The ID of the plant.
            timespan (Timespan): The ENUM value conforming to the time window you want e.g. hours from today, days, or months.
            date (datetime, optional): The date you are interested in. Defaults to datetime.datetime.now().

        Returns:
            dict: A dictionary containing the plant details.

        Raises:
            Exception: If the request to the server fails.
        """
        date_str = self.__get_date_string(timespan, date)

        response = self.session.get(self.get_url('PlantDetailAPI.do'), params={
            'plantId': plant_id,
            'type': timespan.value,
            'date': date_str
        })

        return response.json().get('back', {})

    def plant_list_two(self):
        """
        Get a list of all plants with detailed information.

        Returns:
            list: A list of plants with detailed information.
        """
        response = self.session.post(
            self.get_url('newTwoPlantAPI.do'),
            params={'op': 'getAllPlantListTwo'},
            data={
                'language': '1',
                'nominalPower': '',
                'order': '1',
                'pageSize': '15',
                'plantName': '',
                'plantStatus': '',
                'toPageNum': '1'
            }
        )

        return response.json().get('PlantList', [])

    def inverter_data(self, inverter_id, date=None):
        """
        Get inverter data for specified date or today.

        Args:
            inverter_id (str): The ID of the inverter.
            date (datetime, optional): The date you are interested in. Defaults to datetime.datetime.now().

        Returns:
            dict: A dictionary containing the inverter data.

        Raises:
            Exception: If the request to the server fails.
        """
        date_str = self.__get_date_string(date=date)
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterData',
            'id': inverter_id,
            'type': 1,
            'date': date_str
        })

        return response.json()

    def inverter_detail(self, inverter_id):
        """
        Get detailed data from PV inverter.

        Args:
            inverter_id (str): The ID of the inverter.

        Returns:
            dict: A dictionary containing the inverter details.

        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData',
            'inverterId': inverter_id
        })

        return response.json()

    def inverter_detail_two(self, inverter_id):
        """
        Get detailed data from PV inverter (alternative endpoint).

        Args:
            inverter_id (str): The ID of the inverter.

        Returns:
            dict: A dictionary containing the inverter details.

        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData_two',
            'inverterId': inverter_id
        })

        return response.json()

    def tlx_system_status(self, plant_id, tlx_id):
        """
        Get status of the system

        Args:
            plant_id (str): The ID of the plant.
            tlx_id (str): The ID of the TLX inverter.

        Returns:
            dict: A dictionary containing system status.

        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getSystemStatus_KW"},
            data={"plantId": plant_id,
                  "id": tlx_id}
        )

        return response.json().get('obj', {})

    def tlx_energy_overview(self, plant_id, tlx_id):
        """
        Get energy overview

        Args:
            plant_id (str): The ID of the plant.
            tlx_id (str): The ID of the TLX inverter.

        Returns:
            dict: A dictionary containing energy data.

        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getEnergyOverview"},
            data={"plantId": plant_id,
                  "id": tlx_id}
        )

        return response.json().get('obj', {})

    def tlx_energy_prod_cons(self, plant_id, tlx_id, timespan=Timespan.hour, date=None):
        """
        Get energy production and consumption (KW)

        Args:
            tlx_id (str): The ID of the TLX inverter.
            timespan (Timespan): The ENUM value conforming to the time window you want e.g. hours from today, days, or months.
            date (datetime): The date you are interested in.

        Returns:
            dict: A dictionary containing energy data.

        Raises:
            Exception: If the request to the server fails.
        """

        date_str = self.__get_date_string(timespan, date)

        response = self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getEnergyProdAndCons_KW"},
            data={'date': date_str,
                "plantId": plant_id,
                "language": "1",
                 "id": tlx_id,
                 "type": timespan.value}
        )

        return response.json().get('obj', {})

    def tlx_data(self, tlx_id, date=None):
        """
        Get TLX inverter data for specified date or today.

        Args:
            tlx_id (str): The ID of the TLX inverter.
            date (datetime, optional): The date you are interested in. Defaults to datetime.datetime.now().

        Returns:
            dict: A dictionary containing the TLX inverter data.

        Raises:
            Exception: If the request to the server fails.
        """
        date_str = self.__get_date_string(date=date)
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxData',
            'id': tlx_id,
            'type': 1,
            'date': date_str
        })

        return response.json()

    def tlx_detail(self, tlx_id):
        """
        Get detailed data from TLX inverter.

        Args:
            tlx_id (str): The ID of the TLX inverter.

        Returns:
            dict: A dictionary containing the detailed TLX inverter data.

        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxDetailData',
            'id': tlx_id
        })

        return response.json()

    def tlx_params(self, tlx_id):
        """
        Get parameters for TLX inverter.

        Args:
            tlx_id (str): The ID of the TLX inverter.

        Returns:
            dict: A dictionary containing the TLX inverter parameters.

        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxParams',
            'id': tlx_id 
        })

        return response.json()

    def tlx_all_settings(self, tlx_id):
        """
        Get all possible settings from TLX inverter.

        Args:
            tlx_id (str): The ID of the TLX inverter.

        Returns:
            dict: A dictionary containing all possible settings for the TLX inverter.

        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.post(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxSetData'
        }, data={
            'serialNum': tlx_id
        })

        return response.json().get('obj', {}).get('tlxSetBean')

    def tlx_enabled_settings(self, tlx_id):
        """
        Get "Enabled settings" from TLX inverter.
        
        Args:
            tlx_id (str): The ID of the TLX inverter.
        
        Returns:
            dict: A dictionary containing the enabled settings.
        
        Raises:
            Exception: If the request to the server fails.
        """
        string_time = datetime.datetime.now().strftime('%Y-%m-%d')
        response = self.session.post(
            self.get_url('newLoginAPI.do'),
            params={'op': 'getSetPass'},
            data={'deviceSn': tlx_id, 'stringTime': string_time, 'type': '5'}
        )

        return response.json().get('obj', {})

    def tlx_battery_info(self, serial_num):
        """
        Get battery information.
        
        Args:
            serial_num (str): The serial number of the battery.
        
        Returns:
            dict: A dictionary containing the battery information.
        
        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.post(
            self.get_url('newTlxApi.do'),
            params={'op': 'getBatInfo'},
            data={'lan': 1, 'serialNum': serial_num}
        )

        return response.json().get('obj', {})

    def tlx_battery_info_detailed(self, plant_id, serial_num):
        """
        Get detailed battery information.
        
        Args:
            plant_id (str): The ID of the plant.
            serial_num (str): The serial number of the battery.
        
        Returns:
            dict: A dictionary containing the detailed battery information.
        
        Raises:
            Exception: If the request to the server fails.
        """
        response = self.session.post(
            self.get_url('newTlxApi.do'),
            params={'op': 'getBatDetailData'},
            data={'lan': 1, 'plantId': plant_id, 'id': serial_num}
        )

        return response.json()

    def mix_info(self, mix_id, plant_id = None):
        """
        Returns high level values from Mix device

        Keyword arguments:
        mix_id -- The serial number (device_sn) of the inverter
        plant_id -- The ID of the plant (the mobile app uses this but it does not appear to be necessary) (default None)

        Returns:
        'acChargeEnergyToday' -- ??? 2.7
        'acChargeEnergyTotal' -- ??? 25.3
        'acChargePower' -- ??? 0
        'capacity': '45' -- The current remaining capacity of the batteries (same as soc but without the % sign)
        'eBatChargeToday' -- Battery charged today in kWh
        'eBatChargeTotal' -- Battery charged total (all time) in kWh
        'eBatDisChargeToday' -- Battery discharged today in kWh
        'eBatDisChargeTotal' -- Battery discharged total (all time) in kWh
        'epvToday' -- Energy generated from PVs today in kWh
        'epvTotal' -- Energy generated from PVs total (all time) in kWh
        'isCharge'-- ??? 0 - Possible a 0/1 based on whether or not the battery is charging
        'pCharge1' -- ??? 0
        'pDischarge1' -- Battery discharging rate in W
        'soc' -- Statement of charge including % symbol
        'upsPac1' -- ??? 0
        'upsPac2' -- ??? 0
        'upsPac3' -- ??? 0
        'vbat' -- Battery Voltage
        'vbatdsp' -- ??? 51.8
        'vpv1' -- Voltage PV1
        'vpv2' -- Voltage PV2
        """
        request_params={
            'op': 'getMixInfo',
            'mixId': mix_id
        }

        if (plant_id):
          request_params['plantId'] = plant_id

        response = self.session.get(self.get_url('newMixApi.do'), params=request_params)

        return response.json().get('obj', {})

    def mix_totals(self, mix_id, plant_id):
        """
        Returns "Totals" values from Mix device

        Keyword arguments:
        mix_id -- The serial number (device_sn) of the inverter
        plant_id -- The ID of the plant

        Returns:
        'echargetoday' -- Battery charged today in kWh (same as eBatChargeToday from mix_info)
        'echargetotal' -- Battery charged total (all time) in kWh (same as eBatChargeTotal from mix_info)
        'edischarge1Today' -- Battery discharged today in kWh (same as eBatDisChargeToday from mix_info)
        'edischarge1Total' -- Battery discharged total (all time) in kWh (same as eBatDisChargeTotal from mix_info)
        'elocalLoadToday' -- Load consumption today in kWh
        'elocalLoadTotal' -- Load consumption total (all time) in kWh
        'epvToday' -- Energy generated from PVs today in kWh (same as epvToday from mix_info)
        'epvTotal' -- Energy generated from PVs total (all time) in kWh (same as epvTotal from mix_info)
        'etoGridToday' -- Energy exported to the grid today in kWh
        'etogridTotal' -- Energy exported to the grid total (all time) in kWh
        'photovoltaicRevenueToday' -- Revenue earned from PV today in 'unit' currency
        'photovoltaicRevenueTotal' -- Revenue earned from PV total (all time) in 'unit' currency
        'unit' -- Unit of currency for 'Revenue'
        """
        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getEnergyOverview',
            'mixId': mix_id,
            'plantId': plant_id
        })

        return response.json().get('obj', {})

    def mix_system_status(self, mix_id, plant_id):
        """
        Returns current "Status" from Mix device

        Keyword arguments:
        mix_id -- The serial number (device_sn) of the inverter
        plant_id -- The ID of the plant

        Returns:
        'SOC' -- Statement of charge (remaining battery %)
        'chargePower' -- Battery charging rate in kw
        'fAc' -- Frequency (Hz)
        'lost' -- System status e.g. 'mix.status.normal'
        'pLocalLoad' -- Load conumption in kW
        'pPv1' -- PV1 Wattage in W
        'pPv2' -- PV2 Wattage in W
        'pactogrid' -- Export to grid rate in kW
        'pactouser' -- Import from grid rate in kW
        'pdisCharge1' -- Discharging batteries rate in kW
        'pmax' -- ??? 6 ??? PV Maximum kW ??
        'ppv' -- PV combined Wattage in kW
        'priorityChoose' -- Priority setting - 0=Local load
        'status' -- System statue - ENUM - Unknown values
        'unit' -- Unit of measurement e.g. 'kW'
        'upsFac' -- ??? 0
        'upsVac1' -- ??? 0
        'uwSysWorkMode' -- ??? 6
        'vAc1' -- Grid voltage in V
        'vBat' -- Battery voltage in V
        'vPv1' -- PV1 voltage in V
        'vPv2' -- PV2 voltage in V
        'vac1' -- Grid voltage in V (same as vAc1)
        'wBatteryType' -- ??? 1
        """
        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getSystemStatus_KW',
            'mixId': mix_id,
            'plantId': plant_id
        })

        return response.json().get('obj', {})

    def mix_detail(self, mix_id, plant_id, timespan=Timespan.hour, date=None):
        """
        Get Mix details for specified timespan

        Keyword arguments:
        mix_id -- The serial number (device_sn) of the inverter
        plant_id -- The ID of the plant
        timespan -- The ENUM value conforming to the time window you want e.g. hours from today, days, or months (Default Timespan.hour)
        date -- The date you are interested in (Default datetime.datetime.now())

        Returns:
        A chartData object where each entry is for a specific 5 minute window e.g. 00:05 and 00:10 respectively (below)
        'chartData': {   '00:05': {   'pacToGrid' -- Export rate to grid in kW
                                      'pacToUser' -- Import rate from grid in kW
                                      'pdischarge' -- Battery discharge in kW
                                      'ppv' -- Solar generation in kW
                                      'sysOut' -- Load consumption in kW
                                  },
                         '00:10': {   'pacToGrid': '0',
                                      'pacToUser': '0.93',
                                      'pdischarge': '0',
                                      'ppv': '0',
                                      'sysOut': '0.93'},
                          ......
                     }
        'eAcCharge' -- Exported to grid in kWh
        'eCharge' -- System production in kWh = Self-consumption + Exported to Grid
        'eChargeToday' -- Load consumption from solar in kWh
        'eChargeToday1' -- Self-consumption in kWh
        'eChargeToday2' -- Self-consumption in kWh (eChargeToday + echarge1)
        'echarge1' -- Load consumption from battery in kWh
        'echargeToat' -- Total battery discharged (all time) in kWh
        'elocalLoad' -- Load consumption in kW (battery + solar + imported)
        'etouser' -- Load consumption imported from grid in kWh
        'photovoltaic' -- Load consumption from solar in kWh (same as eChargeToday)
        'ratio1' -- % of system production that is self-consumed
        'ratio2' -- % of system production that is exported
        'ratio3' -- % of Load consumption that is "self consumption"
        'ratio4' -- % of Load consumption that is "imported from grid"
        'ratio5' -- % of Self consumption that is directly from Solar
        'ratio6' -- % of Self consumption that is from batteries
        'unit' -- Unit of measurement e.g kWh
        'unit2' -- Unit of measurement e.g kW


        NOTE - It is possible to calculate the PV generation that went into charging the batteries by performing the following calculation:
        Solar to Battery = Solar Generation - Export to Grid - Load consumption from solar
                           epvToday (from mix_info) - eAcCharge - eChargeToday
        """
        date_str = self.__get_date_string(timespan, date)

        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getEnergyProdAndCons_KW',
            'plantId': plant_id,
            'mixId': mix_id,
            'type': timespan.value,
            'date': date_str
        })

        return response.json().get('obj', {})

    def dashboard_data(self, plant_id, timespan=Timespan.hour, date=None):
        """
        Get 'dashboard' data for specified timespan
        NOTE - All numerical values returned by this api call include units e.g. kWh or %
             - Many of the 'total' values that are returned for a Mix system are inaccurate on the system this was tested against.
               However, the statistics that are correct are not available on any other interface, plus these values may be accurate for
               non-mix types of system. Where the values have been proven to be inaccurate they are commented below.

        Keyword arguments:
        plant_id -- The ID of the plant
        timespan -- The ENUM value conforming to the time window you want e.g. hours from today, days, or months (Default Timespan.hour)
        date -- The date you are interested in (Default datetime.datetime.now())

        Returns:
        A chartData object where each entry is for a specific 5 minute window e.g. 00:05 and 00:10 respectively (below)
        NOTE: The keys are interpreted differently, the examples below describe what they are used for in a 'Mix' system
        'chartData': {   '00:05': {   'pacToUser' -- Power from battery in kW
                                      'ppv' -- Solar generation in kW
                                      'sysOut' -- Load consumption in kW
                                      'userLoad' -- Export in kW
                                  },
                         '00:10': {   'pacToUser': '0',
                                      'ppv': '0',
                                      'sysOut': '0.7',
                                      'userLoad': '0'},
                          ......
                     }
        'chartDataUnit' -- Unit of measurement e.g. 'kW',
        'eAcCharge' -- Energy exported to the grid in kWh e.g. '20.5kWh' (not accurate for Mix systems)
        'eCharge' -- System production in kWh = Self-consumption + Exported to Grid e.g '23.1kWh' (not accurate for Mix systems - actually showing the total 'load consumption'
        'eChargeToday1' -- Self-consumption of PPV (possibly including excess diverted to batteries) in kWh e.g. '2.6kWh' (not accurate for Mix systems)
        'eChargeToday2' -- Total self-consumption (PPV consumption(eChargeToday2Echarge1) + Battery Consumption(echarge1)) e.g. '10.1kWh' (not accurate for Mix systems)
        'eChargeToday2Echarge1' -- Self-consumption of PPV only e.g. '0.8kWh' (not accurate for Mix systems)
        'echarge1' -- Self-consumption from Battery only e.g. '9.3kWh'
        'echargeToat' -- Not used on Dashboard view, likely to be total battery discharged e.g. '152.1kWh'
        'elocalLoad' -- Total load consumption (etouser + eChargeToday2) e.g. '20.3kWh', (not accurate for Mix systems)
        'etouser'-- Energy imported from grid today (includes both directly used by load and AC battery charging e.g. '10.2kWh'
        'keyNames' -- Keys to be used for the graph data e.g. ['Solar', 'Load Consumption', 'Export To Grid', 'From Battery']
        'photovoltaic' -- Same as eChargeToday2Echarge1 e.g. '0.8kWh'
        'ratio1' -- % of 'Solar production' that is self-consumed e.g. '11.3%' (not accurate for Mix systems)
        'ratio2' -- % of 'Solar production' that is exported e.g. '88.7%' (not accurate for Mix systems)
        'ratio3' -- % of 'Load consumption' that is self consumption e.g. '49.8%' (not accurate for Mix systems)
        'ratio4' -- % of 'Load consumption' that is imported from the grid e.g '50.2%' (not accurate for Mix systems)
        'ratio5' -- % of Self consumption that is from batteries e.g. '92.1%' (not accurate for Mix systems)
        'ratio6' -- % of Self consumption that is directly from Solar e.g. '7.9%' (not accurate for Mix systems)

        NOTE: Does not return any data for a tlx system. Use plant_energy_data() instead.
        """
        date_str = self.__get_date_string(timespan, date)

        response = self.session.post(self.get_url('newPlantAPI.do'), params={
            'action': "getEnergyStorageData",
            'date': date_str,
            'type': timespan.value,
            'plantId': plant_id
        })

        return response.json()

    def plant_settings(self, plant_id):
        """
        Returns a dictionary containing the settings for the specified plant

        Keyword arguments:
        plant_id -- The id of the plant you want the settings of

        Returns:
        A python dictionary containing the settings for the specified plant
        """
        response = self.session.get(self.get_url('newPlantAPI.do'), params={
            'op': 'getPlant',
            'plantId': plant_id
        })
        
        return response.json()

    def storage_detail(self, storage_id):
        """
        Get "All parameters" from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageInfo_sacolar',
            'storageId': storage_id
        })

        return response.json()

    def storage_params(self, storage_id):
        """
        Get much more detail from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageParams_sacolar',
            'storageId': storage_id
        })

        return response.json()

    def storage_energy_overview(self, plant_id, storage_id):
        """
        Get some energy/generation overview data.
        """
        response = self.session.post(self.get_url('newStorageAPI.do?op=getEnergyOverviewData_sacolar'), params={
            'plantId': plant_id,
            'storageSn': storage_id
        })

        return response.json().get('obj', {})

    def inverter_list(self, plant_id):
        """
        Use device_list, it's more descriptive since the list contains more than inverters.
        """
        warnings.warn("This function may be deprecated in the future because naming is not correct, use device_list instead", DeprecationWarning)
        return self.device_list(plant_id)

    def __get_all_devices(self, plant_id):
        """
        Get basic plant information with device list.
        """
        response = self.session.get(self.get_url('newTwoPlantAPI.do'), 
                                     params={'op': 'getAllDeviceList',                                
                                             'plantId': plant_id,
                                             'language': 1})

        return response.json().get('deviceList', {})

    def device_list(self, plant_id):
        """
        Get a list of all devices connected to plant.
        """
        
        device_list = self.plant_info(plant_id).get('deviceList', [])
        
        if not device_list:
            # for tlx systems, the device_list in plant is empty, so use __get_all_devices() instead
            device_list = self.__get_all_devices(plant_id)

        return device_list

    def plant_info(self, plant_id):
        """
        Get basic plant information with device list.
        """
        response = self.session.get(self.get_url('newTwoPlantAPI.do'), params={
            'op': 'getAllDeviceListTwo',
            'plantId': plant_id,
            'pageNum': 1,
            'pageSize': 1
        })

        return response.json()

    def plant_energy_data(self, plant_id):
        """
        Get the energy data used in the 'Plant' tab in the phone
        """
        response = self.session.post(self.get_url('newTwoPlantAPI.do'), 
                                     params={'op': 'getUserCenterEnertyDataByPlantid'}, 
                                     data={ 'language': 1,
                                            'plantId': plant_id})

        return response.json()
    
    def is_plant_noah_system(self, plant_id):
        """
        Returns a dictionary containing if noah devices are configured for the specified plant

        Keyword arguments:
        plant_id -- The id of the plant you want the noah devices of (str)

        Returns
        'msg'
        'result'    -- True or False
        'obj'   -- An Object containing if noah devices are configured
            'isPlantNoahSystem' -- Is the specified plant a noah system (True or False)
            'plantId'   -- The ID of the plant
            'isPlantHaveNoah'   -- Are noah devices configured in the specified plant (True or False)
            'deviceSn'  -- Serial number of the configured noah device
            'plantName' -- Friendly name of the plant
        """
        response = self.session.post(self.get_url('noahDeviceApi/noah/isPlantNoahSystem'), data={
            'plantId': plant_id
        })
        return response.json()

    
    def noah_system_status(self, serial_number):
        """
        Returns a dictionary containing the status for the specified Noah Device

        Keyword arguments:
        serial_number -- The Serial number of the noah device you want the status of (str)

        Returns
        'msg'
        'result'    -- True or False
        'obj' -- An Object containing the noah device status
            'chargePower'   -- Battery charging rate in watt e.g. '200Watt'
            'workMode'  -- Workingmode of the battery (0 = Load First, 1 = Battery First)
            'soc'   -- Statement of charge (remaining battery %)
            'associatedInvSn'   -- ???
            'batteryNum'    -- Numbers of batterys
            'profitToday'   -- Today generated profit through noah device
            'plantId'   -- The ID of the plant
            'disChargePower'    -- Battery discharging rate in watt e.g. '200Watt'
            'eacTotal'  -- Total energy exported to the grid in kWh e.g. '20.5kWh'
            'eacToday'  -- Today energy exported to the grid in kWh e.g. '20.5kWh'
            'pac'   -- Export to grid rate in watt e.g. '200Watt'
            'ppv'   -- Solar generation in watt e.g. '200Watt'
            'alias' -- Friendly name of the noah device
            'profitTotal'   -- Total generated profit through noah device
            'moneyUnit' -- Unit of currency e.g. '€'
            'status'    -- Is the noah device online (True or False)
        """
        response = self.session.post(self.get_url('noahDeviceApi/noah/getSystemStatus'), data={
            'deviceSn': serial_number
        })
        return response.json()

    
    def noah_info(self, serial_number):
        """
        Returns a dictionary containing the informations for the specified Noah Device

        Keyword arguments:
        serial_number -- The Serial number of the noah device you want the informations of (str)

        Returns
        'msg'
        'result'    -- True or False
        'obj' -- An Object containing the noah device informations
            'neoList'   -- A List containing Objects
            'unitList'  -- A Object containing currency units e.g. "Euro": "euro", "DOLLAR": "dollar"
            'noah'  -- A Object containing the folowing
                'time_segment'  -- A List containing Objects with configured "Operation Mode"
                    NOTE: The keys are generated numerical, the values are generated with folowing syntax "[workingmode (0 = Load First, 1 = Battery First)]_[starttime]_[endtime]_[output power]"
                    'time_segment': {
                        'time_segment1': "0_0:0_8:0_150", ([Load First]_[00:00]_[08:00]_[150 watt])
                        'time_segment2': "1_8:0_18:0_0", ([Battery First]_[08:00]_[18:00]_[0 watt])
                        ....
                     }
                'batSns'    -- A List containing all battery Serial Numbers 
                'associatedInvSn'   -- ???
                'plantId'   -- The ID of the plant
                'chargingSocHighLimit'  -- Configured "Battery Management" charging upper limit
                'chargingSocLowLimit'   -- Configured "Battery Management" charging lower limit
                'defaultPower'  -- Configured "System Default Output Power"
                'version'   -- The Firmware Version of the noah device
                'deviceSn'  -- The Serial number of the noah device
                'formulaMoney'  -- Configured "Select Currency" energy cost per kWh e.g. '0.22'
                'alias' -- Friendly name of the noah device
                'model' -- Model Name of the noah device
                'plantName' -- Friendly name of the plant
                'tempType'  -- ???
                'moneyUnitText' -- Configured "Select Currency" (Value from the unitList) e.G. "euro"
            'plantList' -- A List containing Objects containing the folowing
                'plantId'   -- The ID of the plant
                'plantImgName'  -- Friendly name of the plant Image
                'plantName' -- Friendly name of the plant
        """        
        response = self.session.post(self.get_url('noahDeviceApi/noah/getNoahInfoBySn'), data={
            'deviceSn': serial_number
        })
        return response.json()


    def update_plant_settings(self, plant_id, changed_settings, current_settings = None):
        """
        Applies settings to the plant e.g. ID, Location, Timezone
        See README for all possible settings options

        Keyword arguments:
        plant_id -- The id of the plant you wish to update the settings for
        changed_settings -- A python dictionary containing the settings to be changed and their value
        current_settings -- A python dictionary containing the current settings of the plant (use the response from plant_settings), if None - fetched for you

        Returns:
        A response from the server stating whether the configuration was successful or not
        """
        #If no existing settings have been provided then get them from the growatt server
        if current_settings == None:
            current_settings = self.plant_settings(plant_id)

        #These are the parameters that the form requires, without these an error is thrown. Pre-populate their values with the current values
        form_settings = {
            'plantCoal': (None, str(current_settings['formulaCoal'])),
            'plantSo2': (None, str(current_settings['formulaSo2'])),
            'accountName': (None, str(current_settings['userAccount'])),
            'plantID': (None, str(current_settings['id'])),
            'plantFirm': (None, '0'), #Hardcoded to 0 as I can't work out what value it should have
            'plantCountry': (None, str(current_settings['country'])),
            'plantType': (None, str(current_settings['plantType'])),
            'plantIncome': (None, str(current_settings['formulaMoneyStr'])),
            'plantAddress': (None, str(current_settings['plantAddress'])),
            'plantTimezone': (None, str(current_settings['timezone'])),
            'plantLng': (None, str(current_settings['plant_lng'])),
            'plantCity': (None, str(current_settings['city'])),
            'plantCo2': (None, str(current_settings['formulaCo2'])),
            'plantMoney': (None, str(current_settings['formulaMoneyUnitId'])),
            'plantPower': (None, str(current_settings['nominalPower'])),
            'plantLat': (None, str(current_settings['plant_lat'])),
            'plantDate': (None, str(current_settings['createDateText'])),
            'plantName': (None, str(current_settings['plantName'])),
        }

        #Overwrite the current value of the setting with the new value
        for setting, value in changed_settings.items():
            form_settings[setting] = (None, str(value))

        response = self.session.post(self.get_url('newTwoPlantAPI.do?op=updatePlant'), files = form_settings)

        return response.json()

    def update_inverter_setting(self, serial_number, setting_type, 
                                default_parameters, parameters):
        """
        Applies settings for specified system based on serial number
        See README for known working settings

        Arguments:
        serial_number -- Serial number (device_sn) of the inverter (str)
        setting_type -- Setting to be configured (str)
        default_params -- Default set of parameters for the setting call (dict)
        parameters -- Parameters to be sent to the system (dict or list of str)
                (array which will be converted to a dictionary)

        Returns:
        JSON response from the server whether the configuration was successful
        """
        settings_parameters = parameters
        
        #If we've been passed an array then convert it into a dictionary
        if isinstance(parameters, list):
            settings_parameters = {}
            for index, param in enumerate(parameters, start=1):
                settings_parameters['param' + str(index)] = param
        
        settings_parameters = {**default_parameters, **settings_parameters}

        response = self.session.post(self.get_url('newTcpsetAPI.do'), 
                                     params=settings_parameters)
        
        return response.json()

    def update_mix_inverter_setting(self, serial_number, setting_type, parameters):
        """
        Alias for setting inverter parameters on a mix inverter
        See README for known working settings

        Arguments:
        serial_number -- Serial number (device_sn) of the inverter (str)
        setting_type -- Setting to be configured (str)
        parameters -- Parameters to be sent to the system (dict or list of str)
                (array which will be converted to a dictionary)

        Returns:
        JSON response from the server whether the configuration was successful
        """
        default_parameters = {
            'op': 'mixSetApiNew',
            'serialNum': serial_number,
            'type': setting_type
        }
        return self.update_inverter_setting(serial_number, setting_type, 
                                            default_parameters, parameters)

    def update_ac_inverter_setting(self, serial_number, setting_type, parameters):
        """
        Alias for setting inverter parameters on an AC-coupled inverter
        See README for known working settings

        Arguments:
        serial_number -- Serial number (device_sn) of the inverter (str)
        setting_type -- Setting to be configured (str)
        parameters -- Parameters to be sent to the system (dict or list of str)
                (array which will be converted to a dictionary)

        Returns:
        JSON response from the server whether the configuration was successful
        """
        default_parameters = {
            'op': 'spaSetApi',
            'serialNum': serial_number,
            'type': setting_type
        }
        return self.update_inverter_setting(serial_number, setting_type, 
                                            default_parameters, parameters)

    def update_tlx_inverter_time_segment(self, serial_number, segment_id, batt_mode, start_time, end_time, enabled):
        """
        Updates the time segment settings for a TLX hybrid inverter.

        Arguments:
        serial_number -- Serial number (device_sn) of the inverter (str)
        segment_id -- ID of the time segment to be updated (int)
        batt_mode -- Battery mode (int)
        start_time -- Start time of the segment (datetime.time)
        end_time -- End time of the segment (datetime.time)
        enabled -- Whether the segment is enabled (bool)

        Returns:
        JSON response from the server whether the configuration was successful
        """
        params = {
            'op': 'tlxSet'
        }
        data = {
            'serialNum': serial_number,
            'type': f'time_segment{segment_id}',
            'param1': batt_mode,
            'param2': start_time.strftime('%H'),
            'param3': start_time.strftime('%M'),
            'param4': end_time.strftime('%H'),
            'param5': end_time.strftime('%M'),
            'param6': '1' if enabled else '0'
        }
        
        response = self.session.post(self.get_url('newTcpsetAPI.do'), params=params, data=data)
        result = response.json()
        
        if not result.get('success', False):
            raise Exception(f"Failed to update TLX inverter time segment: {result.get('msg', 'Unknown error')}")
        
        return result

    def update_tlx_inverter_setting(self, serial_number, setting_type, parameter):
        """
        Alias for setting parameters on a tlx hybrid inverter
        See README for known working settings

        Arguments:
        serial_number -- Serial number (device_sn) of the inverter (str)
        setting_type -- Setting to be configured (str)
        parameter -- Parameter(s) to be sent to the system (str, dict, list of str)
                (array which will be converted to a dictionary)

        Returns:
        JSON response from the server whether the configuration was successful
        """
        default_parameters = {
            'op': 'tlxSet',
            'serialNum': serial_number,
            'type': setting_type
        }

        # If parameter is a single value, convert it to a dictionary
        if not isinstance(parameter, (dict, list)):
            parameter = {'param1': parameter}
        elif isinstance(parameter, list):
            parameter = {f'param{index+1}': param for index, param in enumerate(parameter)}

        return self.update_inverter_setting(serial_number, setting_type, 
                                            default_parameters, parameter)


    def update_noah_settings(self, serial_number, setting_type, parameters):
        """
        Applies settings for specified noah device based on serial number
        See README for known working settings

        Arguments:
        serial_number -- Serial number (device_sn) of the noah (str)
        setting_type -- Setting to be configured (str)
        parameters -- Parameters to be sent to the system (dict or list of str)
                (array which will be converted to a dictionary)

        Returns:
        JSON response from the server whether the configuration was successful
        """
        default_parameters = {
            'serialNum': serial_number,
            'type': setting_type
        }
        settings_parameters = parameters
        
        #If we've been passed an array then convert it into a dictionary
        if isinstance(parameters, list):
            settings_parameters = {}
            for index, param in enumerate(parameters, start=1):
                settings_parameters['param' + str(index)] = param
        
        settings_parameters = {**default_parameters, **settings_parameters}

        response = self.session.post(self.get_url('noahDeviceApi/noah/set'), 
                                     data=settings_parameters)
        
        return response.json()


    def plant_list_v1(self):
        """
        Get a list of all plants with detailed information.

        Returns:
            list: A list of plants with detailed information.
        """
        response = self.session.get(
            url=self.get_v1_url('plant/list'),
            data={
                'page': '',
                'perpage': '',
                'search_type': '',
                'search_keyword': ''
            }
        )

        return response.json()

    def plant_details_v1(self, plant_id):
        """
        Get basic information about a power station.
        
        Args:
            plant_id (int): Power Station ID
            
        Returns:
            dict: A dictionary containing the plant details.
            
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return {"error_code": 1, "error_msg": "API token required", "data": None}
            
        response = self.session.get(
            self.get_v1_url('plant/details'),
            params={'plant_id': plant_id}
        )
        
        return response.json()
        
    def plant_energy_overview_v1(self, plant_id):
        """
        Get an overview of a plant's energy data.
        
        Args:
            plant_id (int): Power Station ID
            
        Returns:
            dict: A dictionary containing the plant energy overview.
            
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return {"error_code": 1, "error_msg": "API token required", "data": None}
            
        response = self.session.get(
            self.get_v1_url('plant/data'),
            params={'plant_id': plant_id}
        )
        
        return response.json()
        
    def plant_energy_history_v1(self, plant_id, start_date=None, end_date=None, time_unit="day", page=None, perpage=None):
        """
        Retrieve plant energy data for multiple days/months/years.
        
        Args:
            plant_id (int): Power Station ID
            start_date (date, optional): Start Date - defaults to today
            end_date (date, optional): End Date - defaults to today
            time_unit (str, optional): Time unit ('day', 'month', 'year') - defaults to 'day'
            page (int, optional): Page number - defaults to 1
            perpage (int, optional): Number of items per page - defaults to 20, max 100
            
        Returns:
            dict: A dictionary containing the plant energy history.
            
        Notes:
            - When time_unit is 'day', date interval cannot exceed 7 days
            - When time_unit is 'month', start date must be within same or previous year
            - When time_unit is 'year', date interval must not exceed 20 years
            
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return {"error_code": 1, "error_msg": "API token required", "data": None}
            
        if start_date is None and end_date is None:
            start_date = date.today()
            end_date = date.today()
        elif start_date is None:
            start_date = end_date
        elif end_date is None:
            end_date = start_date
            
        # Validate date ranges based on time_unit
        if time_unit == "day" and (end_date - start_date).days > 7:
            warnings.warn("Date interval must not exceed 7 days in 'day' mode.", RuntimeWarning)
        elif time_unit == "month" and (end_date.year - start_date.year > 1):
            warnings.warn("Start date must be within same or previous year in 'month' mode.", RuntimeWarning)
        elif time_unit == "year" and (end_date.year - start_date.year > 20):
            warnings.warn("Date interval must not exceed 20 years in 'year' mode.", RuntimeWarning)
        
        response = self.session.get(
            self.get_v1_url('plant/energy'),
            params={
                'plant_id': plant_id,
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date.strftime("%Y-%m-%d"),
                'time_unit': time_unit,
                'page': page,
                'perpage': perpage
            }
        )
        
        return response.json()

    def device_list_v1(self, plant_id):
        """
        Get devices associated with plant.
        
        Note:
            returned "device_type" mappings:
             1: inverter (including MAX)
             2: storage
             3: other
             4: max (single MAX)
             5: sph
             6: spa
             7: min (including TLX)
             8: pcs
             9: hps
            10: pbd

        Args:
            plant_id (int): Power Station ID

        Returns:
            DeviceList
            e.g.
            {
                "data": {
                    "count": 3,
                    "devices": [
                        {
                            "device_sn": "ZT00100001",
                            "last_update_time": "2018-12-13 11:03:52",
                            "model": "A0B0D0T0PFU1M3S4",
                            "lost": True,
                            "status": 0,
                            "manufacturer": "Growatt",
                            "device_id": 116,
                            "datalogger_sn": "CRAZT00001",
                            "type": 1
                        },
                    ]
                },
                "error_code": 0,
                "error_msg": ""
            }
        """
        response = self.session.get(
            url=self.get_v1_url("device/list"),
            params={
                "plant_id": plant_id,
                "page": "",
                "perpage": "",
            },
        )
        return response.json()


    def min_detail(self, device_sn):
        """
        Get detailed data for a MIN inverter.

        Args:
            device_sn (str): The serial number of the MIN inverter.

        Returns:
            dict: A dictionary containing the MIN inverter details.

        Raises:
            Exception: If the request to the server fails.
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return {"error_code": 1, "error_msg": "API token required", "data": None}
            
        response = self.session.get(
            self.get_v1_url('device/tlx/tlx_data_info'), 
            params={
                'device_sn': device_sn
            }
        )

        return response.json()

    def min_energy(self, device_sn):
        """
        Get energy data for a MIN inverter.

        Args:
            device_sn (str): The serial number of the MIN inverter.

        Returns:
            dict: A dictionary containing the MIN inverter energy data.

        Raises:
            Exception: If the request to the server fails.
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return {"error_code": 1, "error_msg": "API token required", "data": None}
            
        response = self.session.post(
            url=self.get_v1_url("device/tlx/tlx_last_data"),
            data={
                "tlx_sn": device_sn,
            },
        )

        return response.json()

    def min_energy_history(self, device_sn, start_date=None, end_date=None, timezone=None, page=None, limit=None):
        """
        Get MIN inverter data history.

        Args:
            device_sn (str): The ID of the MIN inverter.
            start_date (date, optional): Start date. Defaults to today.
            end_date (date, optional): End date. Defaults to today.
            timezone (str, optional): Timezone ID.
            page (int, optional): Page number.
            limit (int, optional): Results per page.

        Returns:
            dict: A dictionary containing the MIN inverter history data.

        Raises:
            Exception: If the request to the server fails.
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return {"error_code": 1, "error_msg": "API token required", "data": None}

        if start_date is None and end_date is None:
            start_date = date.today()
            end_date = date.today()
        elif start_date is None:
            start_date = end_date
        elif end_date is None:
            end_date = start_date

        # check interval validity
        if end_date - start_date > timedelta(days=7):
            raise ValueError("date interval must not exceed 7 days")
                
        response = self.session.post(
            url=self.get_v1_url('device/tlx/tlx_data'), 
            data={
                "tlx_sn": device_sn,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone_id": timezone,
                "page": page,
                "perpage": limit,
            }
        )

        return response.json()

    def min_settings(self, device_sn):
        """
        Get settings for a MIN inverter.

        Args:
            device_sn (str): The serial number of the MIN inverter.

        Returns:
            dict: A dictionary containing the MIN inverter settings.

        Raises:
            Exception: If the request to the server fails.
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return {"error_code": 1, "error_msg": "API token required", "data": None}
            
        response = self.session.get(
            self.get_v1_url('device/tlx/tlx_set_info'), 
            params={
                'device_sn': device_sn
            }
        )

        return response.json()

    def min_read_parameter(self, device_sn, parameter_id, start_address=None, end_address=None):
        """
        Read setting from MIN inverter.

        Args:
            device_sn (str): The ID of the TLX inverter.
            parameter_id (str): Parameter ID to read. Don't use start_address and end_address if this is set.
            start_address (int, optional): Register start address (for set_any_reg). Don't use parameter_id if this is set.
            end_address (int, optional): Register end address (for set_any_reg). Don't use parameter_id if this is set.

        Returns:
            dict: A dictionary containing the setting value.

        Raises:
            Exception: If the request to the server fails.
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return None

        if parameter_id is None and start_address is None:
            raise ValueError("specify either parameter_id or start_address/end_address")
        elif parameter_id is not None and start_address is not None:
            raise ValueError(
                "specify either parameter_id or start_address/end_address - not both."
            )
        elif parameter_id is not None:
            # named parameter
            start_address = 0
            end_address = 0
        else:
            # using register-number mode
            parameter_id = "set_any_reg"
            if start_address is None:
                start_address = end_address
            if end_address is None:
                end_address = start_address
                            

        response = self.session.post(
            self.get_v1_url('readMinParam'), 
            data = {
                "device_sn": device_sn,
                "paramId": parameter_id,
                "startAddr": start_address,
                "endAddr": end_address,
            }
        )

        return response.json()

    def min_write_parameter(self, device_sn, parameter_id, parameter_values=None):
        """
        Set parameters on a MIN inverter.
        
        Args:
            device_sn (str): Serial number of the inverter
            parameter_id (str): Setting type to be configured
            parameter_values: Parameter values to be sent to the system.
                Can be a single string (for param1 only),
                a list of strings (for sequential params),
                or a dictionary mapping param positions to values
        
        Returns:
            dict: JSON response from the server
            
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return {"error_code": 1, "error_msg": "API token required", "data": None}
            
        # Initialize all parameters as empty strings
        parameters = {i: "" for i in range(1, 20)}
        
        # Process parameter values based on type
        if parameter_values is not None:
            if isinstance(parameter_values, (str, int, float, bool)):
                # Single value goes to param1
                parameters[1] = str(parameter_values)
            elif isinstance(parameter_values, list):
                # List of values go to sequential params
                for i, value in enumerate(parameter_values, 1):
                    if i <= 19:  # Only use up to 19 parameters
                        parameters[i] = str(value)
            elif isinstance(parameter_values, dict):
                # Dict maps param positions to values
                for pos, value in parameter_values.items():
                    pos = int(pos) if not isinstance(pos, int) else pos
                    if 1 <= pos <= 19:  # Validate parameter positions
                        parameters[pos] = str(value)
        
        # IMPORTANT: Create a data dictionary with ALL parameters explicitly included
        request_data = {
            "tlx_sn": device_sn,
            "type": parameter_id
        }
        
        # Add all 19 parameters to the request
        for i in range(1, 20):
            request_data[f"param{i}"] = str(parameters[i])
        
        # Send the request
        response = self.session.post(
            self.get_v1_url('tlxSet'), 
            data=request_data
        )
        
        return response.json()

    def min_write_time_segment(self, device_sn, segment_id, batt_mode, start_time, end_time, enabled=True):
        """
        Set a time segment for a MIN inverter.
        
        Args:
            device_sn (str): The serial number of the inverter.
            segment_id (int): Time segment ID (1-9).
            batt_mode (int): 0=load priority, 1=battery priority, 2=grid priority.
            start_time (datetime.time): Start time for the segment.
            end_time (datetime.time): End time for the segment.
            enabled (bool): Whether this segment is enabled.
                
        Returns:
            dict: The server response.
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return {"error_code": 1, "error_msg": "API token required", "data": None}
        
        if not 1 <= segment_id <= 9:
            raise ValueError("segment_id must be between 1 and 9")
                
        if not 0 <= batt_mode <= 2:
            raise ValueError("batt_mode must be between 0 and 2")
        
        # Initialize ALL 19 parameters as empty strings, not just the ones we need
        all_params = {
            "tlx_sn": device_sn,
            "type": f"time_segment{segment_id}"
        }
        
        # Add param1 through param19, setting the values we need
        all_params["param1"] = str(batt_mode)
        all_params["param2"] = str(start_time.hour)
        all_params["param3"] = str(start_time.minute)
        all_params["param4"] = str(end_time.hour)
        all_params["param5"] = str(end_time.minute)
        all_params["param6"] = "1" if enabled else "0"
        
        # Add empty strings for all unused parameters
        for i in range(7, 20):
            all_params[f"param{i}"] = ""
        
        # Send the request
        response = self.session.post(
            self.get_v1_url('tlxSet'), 
            data=all_params
        )
        
        return response.json()

    def min_read_time_segments(self, device_sn, settings_data=None):
        """
        Read Time-of-Use (TOU) settings from a Growatt MIN/TLX inverter.
        
        Retrieves all 9 time segments from a Growatt MIN/TLX inverter and
        parses them into a structured format.
        
        Args:
            device_sn (str): The device serial number of the inverter
            settings_data (dict, optional): Settings data from min_settings call to avoid repeated API calls.
                                        Can be either the complete response or just the data portion.
            
        Returns:
            list: A list of dictionaries, each containing details for one time segment:
                - segment_id (int): The segment number (1-9)
                - batt_mode (int): 0=Load First, 1=Battery First, 2=Grid First
                - mode_name (str): String representation of the mode
                - start_time (str): Start time in format "HH:MM"
                - end_time (str): End time in format "HH:MM"
                - enabled (bool): Whether the segment is enabled
                
        Example:
            api = GrowattApi(token="your_api_token")
            
            # Option 1: Make a single call
            tou_settings = api.min_read_tou_settings("DEVICE_SERIAL_NUMBER")
            
            # Option 2: Reuse existing settings data
            settings_response = api.min_settings("DEVICE_SERIAL_NUMBER")
            tou_settings = api.min_read_tou_settings("DEVICE_SERIAL_NUMBER", settings_response)
            
        """
        if not self.v1_api_enabled:
            warnings.warn("V1 API is not enabled. This method requires an API token.", RuntimeWarning)
            return []
        
        # Process the settings data
        if settings_data is None:
            # Fetch settings if not provided
            settings_response = self.min_settings(device_sn=device_sn)
            if settings_response.get('error_code', 1) != 0:
                print(f"Failed to get settings, error: {settings_response.get('error_msg', 'Unknown error')}")
                return []
            settings_data = settings_response.get('data', {})
        else:
            # Check if we were given the full API response or just the data portion
            if 'error_code' in settings_data and 'data' in settings_data:
                # This is the full API response
                if settings_data['error_code'] != 0:
                    print(f"Settings data contains an error: {settings_data.get('error_msg', 'Unknown error')}")
                    return []
                settings_data = settings_data.get('data', {})
            # If it's just the data portion, use it directly (nothing to do)
        
        # Define mode names
        mode_names = {
            0: "Load First",
            1: "Battery First",
            2: "Grid First"
        }
        
        segments = []
        
        # Process each time segment
        for i in range(1, 10):  # Segments 1-9
            # Get raw time values
            start_time_raw = settings_data.get(f'forcedTimeStart{i}', "0:0")
            end_time_raw = settings_data.get(f'forcedTimeStop{i}', "0:0")
            
            # Handle 'null' string values
            if start_time_raw == 'null' or not start_time_raw:
                start_time_raw = "0:0"
            if end_time_raw == 'null' or not end_time_raw:
                end_time_raw = "0:0"
            
            # Format times with leading zeros (HH:MM)
            try:
                start_parts = start_time_raw.split(":")
                start_hour = int(start_parts[0])
                start_min = int(start_parts[1])
                start_time = f"{start_hour:02d}:{start_min:02d}"
            except (ValueError, IndexError):
                start_time = "00:00"
                
            try:
                end_parts = end_time_raw.split(":")
                end_hour = int(end_parts[0])
                end_min = int(end_parts[1])
                end_time = f"{end_hour:02d}:{end_min:02d}"
            except (ValueError, IndexError):
                end_time = "00:00"
            
            # Get the mode value safely
            mode_raw = settings_data.get(f'time{i}Mode')
            if mode_raw == 'null' or mode_raw is None:
                batt_mode = None
            else:
                try:
                    batt_mode = int(mode_raw)
                except (ValueError, TypeError):
                    batt_mode = None
            
            # Get the enabled status safely
            enabled_raw = settings_data.get(f'forcedStopSwitch{i}', 0)
            if enabled_raw == 'null' or enabled_raw is None:
                enabled = False
            else:
                try:
                    enabled = int(enabled_raw) == 1
                except (ValueError, TypeError):
                    enabled = False
            
            segment = {
                'segment_id': i,
                'batt_mode': batt_mode,
                'mode_name': mode_names.get(batt_mode, "Unknown"),
                'start_time': start_time,
                'end_time': end_time,
                'enabled': enabled
            }
            
            segments.append(segment)
        
        return segments