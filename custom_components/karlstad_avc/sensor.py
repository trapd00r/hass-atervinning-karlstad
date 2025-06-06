import logging
from datetime import timedelta
import requests
from bs4 import BeautifulSoup
import re
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

URL = "https://karlstadsenergi.se/atervinning/atervinningscentraler"
SCAN_INTERVAL = timedelta(hours=24)

CENTERS = [
    "Djupdalen",
    "Heden",
    "Vålberg",
    "Våxnäs",
    "Väse",
    "Kvarntorp (Forshaga)",
    "Molkom",
]

def extract_center_name(header_text):
    match = re.match(r"([A-Za-zåäöÅÄÖ\s()]+?)(Stängt|Öppet|\(|$)", header_text)
    if match:
        return match.group(1).replace("ÅVC ", "").strip()
    return header_text.replace("ÅVC ", "").strip()

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # Not used in new integrations
    pass

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = KarlstadAVCCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    sensors = [KarlstadAVCSensor(coordinator, center) for center in CENTERS]
    async_add_entities(sensors, True)

class KarlstadAVCCoordinator(DataUpdateCoordinator):
    def __init__(self, hass):
        super().__init__(
            hass,
            _LOGGER,
            name="Karlstad ÅVC Coordinator",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        return await self.hass.async_add_executor_job(fetch_opening_hours)

def fetch_opening_hours():
    resp = requests.get(URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    data = {}
    for header in soup.find_all("div", class_="ke-open-hours__header"):
        raw_header = header.get_text(strip=True)
        center_name = extract_center_name(raw_header)
        if center_name not in CENTERS:
            continue
        content = header.find_next_sibling("div", class_="ke-open-hours__content")
        today = None
        tomorrow = None
        if content:
            days = content.find_all("div", class_="ke-open-hours__day")
            for i, day in enumerate(days):
                label = day.find("p").get_text(strip=True)
                value = day.find_all("p")[1].get_text(strip=True)
                if label.lower().startswith("idag"):
                    today = value
                    # Tomorrow is the next entry, if available
                    if i + 1 < len(days):
                        tomorrow_value = days[i+1].find_all("p")[1].get_text(strip=True)
                        tomorrow = tomorrow_value
                    break
        data[center_name] = {"today": today, "tomorrow": tomorrow}
    return data

class KarlstadAVCSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, center_name):
        super().__init__(coordinator)
        self._attr_name = f"Karlstad ÅVC {center_name}"
        self.center_name = center_name
        self._attr_unique_id = f"karlstad_avc_{center_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('å', 'a').replace('ä', 'a').replace('ö', 'o')}"

    @property
    def state(self):
        data = self.coordinator.data.get(self.center_name, {})
        return data.get("today")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self.center_name, {})
        return {"tomorrow": data.get("tomorrow")} 