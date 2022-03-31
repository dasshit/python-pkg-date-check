import json
import requests

from typing import Dict

from datetime import datetime

from project.logger import logger


session = requests.Session()


def get_packet_info(package_name: str) -> Dict:

    result = session.get(
        url=f'https://pypi.org/pypi/{package_name}/json'
    )

    try:
        return result.json().get('releases', {})
    except json.decoder.JSONDecodeError:
        return {}


def get_safe_releases(package_name: str, date: datetime) -> Dict:

    safe_version = set()

    for version, info_list in get_packet_info(package_name).items():

        for info in info_list:

            upload_date_obj = datetime.strptime(
                info['upload_time'], '%Y-%m-%dT%H:%M:%S')

            if date > upload_date_obj:
                safe_version.add(version)

    return tuple(safe_version)
