import argparse


from project.shortcuts import get_default_date, \
    parse_date, check_deps


parser = argparse.ArgumentParser(
    prog='depcheck',
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
