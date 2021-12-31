"""
Utility functions and classes that serve the PlexPlay module
"""
import os
import datetime
import frontmatter

from typing import List, Union
from pathlib import Path


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
