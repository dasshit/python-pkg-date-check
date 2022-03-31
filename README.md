# **Install**:

```
git clone git@github.com:dasshit/python-pkg-date-check.git
cd package_date_checker
pip install -r requirements.txt
alias pydep-check='$(which python3) -m pydep-check'
```

# **Usage**

```
pydep-check --help
usage: pydep-check [-h] [-p PATH] [-d DATE] [--handle HANDLE]

Command line tool for checking Python 3 depencies publish date

options:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  Path to requirements.txt
  -d DATE, --date DATE  Last safe date for packages
  --handle HANDLE       Rewrite version in file to last save```