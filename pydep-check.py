import os
import json
import requests

import argparse

from typing import Set, Dict

from pkg_resources import parse_version

from datetime import datetime, timedelta

import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    level='DEBUG',
    format="<level>{level: <8}</level> | "
           "<level>{message}</level>"
)


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



def get_default_date():

    return datetime.strptime('2022-02-23', '%Y-%m-%d') \
           + timedelta(hours=23, minutes=59, seconds=59)


def parse_date(date: str = '2022-02-23') -> datetime.date:

    date_obj = None

    for regexp in ('%d/%m/%Y', '%d.%m.%Y', '%d-%m-%Y',
                   '%Y/%m/%d', '%Y.%m.%d', '%Y-%m-%d'):
        try:
            date_obj = datetime.strptime(date, regexp) \
                       + timedelta(hours=23, minutes=59, seconds=59)
        except ValueError:
            continue
        except Exception as error:
            logger.exception(error)

    if date_obj:
        return date_obj
    else:
        logger.warning(f'Cant parse date - {date}')

        date = get_default_date()

        logger.warning(f'Setting default date - {date}')
        return date


def read_file(path: str):

    if not os.path.exists(path):
        raise FileNotFoundError(f'File not found by this path: {path}')

    if os.path.isdir(path):

        path = os.path.join(path, 'requirements.txt')
        logger.warning(f'Path leads to dir, setting "{path}" as path')
        if not os.path.exists(path):
            raise FileNotFoundError(f'File not found by this path: {path}')

    with open(path, 'r') as file:
        for line in file:
            if line:
                yield line


def parse_deps_from_file(path: str = 'requirements.txt', date: datetime = None) -> Set[Dict[str, str]]:

    deps_dict = []

    for i, line in enumerate(read_file(path)):
        line = line.rstrip()

        logger.info(line)

        line_dict = None

        for splitter in ('==', '>=', '<=', '~=',
                         '>', '<'):
            if line.count(splitter):

                key, value = line.split(splitter)
                line_dict = {
                    key: {
                        'version': value,
                        'splitter': splitter,
                        'safe_releases': sorted(get_safe_releases(key, date), key=parse_version)
                    }
                }

                break
        if line_dict is None:
            raise ValueError(f'Cannot parse line {i}: {line}')

        yield line_dict


def check_deps(args):

    exceptions = 0

    new_package_list = []

    for package in parse_deps_from_file(args.path, args.date):

        for name, info in package.items():

            if info['version'] not in info['safe_releases']:

                safe_version = info['safe_releases'][-1]

                if not args.handle:

                    logger.error(
                        'User requested unsafe version for package {name}{splitter}{version}, last safe version: {safe_version}'.format(
                            name=name, safe_version=info['safe_releases'][-1], **info
                        )
                    )

                    exceptions += 1
                else:
                    logger.warning(
                        'Changing version for package {name} from {version} to last safe: {safe_version}'.format(
                            name=name, safe_version=safe_version, version=package[name]['version'])
                    )

                    package[name]['version'] = safe_version

            new_package_list.append(package)

    if exceptions and not args.handle:

        sys.exit(2)

    elif args.handle:

        path = args.path

        if not os.path.exists(path):
            raise FileNotFoundError(f'File not found by this path: {path}')

        if os.path.isdir(path):

            path = os.path.join(path, 'requirements.txt')
            logger.warning(f'Path leads to dir, setting "{path}" as path')
            if not os.path.exists(path):
                raise FileNotFoundError(f'File not found by this path: {path}')

        with open(path, 'w') as file:

            text = ''

            for package in new_package_list:

                for name, info in package.items():

                    text += '{name}{splitter}{version}\n'.format(
                        name=name, **info)

            file.write(text)


parser = argparse.ArgumentParser(
    prog='pydep-check',
    description='Command line tool '
                'for checking Python 3 depencies publish date')

parser.add_argument(
    '-p', '--path',
    default='requirements.txt',
    type=str, help='Path to requirements.txt')

parser.add_argument(
    '-d', '--date',
    default=get_default_date(),
    type=parse_date, help='Last safe date for packages'
)

parser.add_argument('--handle',
                    default=False,
                    type=bool, help='Rewrite version in file to last save')

args = parser.parse_args()

check_deps(args)
