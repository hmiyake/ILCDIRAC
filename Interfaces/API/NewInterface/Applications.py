'''
Created on Jul 28, 2011

This module contains the definition of the different applications that can
be used to create jobs.

Example usage:

>>> from ILCDIRAC.Interfaces.API.Applications import *
>>> from ILCDIRAC.Interfaces.API.Job import Job 
>>> from ILCDIRAC.Interfaces.API.DiracILC import DiracILC
>>> dirac = DiracILC()
>>> job = Job()
>>> ga = GenericApplication()
>>> ga.setScript("myscript.py")
>>> ga.setArguments("some arguments")
>>> ga.setDependency({"mokka":"v0706P08","marlin":"v0111Prod"})
>>> job.append(ga)
>>> dirac.submit(job)

It's also possible to set all the application's properties in the constructor

>>> ga = GenericApplication({'Script':'myscript.py',"Arguments":"some arguments","Dependency":{"mokka":"v0706P08","marlin":"v0111Prod"}})

but this is more an expert's functionality. 

Running:

>>> help(GenericApplication)

prints out all the available methods.

@author: Stephane Poss, Remi Ete, Ching Bon Lam
'''
from ILCDIRAC.Interfaces.API.NewInterface.Application import Application
from ILCDIRAC.Core.Utilities.Processlist              import *
from ILCDIRAC.Core.Utilities.GeneratorModels          import GeneratorModels
from DIRAC.Core.Workflow.Parameter                    import Parameter
from DIRAC.Core.Workflow.Step                         import *
from DIRAC.Core.Workflow.Module                       import *
from DIRAC                                            import S_OK,S_ERROR


import os, types, string


#################################################################
#            Generic Application: use a script in an 
#                 application framework
#################################################################  
class GenericApplication(Application):
  """ Run a script (python or shell) in an application environment. 
  
  Example:
  
  >>> ga = GenericApplication()
  >>> ga.setScript("myscript.py")
  >>> ga.setArguments("some command line arguments")
  >>> ga.setDependency({"root":"5.26"})
  
  """
  def __init__(self, paramdict = None):
    self.script = None
    self.arguments = ''
    self.dependencies = {}
    self._modulename = "ApplicationScript"
    self.appname = self._modulename
    self._moduledescription = 'An Application script module that can execute any provided script in the given project name and version environment'
    ### The Application init has to come last as if not the passed parameters are overwritten by the defaults.
    Application.__init__(self, paramdict)
      
  def setScript(self,script):
    """ Define script to use
    
    @param script: Script to run on. Can be shell or python. Can be local file or LFN.
    @type script: string
    """
    self._checkArgs( {
        'script' : types.StringTypes
      } )
    if os.path.exists(script) or script.lower().count("lfn:"):
      self.inputSB.append(script)
    self.script = script
    return S_OK()
    
  def setArguments(self,args):
    """ Define the arguments of the script (if any)
    
    @param arguments: Arguments to pass to the command line call
    @type arguments: string
    
    """
    self._checkArgs( {
        'args' : types.StringTypes
      } )  
    self.arguments = args
    return S_OK()
      
  def setDependency(self,appdict):
    """ Define list of application you need
    
    >>> app.setDependency({"mokka":"v0706P08","marlin":"v0111Prod"})
    
    @param appdict: Dictionary of applciation to use: {"App":"version"}
    @type appdict: dict
    
    """  
    #check that dict has proper structure
    self._checkArgs( {
        'appdict' : types.DictType
      } )
    
    self.dependencies.update(appdict)
    return S_OK()

  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter(Parameter("script", "", "string", "", "", False, False, "Script to execute"))
    m1.addParameter(Parameter("arguments", "", "string", "", "", False, False, "Arguments to pass to the script"))
    return m1
  
  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue("script",self.script)
    moduleinstance.setValue('arguments',self.arguments)
  
  def _userjobmodules(self,stepdefinition):
    m1 = self._applicationModule()
    stepdefinition.addModule(m1)
    m1i = stepdefinition.createModuleInstance(m1.getType(),stepdefinition.getType())
    self._applicationModuleValues(m1i)
    
    m2 = self._getUserOutputDataModule()
    stepdefinition.addModule(m2)
    stepdefinition.createModuleInstance(m2.getType(),stepdefinition.getType())
    return S_OK()

  def _prodjobmodules(self,stepdefinition):
    m1 = self._applicationModule()
    stepdefinition.addModule(m1)
    m1i = stepdefinition.createModuleInstance(m1.getType(),stepdefinition.getType())
    self._applicationModuleValues(m1i)
    
    m2 = self._getComputeOutputDataListModule()
    self._modules.append(m2)
    stepdefinition.addModule(m2)
    stepdefinition.createModuleInstance(m2.getType(),stepdefinition.getType())
    return S_OK()    

  def _addParametersToStep(self,stepdefinition):
    res = self._addBaseParameters(stepdefinition)
    if not res["OK"]:
      return S_ERROR("Failed to set base parameters")
    return S_OK()
  
  def _setStepParametersValues(self, instance):
    self._setBaseStepParametersValues(instance)
    for depn,depv in self.dependencies.items():
      self.job._addSoftware(depn,depv)
    return S_OK()
      
  def _checkConsistency(self):
    """ Checks that script and dependencies are set.
    """
    if not self.script:
      return S_ERROR("Script not defined")
    elif not self.script.lower().count("lfn:") and not os.path.exists(self.script):
      return S_ERROR("Specified script is not an LFN and was not found on disk")
      
    if not len(self.dependencies):
      return S_ERROR("Dependencies not set")
    return S_OK()  
  
#################################################################
#            GetSRMFile: as its name suggests...
#################################################################  
class GetSRMFile(Application):
  """ Gets a given file from storage directly using srm path.
  
  Usage:
  
  >>> gf = GetSRMFile()
  >>> fdict = {"file":"srm://srm-public.cern.ch/castor/cern.ch/grid/ilc/prod/clic/1tev/Z_uds/gen/0/nobeam_nobrem_0-200.stdhep","site":"CERN-SRM"}
  >>> fdict = str(fdict)
  >>> gf.setFiles(fdict)
  """
  def __init__(self, paramdict = None):
    self._modulename = "GetSRMFile"
    self.appname = self._modulename
    self._moduledescription = "Module to get files directly from Storage"
    Application.__init__(self, paramdict)

  def setFiles(self,fdict):
    """ Specify the files you need
    
    @param fdict: file dictionary: {file:site}, can be also ["{}","{}"] etc.
    @type fdict: dict or list
    """
    kwargs = {"fdict":fdict}
    if not type(fdict) == type("") and not type(fdict) == type([]):
      return self._reportError('Expected string or list of strings for fdict', __name__, **kwargs)
    
    self.filedict = fdict

  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter(Parameter("srmfiles", "", "string", "", "", False, False, "list of files to retrieve"))
    return m1

  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue("srmfiles",self.filedict)  
  
  def _userjobmodules(self,step):
    m1 = self._applicationModule()
    step.addModule(m1)
    m1i = step.createModuleInstance(m1.getType(),step.getType())
    self._applicationModuleValues(m1i)
    return S_OK()

  def _prodjobmodules(self,step):
    self.log.error("This application is not meant to be used in Production context")
    return S_ERROR('Should not use in Production')

  
  def _checkConsistency(self):
    if not self.filedict:
      return S_ERROR("The file list was not defined")
    return S_OK()

  def _addParametersToStep(self,step):
    res = self._addBaseParameters(step)
    if not res["OK"]:
      return S_ERROR("Failed to set base parameters")
    return S_OK()

#################################################################
#            Whizard: First Generator application
#################################################################    
class Whizard(Application):
  """ Runs whizard to generate a given event type
  
  Usage:
  
  >>> wh = Whizard(dirac.getProcessList())
  >>> wh.setProcess("ee_h_mumu")
  >>> wh.setEnergy(500)
  >>> wh.setNbEvts(1000)
  >>> wh.setModel("SM")

  """
  def __init__(self, processlist = None, paramdict = None):    
    
    Application.__init__(self, paramdict)
    self._modulename = 'WhizardAnalysis'
    self._moduledescription = 'Module to run WHIZARD'
    self.parameterdict = {}
    self.appname = 'whizard'
    self.evttype = ''
    self.model = 'sm'  
    self.seed = 0
    self.jobindex = None
    self.steeringparameter = ''
    self.leshouchesfiles = None
    self.generatormodels = GeneratorModels()
    self.datatype = 'gen'
    self.allowedparams = ['PNAME1','PNAME2','POLAB1','POLAB2','USERB1','USERB2','ISRB1','ISRB2','EPAB1','EPAB2','RECOIL','INITIALS','USERSPECTRUM']
    self.parameters = []
    if processlist:
      self.processlist = processlist
    
    
    
  def setEvtType(self,evttype):
    """ Define process
    
    @param process: Process to generate
    """
    self._checkArgs( {
        'evttype' : types.StringTypes
      } )
    self.evttype = evttype

  def setLuminosity(self,lumi):
    """ Define luminosity to generate 
    
    @param lumi: Luminosity to generate. Not available if cross section is not known a priori. Use with care.
    @type lumi: float
    """
    self._checkArgs( {
        'lumi' : types.FloatType
      } )    
    self.lumi = lumi

  def setRandomSeed(self,seed):
    """ Define random seed to use 
    
    @param seed: Seed to use during integration and generation. Default is Job ID.
    @type seed: int
    """
    self._checkArgs( {
        'seed' : types.IntType
      } )

    self.seed = seed
  
  def setParameterDict(self,paramdict):
    """ Parameters for Whizard steering files
    
    @param paramdict: Dictionary of parameters for the whizard templates. Most parameters are set on the fly.
    @type paramdict: dict
    """
    self._checkArgs( {
        'paramdict' : types.DictType
      } )

    self.parameterdict = paramdict
  
  def setModel(self,model):
    """ Define Model
    
    @param model: Model to use for generation. Predefined list available in GeneratorModels class.
    @type model: string
    """  
    self._checkArgs( {
        'model' : types.StringTypes
      } )

    self. model = model
    
  def _checkConsistency(self):
    #must be filled
    if not self.energy :
      print 'Energy set to 0 !'
      
    if not self.nbevts :
      print 'Number of events set to 0 !'
    
    if not self.evttype:
      return S_ERROR("Process not defined")
    
    if not self.processlist:
      return S_ERROR("Process list was not given")
    
    if self.evttype:
      if not self.processlist.existsProcess(self.evttype)['Value']:
        self.logfile.info("Available processes are:")
        self.processlist.printProcesses()
        return S_ERROR('Process does no exists')
      else:
        cspath = self.processlist.getCSPath(self.evttype)
        whiz_file = os.path.basename(cspath)
        self.version = whiz_file.replace(".tar.gz","").replace(".tgz","").replace("whizard","")
        
    if not self.version:
      return S_ERROR('No version found')
      
    if self.model:
      if not self.generatormodels.has_key(self.model):
        return S_ERROR("Unknown model %s"%self.model)
   
    if not self.steeringfile :
      return S_ERROR('Steering File not given')
   
    if not self.outputFile :
      return S_ERROR('Output File not set')
   
    for key in self.parameterdict.keys():
      if not key in self.allowedparams:
        return S_ERROR("Unknown parameter %s"%key)

    if not self.parameterdict.has_key('PNAME1'):
      print "Assuming incoming beam 1 to be electrons"
      self.parameters.append('PNAME1=e1')
    else:
      self.parameters.append("PNAME1=%s" %self.parameterdict["PNAME1"] )
      
    if not self.parameterdict.has_key('PNAME2'):
      print "Assuming incoming beam 2 to be positrons"
      self.parameters.append('PNAME2=E1')
    else:
      self.parameters.append("PNAME2=%s" %self.parameterdict["PNAME2"] )
       
    if not self.parameterdict.has_key('POLAB1'):
      print "Assuming no polarization for beam 1"
      self.parameters.append('POLAB1=0.0 0.0')
    else:
      self.parameters.append("POLAR1=%s" %self.parameterdict["POLAR1"] )
        
    if not self.parameterdict.has_key('POLAB2'):
      print "Assuming no polarization for beam 2"
      self.parameters.append('POLAB2=0.0 0.0')
    else:
      self.parameters.append("POLAR2=%s" %self.parameterdict["POLAR2"] )
        
    if not self.parameterdict.has_key('USERB1'):
      print "Will put beam spectrum to True for beam 1"
      self.parameters.append('USERB1=T')
    else:
      self.parameters.append("USERB1=%s" %self.parameterdict["USERB1"] )
        
    if not self.parameterdict.has_key('USERB2'):
      print "Will put beam spectrum to True for beam 2"
      self.parameters.append('USERB2=T')
    else:
      self.parameters.append("USERB2=%s" %self.parameterdict["USERB2"] )
        
    if not self.parameterdict.has_key('ISRB1'):
      print "Will put ISR to True for beam 1"
      self.parameters.append('ISRB1=T')
    else:
      self.parameters.append("ISRB1=%s" %self.parameterdict["ISRB1"] )
        
    if not self.parameterdict.has_key('ISRB2'):
      print "Will put ISR to True for beam 2"
      self.parameters.append('ISRB2=T')
    else:
      self.parameters.append("ISRB2=%s" %self.parameterdict["ISRB2"] )
        
    if not self.parameterdict.has_key('EPAB1'):
      print "Will put EPA to False for beam 1"
      self.parameters.append('EPAB1=F')
    else:
      self.parameters.append("EPAB1=%s" %self.parameterdict["EPAB1"] )
        
    if not self.parameterdict.has_key('EPAB2'):
      print "Will put EPA to False for beam 2"
      self.parameters.append('EPAB2=F')
    else:
      self.parameters.append("EPAB2=%s" %self.parameterdict["EPAB2"] )
       
    if not self.parameterdict.has_key('RECOIL'):
      print "Will set Beam_recoil to False"
      self.parameters.append('RECOIL=F')
    else:
      self.parameters.append("RECOIL=%s" %self.parameterdict["RECOIL"] )
        
    if not self.parameterdict.has_key('INITIALS'):
      print "Will set keep_initials to False"
      self.parameters.append('INITIALS=F')
    else:
      self.parameters.append("INITIALS=%s" %self.parameterdict["INITIALS"] )
        
    if not self.parameterdict.has_key('USERSPECTRUM'):
      print "Will set USER_spectrum_on to +-11"
      self.parameters.append('USERSPECTRUM=11')
    else:
      self.parameters.append("USERSPECTRUM=%s" %self.parameterdict["USERSPECTRUM"] )
    
    self.parameters = string.join(self.parameters,";")
      
    return S_OK()  

  def _applicationModule(self):
    #must be filled
    
    md1 = self._createModuleDefinition()
    md1.addParameter(Parameter("evttype",     "", "string", "", "", False, False, "Process to generate"))
    md1.addParameter(Parameter("RandomSeed",  "",  "float", "", "", False, False, "Random seed for the generator"))
    md1.addParameter(Parameter("Lumi",        "",  "float", "", "", False, False, "Luminosity of beam"))
    md1.addParameter(Parameter("SusyModel",   "", "string", "", "", False, False, "Model for generation"))
    md1.addParameter(Parameter("InputFile",   "", "string", "", "", False, False, "Steering file"))
    md1.addParameter(Parameter("JobIndex",    "", "string", "", "", False, False, "Job Index"))
    md1.addParameter(Parameter("parameters",  "", "string", "", "", False, False, "Specific steering parameters"))
    
    return md1
  
  def _applicationModuleValues(self,moduleinstance):

    moduleinstance.setValue("evttype",      self.evttype)
    moduleinstance.setValue("RandomSeed",   self.seed)
    moduleinstance.setValue("Lumi",self.lumi)
    moduleinstance.setValue("SusyModel",self.model)
    moduleinstance.setValue("InputFile",self.steeringfile)
    moduleinstance.setValue("JobIndex",self.jobindex)
    moduleinstance.setValue("parameters",self.steeringparameters)
    
  def _userjobmodules(self,stepdefinition):
    md1 = self._applicationModule()
    stepdefinition.addModule(md1)
    mi1 = stepdefinition.createModuleInstance(md1.getType(),stepdefinition.getType())
    self._applicationModuleValues(mi1)
    
    md2 = self._getUserOutputDataModule()
    stepdefinition.addModule(md2)
    stepdefinition.createModuleInstance(md2.getType(),stepdefinition.getType())
    return S_OK()

  def _prodjobmodules(self,stepdefinition):
    md1 = self._applicationModule()
    stepdefinition.addModule(md1)
    m1i = stepdefinition.createModuleInstance(md1.getType(),stepdefinition.getType())
    self._applicationModuleValues(m1i)
    
    md2 = self._getComputeOutputDataListModule()
    stepdefinition.addModule(md2)
    stepdefinition.createModuleInstance(md2.getType(),stepdefinition.getType())
    return S_OK()

  def _addParametersToStep(self,stepdefinition): pass 
   # must be filled

    
  def _setStepParametersValues(self,stepinstance): pass  # must be filled
    
    
  
#################################################################
#            PYTHIA: Second Generator application
#################################################################    
class Pythia(Application):
  """ Call pythia.
  
  Usage:
  
  >>> py = Pythia()
  >>> py.setVersion("tt_500gev_V2")
  >>> py.setNbEvts(50)

  """
  def __init__(self,paramdict = None):
    self.appname = 'pythia'
    self._modulename = 'PythiaAnalysis'
    self._moduledescription = 'Module to run PYTHIA'
    Application.__init__(self,paramdict)

  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    return m1  

  def _userjobmodules(self,step):
    m1 = self._applicationModule()
    step.addModule(m1)
    m1i = step.createModuleInstance(m1.getType(),step.getType())
    self._applicationModuleValues(m1i)
    
    m2 = self._getUserOutputDataModule()
    step.addModule(m2)
    step.createModuleInstance(m2.getType(),step.getType())
    return S_OK()

  def _prodjobmodules(self,step):
    m1 = self._applicationModule()
    step.addModule(m1)
    m1i = step.createModuleInstance(m1.getType(),step.getType())
    self._applicationModuleValues(m1i)
    
    m2 = self._getComputeOutputDataListModule()
    step.addModule(m2)
    step.createModuleInstance(m2.getType(),step.getType())
    return S_OK()
      
  def _checkConsistency(self):
    if not self.version:
      return S_ERROR("Version not specified")
    
    if not self.nbevts:
      return S_ERROR("Number of events to generate not defined")

    return S_OK()
  
##########################################################################
#            StdhepCut: apply generator level cuts after pythia or whizard
##########################################################################
class StdhepCut(Application): 
  """ Call stdhep cut after whizard of pythia
  
  Usage:
  
  >>> py = Pythia()
  >>> cut = StdhepCut()
  >>> cut.getInputFromApp(py)
  >>> cut.setSteeringFile("mycut.cfg")
  >>> cut setMaxNbEvts(10)
  >>> cut.setNbEvtsPerFile(10)
  
  """
  def __init__(self, paramdict = None):
    self.appname = 'stdhepcut'
    self._modulename = 'StdHepCut'
    self._moduledescription = 'Module to cut on Generator (Whizard of PYTHIA)'
    
    self.maxevts = 0
    self.nbevtsperfile = 0
    Application.__init__(self,paramdict)

  def setMaxNbEvts(self,nbevts):
    """ Max number of events to keep in each file
    
    @param nbevts: Maximum number of events to read from input file
    @type nbevts: int
    """
    self._checkArgs( {
        'nbevts' : types.IntType
      } )
    self.maxevts = nbevts
    
  def setNbEvtsPerFile(self,nbevts):
    """ Number of events per file
    
    @param nbevts: Number of evetns to keep in each file.
    @type nbevts: int
    """
    self._checkArgs( {
        'nbevts' : types.IntType
      } )
    self.nbevtsperfile = nbevts  

  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter(Parameter("MaxNbEvts", 0, "int", "", "", False, False, "Number of evetns to read"))
    return m1

  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue("MaxNbEvts",self.maxevts)

  def _userjobmodules(self,step):
    m1 = self._applicationModule()
    step.addModule(m1)
    m1i = step.createModuleInstance(m1.getType(),step.getType())
    self._applicationModuleValues(m1i)
    
    m2 = self._getUserOutputDataModule()
    step.addModule(m2)
    step.createModuleInstance(m2.getType(),step.getType())
    return S_OK()

  def _prodjobmodules(self,step):
    m1 = self._applicationModule()
    step.addModule(m1)
    m1i = step.createModuleInstance(m1.getType(),step.getType())
    self._applicationModuleValues(m1i)
    
    m2 = self._getComputeOutputDataListModule()
    step.addModule(m2)
    step.createModuleInstance(m2.getType(),step.getType())
    return S_OK()


  def _checkConsistency(self):
    if not self.steeringfile:
      return S_ERROR("Cut file not specified")
    elif not self.steeringfile.lower().count("lfn:") and not os.path.exists(self.steeringfile):
      return S_ERROR("Cut file not found locally and is not an LFN")
    
    if not self.maxevts:
      return S_ERROR("You did not specify how many events you need to keep per file (MaxNbEvts)")
    
    res = self._checkRequiredApp() ##Check that job order is correct
    if not res['OK']:
      return res
    
    return S_OK()
  
  def _resolveLinkedParameters(self,stepinstance):
    if self.inputappstep:
      res = stepinstance.setLink("InputFile",self.inputappstep.getType(),"OutputFile")
      if not res:
        return S_ERROR("Failed to resolve InputFile from %s's OutputFile, possibly not defined."%self.inputappstep.getName())
    return S_OK()  
    