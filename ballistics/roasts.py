"""
Roasts.
Loading roast data from the Bullet data, and outputting it in various formats
"""
from dataclasses import dataclass
import json
import textwrap
from pathlib import Path
from pprint import pprint
from typing import List, Dict
from datetime import datetime, timedelta
from PIL import Image, ImageFont, ImageDraw
from qrcode import QRCode

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
    urlSite: str = ''
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

        # local and remote URLs
        self.urlSite = f"/roasts/{self.batch}"
        self.url = config.baseUrl + self.urlSite

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

    def to_markdown(self) -> Path:
        """
        Output the Roast as a markdown file.
        :return: Path of the output file
        """
        # output_beans_dir = config.outputDir / "beans"
        output_roast_dir = config.outputDir / "roasts"
        if not output_roast_dir.exists():
            output_roast_dir.mkdir(parents=True)
        output_file = output_roast_dir / f"{self.batch}.md"
        with open(output_file, 'w') as roastf:
            # write out the frontmatter
            roastf.write("---\n")
            roastf.write(f"title: {self.name}\n")
            roastf.write(f"batch: {self.batch}\n")
            roastf.write(f"origin: {self.country}\n")
            roastf.write(f"roastedDate: {self.roastDate}\n")
            roastf.write(f"bestDate: {self.roastBestDate[1]}\n")
            roastf.write("type: roast\n")
            roastf.write(f"path: {self.urlSite}\n")
            roastf.write(f"beanPath: {self.bean.urlSite}\n")
            roastf.write(f"beanName: {self.bean.name}\n")
            roastf.write(f"region: {self.region}\n")
            roastf.write(f"rwUrl: https://roast.world/my/roasts/{self.roastId}\n")
            label = f"images/{self.batch}"
            if (config.outputDir / f"roasts/{label}.png").exists():
                # shit gets dicy if this doesn't exist
                roastf.write(f"labelPic: {label}.png\n")
            if (config.outputDir / f"roasts/{label}-profile.png").exists():
                # queries fail if NO roasts have a profile graph
                roastf.write(f"profilePic: {label}-profile.png\n")
            profile = f"images/{self.batch}-profile.png"
            roastf.write("tags:\n")
            roastf.write(" - roastedby\n")
            roastf.write(" - roast\n")
            if self.isDecaf:
                roastf.write(" - decaf\n")
            if self.isOrganic:
                roastf.write(" - organic\n")
            if self.bean.isForEspresso:
                roastf.write(" - espresso\n")
            roastf.write("---\n")
            # write out the semi-structured content
            # TODO: add in details
            roastf.write("### Roast details\n\n")
            if self.roastLevel:
                roastf.write(f"*Roast level:* {self.roastLevel}\n\n")
            roastf.write(f"*Weight in:* {self.weightGreen}g\n\n")
            roastf.write(f"*Weight out:* {self.weightRoasted}g\n\n")
            roastf.write(f"*Roast time:* {(self.roastTimeTotal / 60):.1f} minutes\n\n")
            roastf.write(f"*Development:* {self.roastDVPct:.1f}%\n\n")
            roastf.write("\n")
        roastf.close()
        return output_file

    def generate_labels(self):
        # go through each label and build the label
        # TODO: make this iterable, with some enhanced label layout props?
        # start with the large label
        label = config.labels['large']
        large_label_width = label['width']
        large_label_height = label['height']
        label_size = (large_label_width, large_label_height)  # 2" x 3"
        img = Image.new('RGB', size=(large_label_width, large_label_height), color='white')

        # generate QR code
        qr = QRCode(box_size=10, border=1, version=1)
        qr.add_data(self.url)
        qrimg = qr.make_image()
        img.paste(qrimg, (25, 130))

        # if it's decaf, add a decal to the QR code
        if self.isDecaf:
            decafdecal = Image.new("RGB", (115, 50), "white")
            decafdecalimg = ImageDraw.Draw(decafdecal)
            decafdecalimg.text((4, 6), "DECAF", font=label['font_title'], fill="#FF7F50")
            decafdecalimg.line(((0, 2), (120, 2)), "#FF7F50", 3)
            decafdecalimg.line(((0, 48), (120, 48)), "#FF7F50", 3)
            img.paste(decafdecal, (140, 260))

        # add text to the label
        canvas = ImageDraw.Draw(img)
        # batch number, rotated 90 degrees
        bimg = Image.new("L", (100, 100), 255)
        bnumimg = ImageDraw.Draw(bimg)
        bnumimg.text((0, 0), str(self.batch), font=label['font_batch'], fill=0)
        bnumimg.line(((0, 52), (85, 52)), 0, 4)
        bimg = bimg.rotate(90, expand=False, fillcolor=0)
        img.paste(bimg, (8, 10))
        # roast name
        wrapped_rname = '\n'.join(textwrap.wrap(self.name, label['line_length'])[:label['line_count']])
        canvas.text((70, 18), wrapped_rname, font=label['font_title'], fill=(0, 0, 0))
        # origin
        # FIXME: shrink font size if the text is longer than the space? can we know how long the text would be?
        canvas.text((35, large_label_height - 140), f"Origin: {self.country}", font=label['font_origin'], fill=(0, 0, 0))
        # dates
        canvas.text((110, large_label_height - 72), f"Roasted on: {self.roastDate.strftime('%a %D')}", font=label['font_small'], fill=(0, 0, 0))
        canvas.text((110, large_label_height - 40), f"Best: {self.roastBestDate[0].strftime('%D')} to {self.roastBestDate[1].strftime('%D')}",
                    font=label['font_small'], fill=(0, 0, 0))

        # save the image label file, in an iCloud location, so that I can print them as needed
        img_file = f"{self.batch}.png"
        img_loc = config.outputDir / "roasts/images"
        if not img_loc.exists():
            img_loc.mkdir(parents=True)
        img.save(img_loc / img_file)
        # TODO: small label
        return

    def generate_profile_graph(self):
        pass

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
