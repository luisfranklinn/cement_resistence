import logging
import requests
import urllib3
from typing import Any

from src.config import PI_HOST, PI_USER, PI_PASS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def _get(endpoint: str) -> dict[str, Any]:
    url = f"{PI_HOST}/{endpoint.replace('#', '%23').replace('+', '%2B')}"
    try:
        r = requests.get(url, verify=False, auth=(PI_USER, PI_PASS), timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as err:
        logger.error("GET %s failed: %s", url, err)
        raise


def _get_url(url: str) -> dict[str, Any]:
    try:
        r = requests.get(url, verify=False, auth=(PI_USER, PI_PASS), timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as err:
        logger.error("GET %s failed: %s", url, err)
        raise


def _post(endpoint: str, payload: dict) -> requests.Response:
    url = f"{PI_HOST}/{endpoint}"
    try:
        r = requests.post(url, json=payload, verify=False, auth=(PI_USER, PI_PASS), timeout=30)
        r.raise_for_status()
        return r
    except requests.RequestException as err:
        logger.error("POST %s failed: %s", url, err)
        raise


def get_webid(point: str) -> str:
    data = _get(f"search/query?q={point}")
    return data["Items"][0]["WebId"]


def write_tag(tag: str, payload: dict) -> requests.Response:
    webid = get_webid(tag)
    return _post(f"streams/{webid}/value", payload)


def recorded_range(tag: str, start: str, end: str) -> dict[str, Any]:
    logger.info("recorded_range %s [%s -> %s]", tag, start, end)
    webid = get_webid(tag)
    return _get(f"streams/{webid}/recorded?startTime={start}&endTime={end}")


def recorded_at(tag: str, time: str, mode: str = "Exact") -> dict[str, Any]:
    webid = get_webid(tag)
    return _get(f"streams/{webid}/recordedattime?time={time}&retrievalMode={mode}")


def tag_value_at(tag: str, time: str) -> float | None:
    mode = "AtOrBefore" if "Growth" in tag else "Exact"
    data = recorded_at(tag, time, mode)
    return data["Value"] if data.get("Good") else None
