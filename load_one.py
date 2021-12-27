"""
This script is intended to be run in the interactive shell, load up the roastId listed up the top
and leave the shell interactive and open for querying and exploration.

Otherwise, main() should be importable from an interactive shell, with the roastId as an argument
"""
from typing import Union

import ballistics
from pprint import pprint


"""
Config
This whole section should be a config module/file
"""
# which roast to load
selected_roast = '322'
"""
/Config
"""


def load_first_matching(partial: str) -> Union[ballistics.Roast, None]:
    """
    Loads the first matching roast that contains the batch number.
    If you use the (nominally unique) bach number, it will reliably return the correct roast.
    :param partial: intended to be the batch number
    :return:
    """
    if roast_dict := ballistics.find_roast_by(partial):
        return ballistics.Roast(roast_dict.get(list(roast_dict.keys())[0])[0])
    else:
        return None


if __name__ == '__main__':
    # ballistics.config.init_env()
    # roastd = ballistics.find_roast_by(selected_roast)
    # roast = ballistics.Roast(roastd.get(list(roastd.keys())[0])[0])
    roast = load_first_matching(selected_roast)
    roastj = roast.raw
    # this removes the loooooong arrays before printing them out, to aid in human readability
    roastj.pop('actions')
    roastj.pop('beanDerivative')
    roastj.pop('beanTemperature')
    roastj.pop('drumTemperature')
    roastj.pop('exitTemperature')
    roastj.pop('ibtsDerivative')
    pprint(roastj)
