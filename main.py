from thermal_profile import *
from plotting import *

def buildProfile(path):
    profile = TempProfile(path, 40)
    profile.buildDataframe()
    print('There are ' + str(len(profile.channels)) + ' thermocouples.' )
    profile.buildEdges()
    return profile


##### Path and Profile
path = r"\\Chfile1\ecs_landrive\Automotive_Lighting\LED\P552 MCA Headlamp\P552 MCA Aux\ADVPR\PV Aux\TL D\Agilent Temperature Data\20000131_062031968\dat00001.csv"
profile = buildProfile(path)
## -----------------------------------------------------------------------------
