name = "growattServer"

import datetime
from enum import IntEnum
import hashlib
import json
import requests
import warnings

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
    server_url = 'https://server.growatt.com/'

    def __init__(self):
        self.session = requests.Session()

    def get_url(self, page):
        """
        Simple helper function to get the page url/
        """
        return self.server_url + page

    def login(self, username, password):
        """
        Log the user in.
        """
        password_md5 = hash_password(password)
        response = self.session.post(self.get_url('LoginAPI.do'), data={
            'userName': username,
            'password': password_md5
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_list(self, user_id):
        """
        Get a list of plants connected to this account.
        """
        response = self.session.get(self.get_url('PlantListAPI.do'),
                                    params={'userId': user_id},
                                    allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError("Request failed: %s", response)
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_detail(self, plant_id, timespan, date):
        """
        Get plant details for specified timespan.
        """
        assert timespan in Timespan
        if timespan == Timespan.day:
            date_str = date.strftime('%Y-%m-%d')
        elif timespan == Timespan.month:
            date_str = date.strftime('%Y-%m')

        response = self.session.get(self.get_url('PlantDetailAPI.do'), params={
            'plantId': plant_id,
            'type': timespan.value,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def inverter_data(self, inverter_id, date):
        """
        Get inverter data for specified date or today.
        """
        if date is None:
            date = datetime.date.today()
        date_str = date.strftime('%Y-%m-%d')
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterData',
            'id': inverter_id,
            'type': 1,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data

    def inverter_detail(self, inverter_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData',
            'inverterId': inverter_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def inverter_detail_two(self, inverter_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData_two',
            'inverterId': inverter_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def tlx_data(self, tlx_id, date):
        """
        Get inverter data for specified date or today.
        """
        if date is None:
            date = datetime.date.today()
        date_str = date.strftime('%Y-%m-%d')
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxData',
            'id': tlx_id,
            'type': 1,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data

    def tlx_detail(self, tlx_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxDetailData',
            'id': tlx_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

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

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

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

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

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

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def mix_detail(self, mix_id, plant_id, timespan=Timespan.hour, date=datetime.datetime.now()):
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
        assert timespan in Timespan
        if timespan == Timespan.day or timespan == Timespan.hour:
            date_str = date.strftime('%Y-%m-%d')
        elif timespan == Timespan.month:
            date_str = date.strftime('%Y-%m')

        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getEnergyProdAndCons_KW',
            'plantId': plant_id,
            'mixId': mix_id,
            'type': timespan.value,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))

        #Some of the 'totals' values that are returned by this function do not align to what we would expect, however the graph data always seems to be accurate.
        #Therefore, here we take a moment to calculate the same values provided elsewhere but based on the graph data instead
        #The particular stats that we question are 'load consumption' (elocalLoad)  and 'import from grid' (etouser) which seem to be calculated from one-another
        #It would appear that 'etouser' is calculated on the backend incorrectly for systems that use AC battery charged (e.g. during cheap nighttime rates)
        if timespan == Timespan.hour or timespan == Timespan.day:
          pacToGridToday = 0.0
          pacToUserToday = 0.0
          pdischargeToday = 0.0
          ppvToday = 0.0
          sysOutToday = 0.0

          chartData = data['obj']['chartData']
          for time_entry in chartData:
            #For each time entry convert it's wattage into kWh, this assumes that the wattage value is
            #the same for the whole 5 minute window (it's the only assumption we can make)
            #We Multiply the wattage by 5/60 (the number of minutes of the time window divided by the number of minutes in an hour)
            #to give us the equivalent kWh reading for that 5 minute window
            pacToGridToday += float(chartData[time_entry]['pacToGrid']) * (5/60)
            pacToUserToday += float(chartData[time_entry]['pacToUser']) * (5/60)
            pdischargeToday += float(chartData[time_entry]['pdischarge']) * (5/60)
            ppvToday += float(chartData[time_entry]['ppv']) * (5/60)
            sysOutToday += float(chartData[time_entry]['sysOut']) * (5/60)

          data['obj']['calculatedPacToGridTodayKwh'] = round(pacToGridToday,2)
          data['obj']['calculatedPacToUserTodayKwh'] = round(pacToUserToday,2)
          data['obj']['calculatedPdischargeTodayKwh'] = round(pdischargeToday,2)
          data['obj']['calculatedPpvTodayKwh'] = round(ppvToday,2)
          data['obj']['calculatedSysOutTodayKwh'] = round(sysOutToday,2)

        return data['obj']

    def storage_detail(self, storage_id):
        """
        Get "All parameters" from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageInfo_sacolar',
            'storageId': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_params(self, storage_id):
        """
        Get much more detail from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageParams_sacolar',
            'storageId': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_energy_overview(self, plant_id, storage_id):
        """
        Get some energy/generation overview data.
        """
        response = self.session.post(self.get_url('newStorageAPI.do?op=getEnergyOverviewData_sacolar'), params={
            'plantId': plant_id,
            'storageSn': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def inverter_list(self, plant_id):
        """
        Use device_list, it's more descriptive since the list contains more than inverters.
        """
        warnings.warn("This function may be deprecated in the future because naming is not correct, use device_list instead", DeprecationWarning)
        return self.device_list(plant_id)

    def device_list(self, plant_id):
        """
        Get a list of all devices connected to plant.
        """
        return self.plant_info(plant_id)['deviceList']

    def plant_info(self, plant_id):
        """
        Get basic plant information with device list.
        """
        response = self.session.get(self.get_url('newTwoPlantAPI.do'), params={
            'op': 'getAllDeviceList',
            'plantId': plant_id,
            'pageNum': 1,
            'pageSize': 1
        })

        data = json.loads(response.content.decode('utf-8'))
        return data
