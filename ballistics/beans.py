"""
Beans.
Loading bean data from the Bullet data, and outputting it in various formats
"""
from dataclasses import dataclass
import json
from typing import List, Dict

import ballistics
from .utils import Stopwatch
from .config import config
# from .roasts import Roast, find_roast_by


@dataclass
class Bean:
    """
    Utility class for coffee beans
    """
    beanId: str = ''
    name: str = ''
    description: str = ''
    country: str = ''
    region: str = ''
    farm: str = ''
    process: str = ''
    isOrganic: bool = False
    isDecaf: bool = False
    raw: json = None
    roasts: list = None

    def __post_init__(self):
        if not config.initialized:
            config.init_env()
        with open(config.beans_dir / self.beanId) as json_file:
            self.raw = json.load(json_file)
        self.beanId = self.raw.get('uid')
        self.name = self.raw.get('name')
        if 'decaf' in self.name.casefold():
            self.isDecaf = True
        self.description = self.raw.get('description')
        self.country = self.raw.get('country')
        if not self.country:
            self.country = 'Blend/Unknown'
        self.region = self.raw.get('region')
        self.farm = self.raw.get('farm')
        self.process = self.raw.get('process')
        # TODO: check to make sure this always resolved to true or false
        self.isOrganic = self.raw.get('isOrganic')
        self.load_roasts()

    def load_roasts(self):
        """
        Loads and attaches all the roasts that use this bean
        :return: list of Roasts
        """
        self.roasts = list()
        roasts = ballistics.find_roast_by(self.beanId, 'beanid').get(self.beanId)
        # if there are no roasts for the bean, skip it
        if roasts:
            for roast_id in roasts:
                self.roasts.append(ballistics.Roast(roast_id))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, Origin:{self.country}, # Roasts:{len(self.roasts)})"

    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"


def find_bean_by(name: str) -> Dict:
    """
    Searches through the bean repository to find all bean IDs that match a (partial) name provided
    :param name: the name (or fragment) of a bean to search for
    :return: dict of matching beans: {name: [ID]}
    """
    beans = dict()
    for file in config.beans_dir.glob('*'):
        config.logger.debug(f"Found bean: {file}")
        with open(file) as json_file:
            beanf = json.load(json_file)
        bname = beanf.get('name')
        if name.casefold() in bname.casefold():
            if not beans.get(bname):
                beans[bname] = list()
            beans[bname].append(beanf.get('uid'))
    return beans
