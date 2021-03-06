#!/usr/bin/env python
"""
Create a list of lfns form a repository file created during job submission

Options:

  -r repoLocation       Path to repository file

:since: Apr 22, 2010
:author: Stephane Poss
"""
__RCSID__ = "$Id$"

from DIRAC.Core.Base import Script
from DIRAC import exit as dexit
from DIRAC import S_OK
class _Params(object):
  """dummy"""
  def __init__(self):
    self.repo = ''
  def setRepo(self, optionVal):
    self.repo = optionVal
    return S_OK()
  def registerSwitches(self):
    Script.registerSwitch('r:', 'repository=', 'Path to repository file', self.setRepo)
    Script.setUsageMessage('\n'.join( [ __doc__.split( '\n' )[1],
                                        '\nUsage:',
                                        '  %s [option|cfgfile] ...\n' % Script.scriptName ] ) )
    
def _createLFNList():
  """create the LFnList"""
  cliparams = _Params()
  cliparams.registerSwitches()
  Script.parseCommandLine( ignoreErrors = False )
  from DIRAC import gLogger
  
  repoLocation =  cliparams.repo
  if not repoLocation:
    Script.showHelp()
    dexit(2)
  from ILCDIRAC.Interfaces.API.DiracILC import DiracILC
  dirac = DiracILC(True, repoLocation)
  
  dirac.monitorRepository(False)
  lfns = []
  lfns = dirac.retrieveRepositoryOutputDataLFNs()
  gLogger.notice("lfnlist=[")
  for lfn in lfns :
    gLogger.notice('"LFN:%s",' % lfn)
  gLogger.notice("]")
  dexit(0)

if __name__=="__main__":
  _createLFNList()
