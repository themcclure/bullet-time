"""
Roasts.
Loading roast data from the Bullet data, and outputting it in various formats
"""
from dataclasses import dataclass
import json
from pprint import pprint
from typing import List, Dict
from datetime import datetime, timedelta

from .errors import ForeignRoastException
from .utils import Stopwatch
from .config import config
from .beans import Bean, find_bean_by


@dataclass
class RoastCollection:
    """
    Collection of Roasts
    """
    # roasts: list

    def __post_init__(self):
        self.roasts = list()
        if not config.initialized:
            config.init_env()
        for file in config.roasts_dir.glob('*'):
            config.logger.debug(f"Collection loading roast: {file.stem}")
            try:
                roast = Roast(file.stem)
                if roast:
                    self.roasts.append(roast)
            except ForeignRoastException as e:
                config.logger.debug(f"Encountered error creating Roast ({file.stem}, message = {e}")

    def __iter__(self):
        # FIXME: this isn't working for some reason
        return iter(self.roasts)

    def __repr__(self):
        return f"{self.__class__.__name__}(Collection of {len(self.roasts)} roasts)"

    def __str__(self):
        return f"{self.__class__.__name__}(Collection of {len(self.roasts)} roasts)"


@dataclass
class Roast:
    """
    Utility class for coffee roasts
    """
    roastId: str = ''
    batch: int = None
    name: str = ''
    description: str = ''
    roastLevel: str = ''
    url: str = ''
    descriptionBean: str = ''
    country: str = ''
    region: str = ''
    process: str = ''
    isOrganic: bool = False
    isDecaf: bool = False
    weightGreen: float = 0.0
    weightRoasted: float = 0.0
    weightLossPct: float = 0.0
    roastDate: datetime = None
    roastTimeDrying: float = 0.0
    roastTimeDevelopment: float = 0.0
    roastTimeTotal: float = 0.0
    roastDVPct: float = 0.0
    bean: Bean = None
    raw: json = None

    def __post_init__(self):
        if not config.initialized:
            config.init_env()
        with open(config.roasts_dir / self.roastId) as json_file:
            self.raw = json.load(json_file)
        self.beanId = self.raw.get('beanId')
        roastname = self.raw.get('roastName')

        ################
        # Fatal error checking
        ################
        # This flag indicates a saved roast or other roast brought into RoasTime that wasn't actually roasted
        if self.raw.get('isFork') == 1:
            raise ForeignRoastException(f"Roast {self.roastId} is a recipe or borrowed roast profile")
        # we have found an abberant roast, and it either needs to be renamed (fixed in the source) or it needs
        # to be excluded from the data
        if ' - ' not in roastname:
            config.logger.debug(f"Found an aberrantly named roast {roastname}")
            raise ForeignRoastException(f"Roast {self.roastId} aberrantly named as {roastname}")
        ################

        # split names into batch number and name
        self.batch, self.name = self.raw.get('roastName').split(' - ')
        self.url = config.baseUrl + self.batch

        self.bean = Bean(self.beanId)
        self.weightGreen = float(self.raw.get('weightGreen'))
        self.weightRoasted = float(self.raw.get('weightRoasted'))
        self.weightLossPct = (1.0 - self.weightRoasted / self.weightGreen)*100.0
        self.roastDate = datetime.fromtimestamp(self.raw.get('dateTime') / 1000)
        # enjoy between these two date
        self.roastBestDate = [self.roastDate + timedelta(days=config.bestDaysStart), self.roastDate + timedelta(days=config.bestDaysEnd)]
        self.roastTimeTotal = float(self.raw.get('totalRoastTime'))
        rate = int(self.raw.get('sampleRate'))
        start_at = int(self.raw.get('roastStartIndex'))
        self.roastTimeDrying = (int(self.raw.get('indexYellowingStart')) - start_at) / rate  # number of samples since start divided by samples/second
        self.roastTimeDevelopment = self.roastTimeTotal - (int(self.raw.get('indexFirstCrackStart')) / rate)  # from first crack to end of roast
        self.roastDVPct = self.roastTimeDevelopment / self.roastTimeTotal * 100.0
        roast_degree = self.raw.get('roastDegree')
        if roast_degree:
            self.roastLevel = config.roastLevels[int(roast_degree)]

        # info inherited from the Bean
        self.descriptionBean = self.bean.description
        self.isDecaf = self.bean.isDecaf
        self.isOrganic = self.bean.isOrganic
        self.country = self.bean.country
        self.region = self.bean.region
        self.process = self.bean.process

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
    if not config.initialized:
        config.init_env()

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
