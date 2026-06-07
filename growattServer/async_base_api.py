"""Async Growatt API client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Self

import httpx

from .base_api import DEFAULT_TIMEOUT, _GrowattApiBase, hash_password
from .exceptions import (
    GrowattApiConnectionError,
    GrowattApiError,
    GrowattApiStatusError,
    GrowattApiTimeoutError,
)

_T = TypeVar("_T")


class AsyncGrowattApi(_GrowattApiBase):
    """
    Async client for Growatt API endpoints.

    All methods inherited from ``_GrowattApiBase`` work transparently in async
    context because they return ``self._request(...)`` or chain to another
    base method, both of which yield coroutines when ``_request`` is async.
    """

    def __init__(self, add_random_user_id: bool = False, agent_identifier: str | None = None, session: httpx.AsyncClient | None = None, timeout: float | None = DEFAULT_TIMEOUT) -> None:
        """
        Initialize the Growatt API client.

        Args:
            add_random_user_id: Append a short random suffix to the user-agent.
            agent_identifier: Optional override for the user-agent string.
            session: Optional httpx.AsyncClient to reuse.
            timeout: Request timeout in seconds. Defaults to 30s. Pass None to disable.

        """
        super().__init__(add_random_user_id, agent_identifier)

        if session is not None:
            self.session = session
            self._owns_session = False
        else:
            self.session = httpx.AsyncClient(
                headers={"User-Agent": self.agent_identifier},
                follow_redirects=True,
                timeout=timeout,
            )
            self._owns_session = True

    async def _request(self, method: str, url: str, *, params: dict[str, Any] | None = None, data: dict[str, Any] | None = None, follow_redirects: bool | None = None, extract: Callable[[Any], _T] | None = None, text: bool = False) -> Any:
        """Make an async HTTP request and return the JSON response (or text if text=True)."""
        kwargs: dict[str, Any] = {}
        if params is not None:
            kwargs["params"] = params
        if data is not None:
            kwargs["data"] = data
        if follow_redirects is not None:
            kwargs["follow_redirects"] = follow_redirects
        try:
            response = await self.session.request(method, url, **kwargs)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            msg = f"Request to {url} timed out"
            raise GrowattApiTimeoutError(msg) from exc
        except httpx.ConnectError as exc:
            msg = f"Failed to connect to {url}"
            raise GrowattApiConnectionError(msg) from exc
        except httpx.HTTPStatusError as exc:
            msg = f"HTTP {exc.response.status_code} error for {url}"
            raise GrowattApiStatusError(msg, exc.response.status_code) from exc
        except httpx.HTTPError as exc:
            msg = f"HTTP error during request to {url}: {exc}"
            raise GrowattApiError(msg) from exc
        result = response.text if text else response.json()
        return extract(result) if extract is not None else result

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

    # Methods that need direct session access or chain async calls

    async def plant_list(self, user_id: str) -> dict[str, Any]:
        """
        Get a list of plants connected to this account.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict: A dictionary containing 'data' (list of plants) and 'totalData' keys.

        Raises:
            GrowattApiError: If the request to the server fails.

        """
        return await self._request(
            "GET", self.get_url("PlantListAPI.do"),
            params={"userId": user_id},
            follow_redirects=False,
            extract=lambda r: r.get("back", []),
        )

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
        response.raise_for_status()

        data = response.json()["back"]
        if data["success"]:
            data.update({
                "userId": data["user"]["id"],
                "userLevel": data["user"]["rightlevel"]
            })
        return data

    async def device_list(self, plant_id: str) -> list[dict[str, Any]]:
        """Get a list of all devices connected to plant."""
        device_list = (await self.plant_info(plant_id)).get("deviceList", [])

        if not device_list:
            # for tlx systems, the device_list in plant is empty, so use _get_all_devices() instead
            device_list = await self._get_all_devices(plant_id)

        return device_list

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
        # If no existing settings have been provided then get them from the growatt server
        if current_settings is None:
            current_settings = await self.plant_settings(plant_id)

        # These are the parameters that the form requires, without these an error is thrown. Pre-populate their values with the current values
        form_settings = {
            "plantCoal": (None, str(current_settings["formulaCoal"])),
            "plantSo2": (None, str(current_settings["formulaSo2"])),
            "accountName": (None, str(current_settings["userAccount"])),
            "plantID": (None, str(current_settings["id"])),
            # Hardcoded to 0 as I can't work out what value it should have
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

        # Overwrite the current value of the setting with the new value
        for setting, value in changed_settings.items():
            form_settings[setting] = (None, str(value))

        response = await self.session.post(self.get_url(
            "newTwoPlantAPI.do?op=updatePlant"), files=form_settings)
        response.raise_for_status()

        return response.json()
