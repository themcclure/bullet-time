"""
Utility functions and classes that serve the PlexPlay module
"""
import os
import datetime
import textwrap

import frontmatter

from typing import List, Union
from pathlib import Path

from PIL import Image, ImageFont, ImageDraw
from qrcode import QRCode


def generate_large_label(label_conf: dict, batch: str, name: str, url: str, is_decaf: bool,
                         roast_date: datetime.datetime, start_date: datetime.datetime, end_date: datetime.datetime,
                         country: str = "Blend/Unknown") -> Image:
    # label = config.labels['large']
    large_label_width = label_conf['width']
    large_label_height = label_conf['height']
    label_size = (large_label_width, large_label_height)  # 2" x 3"
    img = Image.new('RGB', size=(large_label_width, large_label_height), color='white')

    # generate QR code
    qr = QRCode(box_size=9, border=1, version=1)
    qr.add_data(url)
    qrimg = qr.make_image()
    img.paste(qrimg, (25, 130))

    # if it's decaf, add a decal to the QR code
    if is_decaf:
        decafdecal = Image.new("RGB", (115, 50), "white")
        decafdecalimg = ImageDraw.Draw(decafdecal)
        decafdecalimg.text((4, 6), "DECAF", font=label_conf['font_title'], fill="#FF7F50")
        decafdecalimg.line(((0, 2), (120, 2)), "#FF7F50", 3)
        decafdecalimg.line(((0, 48), (120, 48)), "#FF7F50", 3)
        img.paste(decafdecal, (140, 260))

    # add text to the label
    canvas = ImageDraw.Draw(img)
    # TODO: reduce font size by 3/len(batch) so that it will fit arbitrary length batch numbers
    # batch number, rotated 90 degrees
    bimg = Image.new("L", (100, 100), 255)
    bnumimg = ImageDraw.Draw(bimg)
    bnumimg.text((0, 0), batch, font=label_conf['font_batch'], fill=0)
    bnumimg.line(((0, 52), (85, 52)), 0, 4)
    bimg = bimg.rotate(90, expand=False, fillcolor=0)
    img.paste(bimg, (8, 10))
    # roast name
    wrapped_rname = '\n'.join(textwrap.wrap(name, label_conf['line_length'])[:label_conf['line_count']])
    canvas.text((70, 18), wrapped_rname, font=label_conf['font_title'], fill=(0, 0, 0))
    # origin
    # FIXME: shrink font size if the text is longer than the space? can we know how long the text would be?
    canvas.text((35, large_label_height - 140), f"Origin: {country}", font=label_conf['font_origin'], fill=(0, 0, 0))
    # dates
    canvas.text((110, large_label_height - 72), f"Roasted on: {roast_date.strftime('%a %D')}",
                font=label_conf['font_small'], fill=(0, 0, 0))
    canvas.text((110, large_label_height - 40),
                f"Best: {start_date.strftime('%D')} to {end_date.strftime('%D')}",
                font=label_conf['font_small'], fill=(0, 0, 0))
    return img


def merge_markdown(original: Path, annotation: Path) -> str:
    """
    Take two markdown files and annotate the original.
    Annotation goes like this:
        - merge the original with the frontmatter from the annotation version
        - insert the main body of the annotation version in between the heading (first line) of the original and
          the rest of the content
    Return a multi-line string ready to be saved to file
    (Should the save to file be part of this function?)
    :param original: Path to the "original" markdown file
    :param annotation Path to the "annotation" markdown file - this needs to be a Path but the file is ignored if it
        doesn't exist
    :return: merged string
    """
    orig_file = frontmatter.load(original)
    meta = orig_file.metadata
    content = orig_file.content.split('\n')
    if annotation.exists():
        annotation_file = frontmatter.load(annotation)
        # merge frontmatter:
        meta.update(annotation_file.metadata)

        # merge content (assuming top row is header, keep it, then insert on row 2 all the override content,
        # surrounded by blank lines - then the rest of the original content
        content[1:1] = '\n'
        content[1:1] = annotation_file.content.split('\n')
        content[1:1] = '\n'

    # combine into one big happy markdown file
    results = '---\n'
    for item in meta.items():
        results += f"{item[0]}: {item[1]}\n"
    results += '---\n'
    results += '\n'.join(content)
    return results


def get_from_env(name: str) -> Union[int, str, List, None]:
    """
    Fetches information from the environment and returns an appropriately typed object in retrun.

    If the env variable:
        - result contains a pipe (|) then it will be split on the pipe and returned as a list.
        - result isnumeric() then it is returned as a number
        - name contains DIR or FILE, then it will be returned as a Path()

    :param name: the name of item to get from the environment
    :return: value from the environment, cast into int, str, or list (as needed)
    """
    item = os.getenv(name)
    # if it's empty, return None
    if item is None:
        return
    if '|' in item:
        # if it's supposed to be a list, turn it into one. Also, ConfigParser changes \n to \\n, this changes it back
        item = [x.replace('\\n', '\n') for x in item.split('|') if x != '']
        if '::' in item:  # then make a dict of lists
            item = {i[0]: i[1:] for i in (x.split("::") for x in item if '::' in x)}
        elif ':' in item:  # else just make a dict
            item = {i[0]: i[1:] for i in (x.split(":") for x in item if ':' in x)}
    elif item.isnumeric():
        # if it's a number, return it as an int
        item = int(item)
    elif 'FILE' in name or 'DIR' in name:
        # If it has file or dir in its name, then we treat it as a file or a directory and return a Pathlib object
        item = Path(item)
    return item


class Stopwatch(object):
    """
    Simple class to measure and return times between "clicks".
    Stopwatch.start() resets the timer to now
    Stopwatch.click() sets the "last timing point" to now
    Stopwatch.time() returns a string of the time between now and the last recorded timing point (as does __repr__())
    Stopwatch.stop() sets the "final timing point" to be the start time, so time/__repr__() returns the total time
    Stopwatch.avg() returns the average time from start() to now, divided by the number of clicks
    """
    _start_time = None
    _last_time = None
    _stop_time = None
    _click_count = 0

    def __init__(self):
        self._last_time = datetime.datetime.now()
        self._start_time = self._last_time
        self._stop_time = None
        self._click_count = 1

    def __repr__(self):
        return f"{self.time():.2f}"

    def start(self):
        self._start_time = datetime.datetime.now()
        self._last_time = self._start_time
        self._stop_time = None
        return 0

    def click(self):
        preclick_time = self.time()
        if self._stop_time is None:
            self._click_count += 1
            self._last_time = datetime.datetime.now()
        return preclick_time

    def stop(self):
        if self._stop_time is None:
            self._stop_time = datetime.datetime.now()
            self._last_time = self._start_time
        return self.time()

    def time(self, running_total=False):
        """
        Returns the time in seconds since the last click, or from the beginning if running is True.
        If the clock has stopped, then it measures until the stop time, otherwise it measures from now.
        :param running_total: if True, returns a running total of time since start()
        :return: number of seconds
        """
        if running_total:
            # measure the time since start()
            start_time = self._start_time
        else:
            # measure the time since the last click()
            start_time = self._last_time
        if self._stop_time is None:
            # clock is still running, so measure until now()
            stop_time = datetime.datetime.now()
        else:
            # clock has stopped running, so measure until stop()
            stop_time = self._stop_time
        duration = stop_time - start_time
        return duration.total_seconds()

    def avg(self, full=False):
        """
        Returns the average time from start() to now, divided by the number of clicks
        :param full: if True, then it returns a string with more full info in it, otherwise it returns the raw float
        :return: raw average number of seconds (float), or a string with full information in it
        """
        if full:
            return f"Total time: {self.time(running_total=True):.2f}, average time: " \
                   f"{self.time(running_total=True) / self._click_count:.2f}, over {self._click_count} clicks."
        else:
            return self.time(running_total=True) / self._click_count
