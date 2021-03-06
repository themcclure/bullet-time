"""
Module section for setting, holding and providing the configuration items for this module.
"""
import dataclasses
import logging
import os
from dataclasses import dataclass
# from typing import List
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw
from qrcode import QRCode

from .utils import get_from_env


@dataclass
class BallisticsConfig:
    name: str
    src_dir: Path = Path('.')
    roasts_dir: Path = Path('.')
    beans_dir: Path = Path('.')
    load_only: bool = False
    initialized: bool = False
    log_level: str = ''
    log_file: str = ''
    log_format: str = ''
    logger: logging.Logger = None
    roastLevels = {
        0: 'Very Light (Cinnamon)',
        1: 'Light (City)',
        2: 'Medium Light (City +)',
        3: 'Medium (Full City)',
        4: 'Medium Dark (Full City+)',
        5: 'Dark (Vienna)',
        6: 'Dark (French)',
    }
    bestDaysStart: int = 3
    bestDaysEnd: int = 21 + bestDaysStart
    baseUrl: str = 'https://roastedby.themcclure.com/'
    outputDir: Path = Path('.')
    publishDir: Path = Path('.')
    annotationsDir: Path = None
    labels: dict = None

    def init_env(self, name: str = None, force: bool = False) -> None:
        """
        Initalizes the configuration with defaults, overridden by the runtime environment.
        This is a one time deal - repeated attempts to initialize the environment will fail, unless explicitly forced
        :param name: descriptive name of the configuration (best as the Plex friendly name)
        :param force: forces reinitialization
        """
        # re-initialization guard
        if self.initialized and not force:
            self.logger.debug('BallisticsConfig was already initilized, so re-initialization was skipped')
            return

        # initialization section
        load_dotenv()

        # logging section
        self.log_level = get_from_env('BALL_LOG_LEVEL') or 'DEBUG'
        self.log_file = get_from_env('BALL_LOG_FILE') or 'logfile.log'
        self.log_format = get_from_env('BALL_LOG_FORMAT') or '%(asctime)s:%(levelname)-3.3s:%(funcName)-16.16s:%(lineno)-.3d: %(message)s'
        self.logger = self.init_logging()

        # roaster specific section
        self.src_dir = Path(f"~{os.getenv('BALL_USER', '')}").expanduser() / os.getenv('BALL_HOME_DIR', '')
        self.roasts_dir = self.src_dir / 'roasts'
        self.beans_dir = self.src_dir / 'beans'

        # output, website, and label section
        self.outputDir = (Path(f"~{os.getenv('BULLET_USER', '')}").expanduser() / os.getenv('BALL_OUTPUT_DIR', '')) or self.outputDir
        self.annotationsDir = (Path(f"~{os.getenv('BULLET_USER', '')}").expanduser() / os.getenv('BALL_ANNOTATIONS_DIR', '')) or self.annotationsDir
        self.publishDir = (Path(f"~{os.getenv('BULLET_USER', '')}").expanduser() / os.getenv('BALL_PUBLISH_DIR', '')) or self.publishDir
        self.baseUrl = os.getenv('BALL_BASE_URL', '') or self.baseUrl
        self.bestDaysStart = os.getenv('BALL_MIN_DAYS', '') or self.bestDaysStart
        self.bestDaysEnd = (os.getenv('BALL_MIN_DAYS', '') or self.bestDaysEnd) + self.bestDaysStart
        self.labels = dict()
        self.labels['large'] = {
            'width': 406,  # 2", @ 203 DPI
            'height': 609,  # 3", @ 203 DPI
            'font_batch': ImageFont.truetype('Menlo', 48),
            'font_title': ImageFont.truetype('Menlo', 36),
            'font_origin': ImageFont.truetype('Arial', 38),
            'font_small': ImageFont.truetype('Arial', 24),
            'line_length': 18,
            'line_count': 2,

        }

        # general utility section
        if name:
            self.name = name
        self.load_only = bool(get_from_env('BALL_LOAD_ONLY'))
        self.initialized = True
        self.logger.debug('BallisticsConfig initilized!')

    def init_logging(self) -> logging.Logger:
        # create logger
        logger = logging.getLogger('Ballistics')
        logger.setLevel('DEBUG')

        # file logging
        file_logger = logging.FileHandler(self.log_file)
        file_logger.setFormatter(logging.Formatter(self.log_format))
        file_logger.setLevel(self.log_level)
        logger.addHandler(file_logger)

        # console logging
        console_logger = logging.StreamHandler()
        console_logger.setFormatter(logging.Formatter(self.log_format))
        console_logger.setLevel('ERROR')
        logger.addHandler(console_logger)

        return logger


config = BallisticsConfig('Config')
