import os
import sys

from typing import Set, Dict

from pkg_resources import parse_version

from datetime import datetime, timedelta
from loguru import logger

from project.pypi_api import get_safe_releases


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
