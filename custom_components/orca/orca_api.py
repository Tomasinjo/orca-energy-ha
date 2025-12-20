"""Orca Heat Pump API client."""

import asyncio
from dataclasses import dataclass, field
import logging
from pathlib import Path
import re
from typing import Any

import aiofiles
import aiohttp
import yaml

_LOGGER = logging.getLogger(__name__)

# translates english circuit names to slovenian
CIRCUIT_NAME_MAP_SI = {
    "Heating Circuit 1": "ogrevalni krog 1",
    "Heating Circuit 2": "ogrevalni krog 2",
    "Heating Circuit 3": "ogrevalni krog 1",
    "Direct Circuit 1": "direktna veja 1",
    "Direct Circuit 2": "direktna veja 2",
    "Direct Circuit 3": "direktna veja 3",
    "Cellar": "klet",
    "Ground Floor": "pritličje",
    "Floor": "talno",
    "1. Floor": "1. nadstropje",
    "2. Floor": "2. nadstropje",
    "Attic": "mansarda",
    "Radiator": "tadiatorji",
    "Convector": "konvektorji",
    "Heating": "gretje",
    "Cooling": "hlajenje",
    "Wall": "stensko",
}


@dataclass
class OrcaTagConfig:
    """Represents a static configuration entry from config.yaml."""

    id: str
    tag: str
    name: str
    name_si: str
    description: str = ""
    type: str = ""  # temperature, percentage, boolean, multimode, power_factor
    unit: str = ""
    adjustable: bool = False
    heating_circuit: int | None = None
    value_map: dict[int, str] = field(default_factory=dict)

    # These fields are updated dynamically during initialization based on MK1/MK2
    final_name: str = field(init=False)
    final_name_si: str = field(init=False)
    unique_id: str = field(init=False)

    def __post_init__(self):
        """Post-initialization to set final names and unique ID."""
        self.final_name = self.name.capitalize()
        self.final_name_si = self.name_si.capitalize()
        self.unique_id = self.id


@dataclass
class OrcaTagValue:
    """Represents a runtime value retrieved from the Heat Pump."""

    tag: str
    value: float | int | bool | None
    config: OrcaTagConfig

    def __repr__(self):
        """Printable for debugging."""
        return f"""
Tag: {self.tag}
Value: {self.value}
Config: {self.config}
""".strip()


class OrcaApi:
    """Client for interacting with the Orca Heat Pump API."""

    def __init__(self, username, password, host, config_path=None) -> None:
        """Initialize the Orca API client."""
        self.username = username
        self.password = password
        self.host = host
        self.available_circuits: list[int] = []
        self._token = None
        self._config: list[OrcaTagConfig] = []
        self._config_by_tags: dict[str, OrcaTagConfig] = {}
        self._config_by_ids: dict[str, OrcaTagConfig] = {}

        # Resolve config path
        if config_path:
            self._config_path = config_path
        else:
            current_dir = Path(__file__).parent
            self._config_path = current_dir / "config.yml"

    async def initialize(self):
        """Load configuration and authenticate.

        Loads config, authenticates, determines circuit names,
        and updates tag definitions accordingly.
        """
        config_entries = await self._load_config()
        self._config_by_tags = {
            config.tag: config for config in config_entries
        }  # initial config, unfiltered, required by _get_bulk_values()
        self._config = await self._filter_and_rename_circuits(config_entries)

        self._config_by_tags = {
            config.tag: config for config in self._config
        }  # final config, filtered, and with final names and unique_id
        self._config_by_ids = {config.unique_id: config for config in self._config}

    async def fetch_all(self) -> list[OrcaTagValue]:
        """Fetches all tags defined in config.

        Returns a dict keyed by tag name containing OrcaTagValue objects.
        Filters out invalid (-9999) or unknown tags.
        """
        return await self._get_bulk_values(tags=list(self._config_by_tags.keys()))

    async def fetch_by_tags(self, tags: list[str]) -> dict[str, OrcaTagValue]:
        """Fetches specific list of tags."""
        return {c.tag: c for c in await self._get_bulk_values(tags)}

    async def fetch_by_ids(self, ids: list[str]) -> dict[str, OrcaTagValue]:
        """Fetches specific list by unique ID."""
        tags = [
            self._config_by_ids[_id].tag for _id in ids if self._config_by_ids.get(_id)
        ]
        return {c.config.unique_id: c for c in await self._get_bulk_values(tags)}

    async def set_value_by_tag(self, tag: str, value: Any):
        """Sets a value on the heat pump by tag.

        Performs necessary type conversions (e.g. float 22.5 -> int 225).
        """
        if tag not in self._config_by_tags:
            raise ValueError(f"Tag {tag} is not defined in configuration.")

        config = self._config_by_tags[tag]
        if not config.adjustable:
            raise ValueError(f"Tag {tag} is not marked as adjustable.")

        converted_val = self._prepare_value_for_write(value, config)

        url = f"http://{self.host}/cgi/writeTags?n=1&t1={tag}&v1={converted_val}"
        await self._make_request(url)

    async def set_value_by_id(self, id: str, value: Any):
        config = self._config_by_ids.get(id)
        if not config:
            raise ValueError(f"Tag with ID {id} is not defined in configuration.")
        return await self.set_value_by_tag(tag=config.tag, value=value)

    async def _load_config(self) -> list[OrcaTagConfig]:
        """Reads YAML configuration file."""
        if not Path.exists(self._config_path):
            raise FileNotFoundError(f"Config file not found at {self._config_path}")

        async with aiofiles.open(self._config_path, encoding="utf8") as f:
            content = await f.read()
            yaml_data = yaml.safe_load(content) or {}

        config = []
        for tag, data in yaml_data.items():
            config.append(
                OrcaTagConfig(
                    id=data.get("id", tag),
                    tag=tag,
                    name=data.get("name", tag),
                    name_si=data.get("name_si", tag),
                    description=data.get("description", ""),
                    type=data.get("type", "text"),
                    unit=data.get("unit", ""),
                    adjustable=data.get("adjustable", False),
                    heating_circuit=data.get("heating_circuit"),
                    value_map=data.get("value_map", {}),
                )
            )

        return config

    async def _filter_and_rename_circuits(
        self, config_entries: list[OrcaTagConfig]
    ) -> list[OrcaTagConfig]:
        """Post-initialization to set final names and unique ID.

        Determines which heating circuits are used by heat pump by checking
        whether all tags in "circuit_tags" return a valid value.
        Furthermore, circuits defined in "name_tags" are used to generate dynamic
        name according to name set in heat pump (TALNO, FLOOR, RADIATOR...)

        Returns only circuits that are actually configured.
        """
        # Tags that define the name of heating circuit
        # likely result: {1: "MK1_IME", 2: "MK1_IME(2)"}
        name_tags = {
            cfg.heating_circuit: tag
            for tag, cfg in self._config_by_tags.items()
            if cfg.id == "hc_name"
        }

        # The following defines which fields must be available (return non-9999 value)
        # to treat the heating circle as in use.
        # If all tags don't return a valid value, all config.yml entries belonging
        # to this circuit will not be fetched.
        circuit_tags = {
            0: ["2_Poti1"],
            1: ["2_Temp_Prostora"],
            2: ["2_Temp_RF2"],
            3: ["2_Poti5"],
            4: ["2_Poti3", "2_Poti3"],
            5: ["2_Temp_Zalog"],  # fake circuit for buffer tank
        }

        tags_to_get = list(name_tags.values()) + [
            i for lst in circuit_tags.values() for i in lst
        ]

        results = await self.fetch_by_tags(tags=tags_to_get)

        for circuit_id, tags in circuit_tags.items():
            # means all tags are in results and have valid value - the circuit is available
            if len([t for t in tags if t in results]) == len(tags):
                self.available_circuits.append(circuit_id)

        filtered_config = []
        for config in config_entries:
            if config.heating_circuit not in self.available_circuits:
                continue
            if name_tag := name_tags.get(config.heating_circuit):
                if name_result := results.get(name_tag):
                    appendix_en = (
                        name_result.value
                    )  # retrieves english name for circuit as configured on HP.
                    appendix_si = CIRCUIT_NAME_MAP_SI.get(
                        str(appendix_en), config.heating_circuit
                    )
                else:
                    appendix_en = config.heating_circuit
                    appendix_si = config.heating_circuit

                config.final_name = f"{appendix_en} {config.name}".capitalize()
                config.final_name_si = f"{appendix_si} {config.name_si}".capitalize()
                config.unique_id = f"{config.id}_{config.heating_circuit}"
            filtered_config.append(config)

        return filtered_config

    async def _get_bulk_values(
        self, tags: list[str], raw_mode=False
    ) -> list[OrcaTagValue]:
        """Internal method to fetch multiple tags.

        raw_mode: if True, skips the -9999 check (useful for system tags).
        """
        result = []
        if not tags:
            return result

        parsed_data = {}
        for uri in self._generate_uri(tags):
            url = f"http://{self.host}{uri}"

            response_text = await self._make_request(url)
            parsed_data |= self._parse_response(response_text)

        for tag, raw_val_str in parsed_data.items():
            config = self._config_by_tags[tag]

            # Check for non-existent sensors
            if raw_val_str == "-9999" and not raw_mode:
                continue

            processed_value = self._convert_read_value(raw_val_str, config)

            result.append(OrcaTagValue(tag=tag, value=processed_value, config=config))
        return result

    async def _make_request(self, url: str, attempt_auth=True) -> str:
        """Handles HTTP request, cookies/token, and re-authentication."""
        cookies = {"IDALToken": self._token} if self._token else {}

        try:
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.get(url, timeout=10) as resp:
                    data = await resp.text()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to heat pump: {e}")
        except asyncio.TimeoutError:
            raise TimeoutError(
                "Request to heat pump timed out, verify network connectivity."
            )
        if "#E_NEED_LOGIN" in data or "E_NEED_LOGIN" in data:
            if attempt_auth:
                _LOGGER.debug("Token expired or missing, authenticating again")
                await self._authenticate()
                return await self._make_request(url, attempt_auth=False)

        if "#E_" in data and "E_UNKNOWNTAG" not in data:
            raise RuntimeError(f"API Error: {data}")
        return data

    async def _authenticate(self):
        login_url = f"http://{self.host}/cgi/login?username={self.username}&password={self.password}"

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(login_url, timeout=10) as resp:
                        text = await resp.text()
            except Exception as e:
                raise ConnectionError(f"Auth connection failed: {e}")

            if "IDALToken" in text:
                match = re.search(r"IDALToken=([^\s]+)", text)
                if match:
                    self._token = match.group(1)
                    _LOGGER.debug("Authentication successful")
                    return
                else:
                    raise ValueError("Token not found in successful login response.")

            elif "#E_TOO_MANY_USERS" in text:
                _LOGGER.warning(
                    "Too many users connected to Heat Pump. Retrying in 5 seconds"
                )
                await asyncio.sleep(5)
                continue
            elif "#E_PASS_DONT_MATCH" in text:
                raise PermissionError("Login failed: Incorrect username or password.")
            else:
                # This handles wrong password or unknown errors
                raise PermissionError(f"Login failed: {text}")

    def _generate_uri(self, tags: list[str]) -> list[str]:
        params = ""
        count = 0
        uris = []
        for tag in tags:
            count += 1
            params += f"&t{count}={tag}"
            if count >= 150:  # max tags per request
                uris.append(f"/cgi/readTags?client=OrcaTouch1172&n={count}{params}")
                params = ""
                count = 0
        uris.append(f"/cgi/readTags?client=OrcaTouch1172&n={count}{params}")
        return uris

    def _parse_response(self, raw_data: str) -> dict[str, str]:
        """Parses the raw hash/semicolon separated response.

        Format example: 2_Temp_VF2;S_OK;192;217#Next_Tag;...
        """
        results = {}
        # Responses are separated by #
        entries = raw_data.strip().split("#")

        for entry in entries:
            clean_entry = entry.replace("\t", ";").replace("\n", ";")
            parts = clean_entry.split(";")

            if len(parts) < 4:
                continue

            tag_name = parts[0]
            status = parts[1]
            val = parts[3]

            if status != "S_OK":
                continue

            results[tag_name] = val

        return results

    def _convert_read_value(self, raw_value: str, config: OrcaTagConfig) -> Any:
        """Converts string from API to typed Python object."""

        # Helper to safely parse int/float
        def safe_num(v):
            try:
                return int(v)
            except ValueError:
                try:
                    return float(v)
                except ValueError:
                    return v

        val = safe_num(raw_value)

        if config.type in ["temperature", "percentage", "power_factor", "curve_shift"]:
            if isinstance(val, (int, float)):
                return round(val / 10.0, 1)
            return 0.0

        if config.type == "boolean":
            if str(val) == "1":
                return True
            return False

        if config.type == "multimode":
            if isinstance(val, int) and val in config.value_map:
                return config.value_map[val]
            return val
        return None

    def _prepare_value_for_write(self, input_value: Any, config: OrcaTagConfig) -> str:
        """Prepares a Python value to be sent to the API."""

        if config.type in ["temperature", "percentage", "power_factor", "curve_shift"]:
            try:
                float_val = float(input_value)
                return str(int(float_val * 10))
            except ValueError:
                raise ValueError(
                    f"Invalid numeric value for {config.type}: {input_value}"
                )

        elif config.type == "boolean":
            return "1" if input_value else "0"

        if config.type == "multimode" and isinstance(input_value, str):
            reverse_map = {v: k for k, v in config.value_map.items()}
            if input_value in reverse_map:
                return str(reverse_map[input_value])

        return str(input_value)
