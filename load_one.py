"""
This script is intended to be run in the interactive shell, load up the roastId listed up the top
and leave the shell interactive and open for querying and exploration.

Otherwise, main() should be importable from an interactive shell, with the roastId as an argument
"""
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

# def loadroast(roast_id: int) -> List[object]:
#     """
#     Loads the named roast and returns the JSON object
#     :param roast_id:
#     :return:
#     """
#     # scan through the roast_dir
#     for file in roasts_dir.glob('*'):
#         # print(f"Found file {file}")
#         with open(file) as json_file:
#             rf = json.load(json_file)
#
#         # clean up and prep the data
#         if rf.get('isFork') == 1:
#             # This flag indicates a saved roast or other roast brought into RoasTime that wasn't actually roasted
#             continue
#         roastname = rf.get('roastName')
#         if not roastname.startswith(str(roast_id)):
#             # not our roast
#             continue
#
#         # load the bean as well
#         rbeanid = rf.get('beanId')
#         with open(beans_dir / rbeanid) as json_file:
#             bf = json.load(json_file)
#
#         return [rf, bf]


if __name__ == '__main__':
    # ballistics.config.init_env()
    roastd = ballistics.find_roast_by(selected_roast)
    roast = ballistics.Roast(roastd.get(list(roastd.keys())[0])[0])
    roastj = roast.raw
    # this removes the loooooong arrays before printing them out, to aid in human readability
    roastj.pop('actions')
    roastj.pop('beanDerivative')
    roastj.pop('beanTemperature')
    roastj.pop('drumTemperature')
    roastj.pop('exitTemperature')
    roastj.pop('ibtsDerivative')
    pprint(roastj)
