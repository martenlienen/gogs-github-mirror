# Set up gogs mirrors for your github repositories

The script will set up mirrors in your gogs under your user for all repos that
belong to your user and are not forks (optionally also with forks). Private
repos will be mirrored privately in gogs as well.

```sh
pip install -r requirements.txt

./setup_mirrors.py --help
```
