"""
Roasts.
Loading roast data from the Bullet data, and outputting it in various formats
"""
from dataclasses import dataclass
import json
from pprint import pprint
from typing import List, Dict

from .utils import Stopwatch
from .config import config
from .beans import Bean, find_bean_by


@dataclass
class Roast:
    """
    Utility class for coffee roasts
    """
    roastId: str = ''
    name: str = ''
    # description: str = ''
    # country: str = ''
    # region: str = ''
    # farm: str = ''
    # process: str = ''
    # isOrganic: bool = False
    # isDecaf: bool = False
    raw: json = None

    def __post_init__(self):
        if not config.initialized:
            config.init_env()
        with open(config.roasts_dir / self.roastId) as json_file:
            self.raw = json.load(json_file)
        self.beanId = self.raw.get('uid')
        self.name = self.raw.get('roastName')
        # if 'decaf' in self.name.casefold():
        #     self.isDecaf = True
        # self.description = self.raw.get('description')
        # self.country = self.raw.get('country')
        # if not self.country:
        #     self.country = 'Blend/Unknown'
        # self.region = self.raw.get('region')
        # self.farm = self.raw.get('farm')
        # self.process = self.raw.get('process')
        # self.isOrganic = self.raw.get('isOrganic')

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, Origin:{self.beanId})"

    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"


def find_roast_by(search_val: str, method: str = 'name') -> Dict:
    """
    Searches through the roasts repository to find all roast IDs that match a (partial) name provided
    :param search_val: the name (or fragment) of a roast to search for
    :param method: (optional) 'name' or 'beanid' - match on the roast name, or the bean id
    :return: dict of matching roasts: {name: [ID]}
    """
    roasts = dict()
    for file in config.roasts_dir.glob('*'):
        config.logger.debug(f"Found roast: {file}")
        with open(file) as json_file:
            roastf = json.load(json_file)
        rname = roastf.get('roastName')
        roast_id = roastf.get('uid')
        bean_id = roastf.get('beanId')
        # filter out the roasts that aren't mine (NOTE: This is peculiar to MY naming scheme, YMMV
        if roastf.get('isFork') == 1:
            # This flag indicates a saved roast or other roast brought into RoasTime that wasn't actually roasted
            continue
        if ' - ' not in rname:
            # this means it's a roast that doesn't follow my naming convention!
            config.logger.debug(f"Found a roast naming scheme violation, roastID {roast_id}")
            continue
        # match on name
        if method == 'beanid':
            if search_val != bean_id:
                continue
        else:
            if search_val.casefold() not in rname.casefold():
                continue
        if not roasts.get(bean_id):
            roasts[bean_id] = list()
        roasts[bean_id].append(roast_id)
    return roasts
