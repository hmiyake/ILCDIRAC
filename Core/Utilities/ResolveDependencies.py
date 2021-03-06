'''
Set of functions used to resolve the applications' dependencies, looking into the CS

Works recursively

:since: Apr 26, 2010
:author: Stephane Poss
'''

__RCSID__ = "$Id$"

from DIRAC import gLogger
from DIRAC.ConfigurationSystem.Client.Helpers.Operations            import Operations

def resolveDeps(sysconfig, appli, appversion):
  """ Resolve the dependencies
  
  :param string sysconfig: system configuration
  :param string appli: application name
  :param string appversion: application version
  :return: list of dictionaries
  """
  log = gLogger.getSubLogger("resolveDeps")
  ops = Operations()
  deps = ops.getSections('/AvailableTarBalls/%s/%s/%s/Dependencies' % (sysconfig, appli, 
                                                                       appversion), '')
  depsarray = []
  if deps['OK']:
    for dep in deps['Value']:
      vers = ops.getValue('/AvailableTarBalls/%s/%s/%s/Dependencies/%s/version' % (sysconfig, appli, 
                                                                                   appversion, dep), '')
      depvers = ''
      if vers:
        depvers = vers
      else:
        log.error("Retrieving dependency version for %s failed, skipping to next !" % (dep))
        continue
      log.verbose("Found dependency %s %s" % (dep, depvers))
      depdict = {}
      depdict["app"] = dep
      depdict["version"] = depvers
      depsarray.append(depdict)
      ##resolve recursive dependencies
      depsofdeps = resolveDeps(sysconfig, dep, depvers)
      depsarray.extend(depsofdeps)
  else:
    log.verbose("Could not find any dependency for %s %s, ignoring" % (appli, appversion))
  return depsarray
