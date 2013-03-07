'''
Created on Feb 10, 2012

@author: Stephane Poss
'''

from DIRAC import gConfig, S_OK, S_ERROR
from ILCDIRAC.Core.Utilities.CombinedSoftwareInstallation  import getSoftwareFolder

def getSteeringFileDirName(systemConfig, application, applicationVersion):
  """ Locate the path of the steering file directory assigned to the specified applciation
  """
  version = gConfig.getValue('/Operations/AvailableTarBalls/%s/%s/%s/Dependencies/steeringfiles/version' % (systemConfig, 
                                                                                                            application,
                                                                                                            applicationVersion), '')
  if not version:
    return S_ERROR("Could not find attached SteeringFile version")
  TarBall = gConfig.getValue('/Operations/AvailableTarBalls/%s/steeringfiles/%s/TarBall' % (systemConfig, version), '')
  if not TarBall:
    return S_ERROR("Could not find tar ball for SteeringFile")
  mydir = TarBall.replace(".tgz", "").replace(".tar.gz", "")
  res = getSoftwareFolder(mydir)
  if not res['OK']:
    return res
  mySoftDir = res['Value']
  return S_OK(mySoftDir)