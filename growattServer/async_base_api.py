"""Async Growatt API client using httpx."""

from __future__ import annotations

import datetime
import json
import re
import secrets
import warnings
from typing import TYPE_CHECKING, Any

import httpx

from .base_api import Timespan, hash_password
from .exceptions import GrowattError

if TYPE_CHECKING:
    from typing import Self

name = "growattServer"


async def _raise_for_status(response: httpx.Response) -> None:
    response.raise_for_status()


class AsyncGrowattApi:
    """Async client for Growatt API endpoints using httpx."""

    server_url = "https://openapi.growatt.com/"
    agent_identifier = "Dalvik/2.1.0 (Linux; U; Android 12; https://github.com/indykoning/PyPi_GrowattServer)"

    def __init__(self, add_random_user_id: bool = False, agent_identifier: str | None = None, session: httpx.AsyncClient | None = None) -> None:
        """
        Initialize the async Growatt API client.

        Args:
            add_random_user_id: Append a short random suffix to the user-agent.
            agent_identifier: Optional override for the user-agent string.
            session: Optional httpx.AsyncClient to reuse.

        """
        if agent_identifier is not None:
            self.agent_identifier = agent_identifier

        if add_random_user_id:
            random_number = "".join(str(secrets.randbelow(10)) for _ in range(5))
            self.agent_identifier += " - " + random_number

        if session is not None:
            self.session = session
            self._owns_session = False
        else:
            self.session = httpx.AsyncClient(
                headers={"User-Agent": self.agent_identifier},
                follow_redirects=True,
                timeout=None,  # noqa: S113
                event_hooks={"response": [_raise_for_status]},
            )
            self._owns_session = True

    async def aclose(self) -> None:
        """Close the underlying HTTP session if we own it."""
        if self._owns_session:
            await self.session.aclose()

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit the async context manager."""
        await self.aclose()

    def __get_date_string(self, timespan: Timespan | None = None, date: datetime.datetime | None = None) -> str:
        if timespan is not None and not isinstance(timespan, Timespan):
            raise ValueError("timespan must be a Timespan enum value")

        if date is None:
            date = datetime.datetime.now(datetime.UTC)

        date_str = ""
        if timespan == Timespan.month:
            date_str = date.strftime("%Y-%m")
        else:
            date_str = date.strftime("%Y-%m-%d")

        return date_str

    def get_url(self, page: str) -> str:
        """Return the page URL."""
        return self.server_url + page

    async def login(self, username: str, password: str, is_password_hashed: bool = False) -> dict[str, Any]:
        """
        Log the user in.

        Returns
        -------
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

        response = await self.session.post(self.get_url("newTwoLoginAPI.do"), data={
            "userName": username,
            "password": password
        })

        data = response.json()["back"]
        if data["success"]:
            data.update({
                "userId": data["user"]["id"],
                "userLevel": data["user"]["rightlevel"]
            })
        return data

    async def plant_list(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get a list of plants connected to this account.

        Args:
            user_id (str): The ID of the user.

        Returns:
            list: A list of plants connected to the account.

        Raises:
            httpx.HTTPError: If the request to the server fails.

        """
        response = await self.session.get(
            self.get_url("PlantListAPI.do"),
            params={"userId": user_id},
            follow_redirects=False
        )

        return response.json().get("back", [])

    async def plant_detail(self, plant_id: str, timespan: Timespan, date: datetime.datetime | None = None) -> dict[str, Any]:
        """
        Get plant details for specified timespan.

        Args:
            plant_id (str): The ID of the plant.
            timespan (Timespan): The ENUM value conforming to the time window you want e.g. hours from today, days, or months.
            date (datetime, optional): The date you are interested in. Defaults to datetime.datetime.now().

        Returns:
            dict: A dictionary containing the plant details.

        Raises:
            httpx.HTTPError: If the request to the server fails.

        """
        date_str = self.__get_date_string(timespan, date)

        response = await self.session.get(self.get_url("PlantDetailAPI.do"), params={
            "plantId": plant_id,
            "type": timespan.value,
            "date": date_str
        })

        return response.json().get("back", {})

    async def plant_list_two(self) -> list[dict[str, Any]]:
        """
        Get a list of all plants with detailed information.

        Returns:
            list: A list of plants with detailed information.

        """
        response = await self.session.post(
            self.get_url("newTwoPlantAPI.do"),
            params={"op": "getAllPlantListTwo"},
            data={
                "language": "1",
                "nominalPower": "",
                "order": "1",
                "pageSize": "15",
                "plantName": "",
                "plantStatus": "",
                "toPageNum": "1"
            }
        )

        return response.json().get("PlantList", [])

    async def inverter_data(self, inverter_id: str, date: datetime.datetime | None = None) -> dict[str, Any]:
        """
        Get inverter data for specified date or today.

        Args:
            inverter_id (str): The ID of the inverter.
            date (datetime, optional): The date you are interested in. Defaults to datetime.datetime.now().

        Returns:
            dict: A dictionary containing the inverter data.

        Raises:
            httpx.HTTPError: If the request to the server fails.

        """
        date_str = self.__get_date_string(date=date)
        response = await self.session.get(self.get_url("newInverterAPI.do"), params={
            "op": "getInverterData",
            "id": inverter_id,
            "type": 1,
            "date": date_str
        })

        return response.json()

    async def inverter_detail(self, inverter_id: str) -> dict[str, Any]:
        """
        Get detailed data from PV inverter.

        Args:
            inverter_id (str): The ID of the inverter.

        Returns:
            dict: A dictionary containing the inverter details.

        Raises:
            httpx.HTTPError: If the request to the server fails.

        """
        response = await self.session.get(self.get_url("newInverterAPI.do"), params={
            "op": "getInverterDetailData",
            "inverterId": inverter_id
        })

        return response.json()

    async def inverter_detail_two(self, inverter_id: str) -> dict[str, Any]:
        """
        Get detailed data from PV inverter (alternative endpoint).

        Args:
            inverter_id (str): The ID of the inverter.

        Returns:
            dict: A dictionary containing the inverter details.

        Raises:
            httpx.HTTPError: If the request to the server fails.

        """
        response = await self.session.get(self.get_url("newInverterAPI.do"), params={
            "op": "getInverterDetailData_two",
            "inverterId": inverter_id
        })

        return response.json()

    async def tlx_system_status(self, plant_id: str, tlx_id: str) -> dict[str, Any]:
        """Get status of the system."""
        response = await self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getSystemStatus_KW"},
            data={"plantId": plant_id, "id": tlx_id}
        )
        return response.json().get("obj", {})

    async def tlx_energy_overview(self, plant_id: str, tlx_id: str) -> dict[str, Any]:
        """Get energy overview."""
        response = await self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getEnergyOverview"},
            data={"plantId": plant_id, "id": tlx_id}
        )
        return response.json().get("obj", {})

    async def tlx_energy_prod_cons(self, plant_id: str, tlx_id: str, timespan: Timespan = Timespan.hour, date: datetime.datetime | None = None) -> dict[str, Any]:
        """Get energy production and consumption (kW)."""
        date_str = self.__get_date_string(timespan, date)
        response = await self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getEnergyProdAndCons_KW"},
            data={"date": date_str, "plantId": plant_id, "language": "1",
                  "id": tlx_id, "type": timespan.value}
        )
        return response.json().get("obj", {})

    async def tlx_data(self, tlx_id: str, date: datetime.datetime | None = None) -> dict[str, Any]:
        """Get TLX inverter data for specified date or today."""
        date_str = self.__get_date_string(date=date)
        response = await self.session.get(self.get_url("newTlxApi.do"), params={
            "op": "getTlxData", "id": tlx_id, "type": 1, "date": date_str
        })
        return response.json()

    async def tlx_detail(self, tlx_id: str) -> dict[str, Any]:
        """Get detailed data from TLX inverter."""
        response = await self.session.get(self.get_url("newTlxApi.do"), params={
            "op": "getTlxDetailData", "id": tlx_id
        })
        return response.json()

    async def tlx_params(self, tlx_id: str) -> dict[str, Any]:
        """Get parameters for TLX inverter."""
        response = await self.session.get(self.get_url("newTlxApi.do"), params={
            "op": "getTlxParams", "id": tlx_id
        })
        return response.json()

    async def tlx_all_settings(self, tlx_id: str) -> dict[str, Any] | None:
        """Get all possible settings from TLX inverter."""
        response = await self.session.post(self.get_url("newTlxApi.do"), params={
            "op": "getTlxSetData"
        }, data={"serialNum": tlx_id})
        return response.json().get("obj", {}).get("tlxSetBean")

    async def tlx_enabled_settings(self, tlx_id: str) -> dict[str, Any]:
        """Get "Enabled settings" from TLX inverter."""
        string_time = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
        response = await self.session.post(
            self.get_url("newLoginAPI.do"),
            params={"op": "getSetPass"},
            data={"deviceSn": tlx_id, "stringTime": string_time, "type": "5"}
        )
        return response.json().get("obj", {})

    async def tlx_battery_info(self, serial_num: str) -> dict[str, Any]:
        """Get battery information."""
        response = await self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getBatInfo"},
            data={"lan": 1, "serialNum": serial_num}
        )
        return response.json().get("obj", {})

    async def tlx_battery_info_detailed(self, plant_id: str, serial_num: str) -> dict[str, Any]:
        """Get detailed battery information."""
        response = await self.session.post(
            self.get_url("newTlxApi.do"),
            params={"op": "getBatDetailData"},
            data={"lan": 1, "plantId": plant_id, "id": serial_num}
        )
        return response.json()

    async def mix_info(self, mix_id: str, plant_id: str | None = None) -> dict[str, Any]:
        """Get high-level values from a Mix device."""
        request_params = {"op": "getMixInfo", "mixId": mix_id}
        if plant_id:
            request_params["plantId"] = plant_id
        response = await self.session.get(self.get_url("newMixApi.do"), params=request_params)
        return response.json().get("obj", {})

    async def mix_totals(self, mix_id: str, plant_id: str) -> dict[str, Any]:
        """Get totals values from a Mix device."""
        response = await self.session.post(self.get_url("newMixApi.do"), params={
            "op": "getEnergyOverview", "mixId": mix_id, "plantId": plant_id
        })
        return response.json().get("obj", {})

    async def mix_system_status(self, mix_id: str, plant_id: str) -> dict[str, Any]:
        """Get current status from a Mix device."""
        response = await self.session.post(self.get_url("newMixApi.do"), params={
            "op": "getSystemStatus_KW", "mixId": mix_id, "plantId": plant_id
        })
        return response.json().get("obj", {})

    async def mix_detail(self, mix_id: str, plant_id: str, timespan: Timespan = Timespan.hour, date: datetime.datetime | None = None) -> dict[str, Any]:
        """Get Mix details for the given timespan."""
        date_str = self.__get_date_string(timespan, date)
        response = await self.session.post(
            self.get_url("newMixApi.do"),
            params={
                "op": "getEnergyProdAndCons_KW", "plantId": plant_id,
                "mixId": mix_id, "type": timespan.value, "date": date_str,
            },
        )
        return response.json().get("obj", {})

    async def get_mix_inverter_settings(self, serial_number: str) -> dict[str, Any]:
        """Get the inverter settings related to battery modes."""
        default_params = {"op": "getMixSetParams", "serialNum": serial_number, "kind": 0}
        response = await self.session.get(self.get_url("newMixApi.do"), params=default_params)
        return response.json()

    async def dashboard_data(self, plant_id: str, timespan: Timespan = Timespan.hour, date: datetime.datetime | None = None) -> dict[str, Any]:
        """Get dashboard data for a plant over a timespan."""
        date_str = self.__get_date_string(timespan, date)
        response = await self.session.post(self.get_url("newPlantAPI.do"), params={
            "action": "getEnergyStorageData", "date": date_str,
            "type": timespan.value, "plantId": plant_id,
        })
        return response.json()

    async def plant_settings(self, plant_id: str) -> dict[str, Any]:
        """Get a dictionary containing the settings for the specified plant."""
        response = await self.session.get(self.get_url("newPlantAPI.do"), params={
            "op": "getPlant", "plantId": plant_id
        })
        return response.json()

    async def storage_detail(self, storage_id: str) -> dict[str, Any]:
        """Get "All parameters" from battery storage."""
        response = await self.session.get(self.get_url("newStorageAPI.do"), params={
            "op": "getStorageInfo_sacolar", "storageId": storage_id
        })
        return response.json()

    async def storage_params(self, storage_id: str) -> dict[str, Any]:
        """Get much more detail from battery storage."""
        response = await self.session.get(self.get_url("newStorageAPI.do"), params={
            "op": "getStorageParams_sacolar", "storageId": storage_id
        })
        return response.json()

    async def storage_energy_overview(self, plant_id: str, storage_id: str) -> dict[str, Any]:
        """Get some energy/generation overview data."""
        response = await self.session.post(self.get_url("newStorageAPI.do?op=getEnergyOverviewData_sacolar"), params={
            "plantId": plant_id, "storageSn": storage_id
        })
        return response.json().get("obj", {})

    async def inverter_list(self, plant_id: str) -> list[dict[str, Any]]:
        """Use device_list, it's more descriptive since the list contains more than inverters."""
        warnings.warn(
            "This function may be deprecated in the future because naming is not correct, use device_list instead", DeprecationWarning, stacklevel=2)
        return await self.device_list(plant_id)

    async def __get_all_devices(self, plant_id: str) -> dict[str, Any]:
        """Get basic plant information with device list."""
        response = await self.session.get(self.get_url("newTwoPlantAPI.do"),
                                          params={"op": "getAllDeviceList",
                                                  "plantId": plant_id,
                                                  "language": 1})
        return response.json().get("deviceList", {})

    async def device_list(self, plant_id: str) -> list[dict[str, Any]]:
        """Get a list of all devices connected to plant."""
        device_list = (await self.plant_info(plant_id)).get("deviceList", [])

        if not device_list:
            device_list = await self.__get_all_devices(plant_id)

        return device_list

    async def plant_info(self, plant_id: str) -> dict[str, Any]:
        """Get basic plant information with device list."""
        response = await self.session.get(self.get_url("newTwoPlantAPI.do"), params={
            "op": "getAllDeviceListTwo", "plantId": plant_id, "pageNum": 1, "pageSize": 1
        })
        return response.json()

    async def plant_energy_data(self, plant_id: str) -> dict[str, Any]:
        """Get the energy data used in the 'Plant' tab in the phone."""
        response = await self.session.post(self.get_url("newTwoPlantAPI.do"),
                                           params={"op": "getUserCenterEnertyDataByPlantid"},
                                           data={"language": 1, "plantId": plant_id})
        return response.json()

    async def is_plant_noah_system(self, plant_id: str) -> dict[str, Any]:
        """Check whether a plant is a Noah system."""
        response = await self.session.post(self.get_url("noahDeviceApi/noah/isPlantNoahSystem"), data={
            "plantId": plant_id
        })
        return response.json()

    async def noah_system_status(self, serial_number: str) -> dict[str, Any]:
        """Get the Noah device status."""
        response = await self.session.post(self.get_url("noahDeviceApi/noah/getSystemStatus"), data={
            "deviceSn": serial_number
        })
        return response.json()

    async def noah_info(self, serial_number: str) -> dict[str, Any]:
        """Get detailed Noah device information."""
        response = await self.session.post(self.get_url("noahDeviceApi/noah/getNoahInfoBySn"), data={
            "deviceSn": serial_number
        })
        return response.json()

    async def update_plant_settings(self, plant_id: str, changed_settings: dict[str, Any], current_settings: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Update plant settings.

        Args:
            plant_id: Plant identifier.
            changed_settings: Dict of settings to change.
            current_settings: Current settings dict or None.

        Returns:
            dict: Server response indicating success or failure.

        """
        if current_settings is None:
            current_settings = await self.plant_settings(plant_id)

        form_settings = {
            "plantCoal": (None, str(current_settings["formulaCoal"])),
            "plantSo2": (None, str(current_settings["formulaSo2"])),
            "accountName": (None, str(current_settings["userAccount"])),
            "plantID": (None, str(current_settings["id"])),
            "plantFirm": (None, "0"),
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

        for setting, value in changed_settings.items():
            form_settings[setting] = (None, str(value))

        response = await self.session.post(self.get_url(
            "newTwoPlantAPI.do?op=updatePlant"), files=form_settings)

        return response.json()

    async def update_inverter_setting(self, serial_number: str, setting_type: str,
                                      default_parameters: dict[str, Any], parameters: dict[str, Any] | list[Any]) -> dict[str, Any]:
        """Apply inverter settings."""
        _ = serial_number
        _ = setting_type
        settings_parameters = parameters

        if isinstance(parameters, list):
            settings_parameters = {}
            for index, param in enumerate(parameters, start=1):
                settings_parameters["param" + str(index)] = param

        settings_parameters = {**default_parameters, **settings_parameters}

        response = await self.session.post(self.get_url("newTcpsetAPI.do"),
                                           params=settings_parameters)
        return response.json()

    async def update_mix_inverter_setting(self, serial_number: str, setting_type: str, parameters: dict[str, Any] | list[Any]) -> dict[str, Any]:
        """Set inverter parameters for a Mix inverter."""
        default_parameters = {
            "op": "mixSetApiNew", "serialNum": serial_number, "type": setting_type
        }
        return await self.update_inverter_setting(serial_number, setting_type,
                                                  default_parameters, parameters)

    async def update_ac_inverter_setting(self, serial_number: str, setting_type: str, parameters: dict[str, Any] | list[Any]) -> dict[str, Any]:
        """Set inverter parameters for an AC-coupled inverter."""
        default_parameters = {
            "op": "spaSetApi", "serialNum": serial_number, "type": setting_type
        }
        return await self.update_inverter_setting(serial_number, setting_type,
                                                  default_parameters, parameters)

    async def update_tlx_inverter_time_segment(self, serial_number: str, segment_id: int, batt_mode: int, start_time: datetime.time, end_time: datetime.time, enabled: bool) -> dict[str, Any]:
        """Update a TLX inverter time segment."""
        params = {"op": "tlxSet"}
        data = {
            "serialNum": serial_number,
            "type": f"time_segment{segment_id}",
            "param1": batt_mode,
            "param2": start_time.strftime("%H"),
            "param3": start_time.strftime("%M"),
            "param4": end_time.strftime("%H"),
            "param5": end_time.strftime("%M"),
            "param6": "1" if enabled else "0"
        }

        response = await self.session.post(self.get_url("newTcpsetAPI.do"), params=params, data=data)
        result = response.json()

        if not result.get("success", False):
            msg = f"Failed to update TLX inverter time segment: {result.get('msg', 'Unknown error')}"
            raise GrowattError(msg)

        return result

    async def update_tlx_inverter_setting(self, serial_number: str, setting_type: str, parameter: dict[str, Any] | list[Any] | str) -> dict[str, Any]:
        """Set parameters on a TLX inverter."""
        default_parameters = {
            "op": "tlxSet", "serialNum": serial_number, "type": setting_type
        }

        if not isinstance(parameter, (dict, list)):
            parameter = {"param1": parameter}
        elif isinstance(parameter, list):
            parameter = {f"param{index+1}": param for index, param in enumerate(parameter)}

        return await self.update_inverter_setting(serial_number, setting_type,
                                                  default_parameters, parameter)

    async def update_noah_settings(self, serial_number: str, setting_type: str, parameters: dict[str, Any] | list[Any]) -> dict[str, Any]:
        """Apply settings for a Noah device."""
        default_parameters = {"serialNum": serial_number, "type": setting_type}
        settings_parameters = parameters

        if isinstance(parameters, list):
            settings_parameters = {}
            for index, param in enumerate(parameters, start=1):
                settings_parameters["param" + str(index)] = param

        settings_parameters = {**default_parameters, **settings_parameters}

        response = await self.session.post(self.get_url("noahDeviceApi/noah/set"),
                                           data=settings_parameters)
        return response.json()

    async def classic_inverter_info(self, device_sn: str) -> dict[str, Any]:
        """
        Get classic inverter information by scraping the inverter settings page.

        Args:
            device_sn: The serial number of the inverter.

        Returns:
            dict: A dictionary containing the inverter information.

        Raises:
            GrowattError: If the inverter data cannot be extracted from the response.

        """
        response = await self.session.get(
            self.get_url("commonDeviceSetC/setInverter"),
            params={"type": "server", "invSn": device_sn},
        )

        match = re.search(r"inv=JSON\.parse\('(\{.*?\})'\)", response.text)
        if not match:
            msg = f"Could not find inverter data in response for device {device_sn}"
            raise GrowattError(msg)

        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as err:
            msg = f"Failed to parse inverter data JSON for device {device_sn}"
            raise GrowattError(msg) from err

    async def update_classic_inverter_setting(self, default_parameters: dict[str, Any], parameters: dict[str, Any] | list[Any]) -> dict[str, Any]:
        """Apply classic inverter settings."""
        settings_parameters = parameters

        if isinstance(parameters, list):
            settings_parameters = {}
            for index, param in enumerate(parameters, start=1):
                settings_parameters["param" + str(index)] = param

        settings_parameters = {**default_parameters, **settings_parameters}

        response = await self.session.post(self.get_url("tcpSet.do"),
                                           params=settings_parameters)
        return response.json()
