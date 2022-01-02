"""
Beans.
Loading bean data from the Bullet data, and outputting it in various formats
"""
from dataclasses import dataclass
import json
import os
from slugify import slugify
from pathlib import Path
from typing import List, Dict

import ballistics
from .utils import Stopwatch
from .config import config


@dataclass
class BeanCollection:
    """
    Collection of Beans
    """
    def __post_init__(self):
        self.beans = list()
        if not config.initialized:
            config.init_env()
        for file in config.beans_dir.glob('*'):
            config.logger.debug(f"Collection loading bean: {file.stem}")
            bean = Bean(file.stem)
            if bean:
                self.beans.append(bean)

    def do_all_markdown(self):
        for bean in self.beans:
            bean.to_markdown()

    def __iter__(self):
        # FIXME: this isn't working for some reason
        return iter(self.beans.__iter__())

    def __repr__(self):
        return f"{self.__class__.__name__}(Collection of {len(self.beans)} beans)"

    def __str__(self):
        return f"{self.__class__.__name__}(Collection of {len(self.beans)} beans)"


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
    isForEspresso: bool = False
    raw: json = None
    roasts: list = None

    def __post_init__(self):
        if not config.initialized:
            config.init_env()
        with open(config.beans_dir / self.beanId) as json_file:
            self.raw = json.load(json_file)
        self.beanId = self.raw.get('uid')
        self.name = self.raw.get('name')
        self.slug = slugify(self.name)
        # local and remote URLs
        self.urlSite = f"/beans/{self.slug}"
        self.url = config.baseUrl + self.urlSite
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
        self.isForEspresso = self.raw.get('espresso')
        self.roasts = ballistics.find_roast_by(self.beanId, 'beanid').get(self.beanId) or list()

    def to_markdown(self) -> Path:
        """
        Output the Bean as a markdown file.
        :return: Path of the output file
        """
        output_beans_dir = config.outputDir / "beans"
        # output_roast_dir = config.outputDir / "roasts"
        if not output_beans_dir.exists():
            output_beans_dir.mkdir(parents=True)
        output_file = output_beans_dir / f"{self.name.strip()}.md"
        with open(output_file, 'w') as beanf:
            roasts = self.get_roasts()
            # write out the frontmatter
            beanf.write("---\n")
            beanf.write(f"title: {self.name}\n")
            beanf.write(f"origin: {self.country}\n")
            beanf.write(f"slug: {self.slug}\n")
            beanf.write("type: bean\n")
            beanf.write(f"path: {self.urlSite}\n")
            beanf.write(f"rwUrl: https://roast.world/beans/{self.beanId}\n")
            if roasts:
                beanf.write(f"lastRoasted: {max(r.roastDate for r in roasts).isoformat(' ', 'minutes')}\n")
            else:
                beanf.write(f"lastRoasted: \n")
            beanf.write("tags:\n")
            beanf.write(" - roastedby\n")
            beanf.write(" - bean\n")
            if self.isDecaf:
                beanf.write(" - decaf\n")
            if self.isOrganic:
                beanf.write(" - organic\n")
            if self.isForEspresso:
                beanf.write(" - espresso\n")
            beanf.write("---\n")
            # write out the semi-structured
            # TODO: add in details
            beanf.write(f"# {self.name}:\n")
            beanf.write(f"### Importer's Description:\n{self.description}\n")
            beanf.write("\n")
            if roasts:
                beanf.write(f"### Roasts made with this bean ({round(sum([item.weightGreen for item in roasts])/1000, 1)}kg):\n")
                for roast in roasts:
                    beanf.write(f"- [{roast.batch}]({roast.urlSite}): {roast.weightGreen}g on {roast.roastDate.strftime('%a %D')}\n")
        beanf.close()
        return output_file

    def get_roasts(self) -> List:
        """
        Loads and returns all the roasts that use this bean
        :return: list of Roasts
        """
        results = list()
        roasts = ballistics.find_roast_by(self.beanId, 'beanid').get(self.beanId)
        # if there are no roasts for the bean, skip it
        if roasts:
            for roast_id in roasts:
                results.append(ballistics.Roast(roast_id))
        return results

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
