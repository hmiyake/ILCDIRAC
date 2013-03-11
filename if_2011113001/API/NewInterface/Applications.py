"""
This module contains the definition of the different applications that can
be used to create jobs.

Example usage:

>>> from ILCDIRAC.Interfaces.API.NewInterface.Applications import *
>>> from ILCDIRAC.Interfaces.API.NewInterface.UserJob import * 
>>> from ILCDIRAC.Interfaces.API.DiracILC import DiracILC
>>> dirac = DiracILC()
>>> job = UserJob()
>>> ga = GenericApplication()
>>> ga.setScript("myscript.py")
>>> ga.setArguments("some arguments")
>>> ga.setDependency({"mokka":"v0706P08","marlin":"v0111Prod"})
>>> job.append(ga)
>>> dirac.submit(job)

It's also possible to set all the application's properties in the constructor

>>> ga = GenericApplication({"Script":"myscript.py","Arguments":"some arguments","Dependency":{"mokka":"v0706P08","marlin":"v0111Prod"}})

but this is more an expert's functionality. 

Running:

>>> help(GenericApplication)

prints out all the available methods.

Warning: Once an application has been added to a job, it is not possible to change the parameters. This is unfortunate, and will be fixed eventually. 
It should be possible to change the parameters up to the point the job is actually submitted.

@author: Stephane Poss
@author: Remi Ete
@author: Ching Bon Lam
"""

from ILCDIRAC.Interfaces.API.NewInterface.Application import Application
from ILCDIRAC.Core.Utilities.ProcessList              import *
from ILCDIRAC.Core.Utilities.GeneratorModels          import GeneratorModels
from ILCDIRAC.Core.Utilities.InstalledFiles           import Exists
from ILCDIRAC.Core.Utilities.WhizardOptions           import WhizardOptions

from DIRAC.Core.Workflow.Parameter                    import Parameter
from DIRAC.Core.Workflow.Step                         import *
from DIRAC.Core.Workflow.Module                       import *
from DIRAC                                            import S_OK,S_ERROR, gConfig


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
    ### The Application init has to come last as if not the passed parameters are overwritten by the defaults.
    Application.__init__(self, paramdict)
    #Those have to come last as the defaults from Application are not right
    self._modulename = "ApplicationScript"
    self.appname = self._modulename
    self._moduledescription = 'An Application script module that can execute any provided script in the given project name and version environment'
      
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
    """ Optional: Define the arguments of the script
    
    @param args: Arguments to pass to the command line call
    @type args: string
    
    """
    self._checkArgs( {
        'args' : types.StringTypes
      } )  
    self.arguments = args
    return S_OK()
      
  def setDependency(self,appdict):
    """ Define list of application you need
    
    >>> app.setDependency({"mokka":"v0706P08","marlin":"v0111Prod"})
    
    @param appdict: Dictionary of application to use: {"App":"version"}
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
    m1.addParameter(Parameter("script",      "", "string", "", "", False, False, "Script to execute"))
    m1.addParameter(Parameter("arguments",   "", "string", "", "", False, False, "Arguments to pass to the script"))
    m1.addParameter(Parameter("debug",    False,   "bool", "", "", False, False, "debug mode"))
    return m1
  
  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue("script",self.script)
    moduleinstance.setValue('arguments',self.arguments)
    moduleinstance.setValue('debug',self.debug)
  
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()    

  def _addParametersToStep(self,stepdefinition):
    res = self._addBaseParameters(stepdefinition)
    if not res["OK"]:
      return S_ERROR("Failed to set base parameters")
    return S_OK()
  
  def _setStepParametersValues(self, instance):
    self._setBaseStepParametersValues(instance)
    for depn,depv in self.dependencies.items():
      self._job._addSoftware(depn,depv)
    return S_OK()
      
  def _checkConsistency(self):
    """ Checks that script and dependencies are set.
    """
    if not self.script:
      return S_ERROR("Script not defined")
    elif not self.script.lower().count("lfn:") and not os.path.exists(self.script):
      return S_ERROR("Specified script is not an LFN and was not found on disk")
      
    if not len(self.dependencies):
      return S_ERROR("Dependencies not set: No application to install. If correct you should use job.setExecutable")
    return S_OK()  
  
#################################################################
#            GetSRMFile: as its name suggests...
#################################################################  
class GetSRMFile(Application):
  """ Gets a given file from storage directly using srm path.
  
  Usage:
  
  >>> gf = GetSRMFile()
  >>> fdict = {"file":"srm://srm-public.cern.ch/castor/cern.ch/grid/ilc/prod/clic/1tev/Z_uds/gen/0/nobeam_nobrem_0-200.stdhep","site":"CERN-SRM"}
  >>> gf.setFiles(fdict)
  
  """
  def __init__(self, paramdict = None):
    Application.__init__(self, paramdict)
    self._modulename = "GetSRMFile"
    self.appname = self._modulename
    self._moduledescription = "Module to get files directly from Storage"

  def setFiles(self,fdict):
    """ Specify the files you need
    
    @param fdict: file dictionary: {file:site}, can be also [{},{}] etc.
    @type fdict: dict or list
    """
    kwargs = {"fdict":fdict}
    if not type(fdict) == type({}) and not type(fdict) == type([]):
      return self._reportError('Expected dict or list of dicts for fdict', __name__, **kwargs)
    
    self.filedict = fdict

  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter(Parameter("srmfiles", [], "list", "", "", False, False, "list of files to retrieve"))
    m1.addParameter(Parameter("debug", False, "bool", "", "", False, False, "debug mode"))
    return m1

  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue("srmfiles",self.filedict)  
    moduleinstance.setValue("debug",self.debug)  
  
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    if not res1["OK"]  :
      return S_ERROR("userjobmodules method failed")
    return S_OK() 

  def _prodjobmodules(self,step):
    self._log.error("This application is not meant to be used in Production context")
    return S_ERROR('Should not use in Production')

  
  def _checkConsistency(self):

    if not self.filedict:
      return S_ERROR("The file list was not defined")
    
    if type(self.filedict) == type({}):
      self.filedict = [self.filedict]

    ##For the getInputFromApp to work, we nedd to tell the application about the expected OutputFile
    flist = ''
    for fdict in self.filedict:
      f = fdict['file']
      bname = f.split("/")[-1]
      flist += bname+";"
      
    self.setOutputFile(flist.rstrip(";"))
        
    return S_OK()

  def _addParametersToStep(self,step):
    res = self._addBaseParameters(step)
    if not res["OK"]:
      return S_ERROR("Failed to set base parameters")
    return S_OK()


#################################################################
#                    ROOT master class
#################################################################  
class _Root(Application):
  """ Root principal class. Will inherit in RootExe and RootMacro classes, so don't use this (you can't anyway)!
  """
  
  def __init__(self, paramdict = None):
    self.arguments = ''
    Application.__init__(self, paramdict)
    
    
  def setScript(self,script):
    self._log.error("Don't use this!")
    return S_ERROR("Not allowed here")
  
  
  def setMacro(self,macro):
    self._log.error("Don't use this!")
    return S_ERROR("Not allowed here")

     
  def setArguments(self,args):
    """ Optional: Define the arguments of the script
    
    @param args: Arguments to pass to the command line call
    @type args: string
    
    """
    self._checkArgs( {
        'args' : types.StringTypes
      } )  
    self.arguments = args
    return S_OK()
      

  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter(Parameter("arguments",    "", "string", "", "", False, False, "Arguments to pass to the script"))
    m1.addParameter(Parameter("script",       "", "string", "", "", False, False, "Script to execute"))
    m1.addParameter(Parameter("debug",     False,   "bool", "", "", False, False, "debug mode"))
    return m1
  
  
  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue('arguments',   self.arguments)
    moduleinstance.setValue("script",      self.script)
    moduleinstance.setValue('debug',       self.debug)
    
  
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 


  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()    

  def _checkConsistency(self):
    """ Checks that script is set.
    """
    if not self.script:
      return S_ERROR("Script or macro not defined")
    if not self.version:
      return S_ERROR("You need to specify the Root version")
    
    res = self._checkRequiredApp() ##Check that job order is correct
    if not res['OK']:
      return res
          
    return S_OK()
  
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK()  

#################################################################
#            Root Script Application: use a script in the 
#                    Root application framework
#################################################################  
class RootScript(_Root):
  """ Run a script (root executable or shell) in the root application environment. 
  
  Example:
  
  >>> rootsc = RootScript()
  >>> rootsc.setScript("myscript.exe")
  >>> rootsc.setArguments("some command line arguments")
  
  """
  def __init__(self, paramdict = None):
    self.script = None
    _Root.__init__(self, paramdict)
    self._modulename = "RootExecutableAnalysis"
    self.appname = 'root'
    self._moduledescription = 'Root application script'
      
      
  def setScript(self,executable):
    """ Define executable to use
    
    @param executable: Script to run on. Can be shell or root executable. Must be a local file.
    @type executable: string
    """
    self._checkArgs( {
        'executable' : types.StringTypes
      } )

    self.script = executable
    if os.path.exists(executable) or executable.lower().count("lfn:"):
      self.inputSB.append(executable)
    return S_OK()
    

#################################################################
#            Root Macro Application: use a macro in the 
#                   Root application framework
#################################################################  
class RootMacro(_Root):
  """ Run a root macro in the root application environment. 
  
  Example:
  
  >>> rootmac = RootMacro()
  >>> rootmac.setMacro("mymacro.C")
  >>> rootmac.setArguments("some command line arguments")
  
  """
  def __init__(self, paramdict = None):
    self.script = None
    _Root.__init__(self, paramdict)
    self._modulename = "RootMacroAnalysis"
    self.appname = 'root'
    self._moduledescription = 'Root macro execution'
      
      
  def setMacro(self,macro):
    """ Define macro to use
    
    @param macro: Macro to run on. Must be a local C file.
    @type macro: string
    """
    self._checkArgs( {
        'macro' : types.StringTypes
      } )

    self.script = macro
    if os.path.exists(macro) or macro.lower().count("lfn:"):
      self.inputSB.append(macro)
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
  >>> wh.setModel("sm")

  """
  def __init__(self, processlist = None, paramdict = None):    
    
    self.parameterdict = {}
    self.model = 'sm'  
    self.seed = 0
    self.lumi = 0
    self.jobindex = ''
    self._optionsdictstr = ''
    self.optionsdict = {}
    self._leshouchesfiles = None
    self._generatormodels = GeneratorModels()
    self.evttype = ''
    self._allowedparams = ['PNAME1','PNAME2','POLAB1','POLAB2','USERB1','USERB2','ISRB1','ISRB2','EPAB1','EPAB2','RECOIL','INITIALS','USERSPECTRUM']
    self.parameters = []
    self._processlist = None
    if processlist:
      self._processlist = processlist
    Application.__init__(self, paramdict)
    ##Those 4 need to come after default constructor
    self._modulename = 'WhizardAnalysis'
    self._moduledescription = 'Module to run WHIZARD'
    self.appname = 'whizard'
    self.datatype = 'gen'
    
    
  def setEvtType(self,evttype):
    """ Define process. If the process given is not found, when calling job.append a full list is printed.
    
    @param evttype: Process to generate
    @type evttype: string
    """
    self._checkArgs( {
        'evttype' : types.StringTypes
      } )
    if self.addedtojob:
      self._log.error("Cannot modify this attribute once application has been added to Job")
      return S_ERROR("Cannot modify")
    self.evttype = evttype

  def setLuminosity(self,lumi):
    """ Optional: Define luminosity to generate 
    
    @param lumi: Luminosity to generate. Not available if cross section is not known a priori. Use with care.
    @type lumi: float
    """
    self._checkArgs( {
        'lumi' : types.FloatType
      } )    
    self.lumi = lumi

  def setRandomSeed(self,seed):
    """ Optional: Define random seed to use. Default is Job ID.
    
    @param seed: Seed to use during integration and generation. 
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

  def setFullParameterDict(self,dict):
    """ Parameters for Whizard steering files, better than above as much more complete (cannot be more complete)
    
    >>> pdict = {}
    >>> pdict['process_input'] = {}
    >>> pdict['process_input']['process_id']='h_n1n1'#processes here are not those of the templates, but those of the whizard.prc
    >>> pdict['process_input']['sqrts'] = 3000.
    >>> pdict['simulation_input'] = {}
    >>> pdict['simulation_input']['n_events'] = 100
    >>> pdict['beam_input_1'] = {}
    >>> pdict['beam_input_1']['polarization']='1.0 0.0'
    >>> pdict['beam_input_1']['USER_spectrum_mode'] = 11
    >>> pdict['beam_input_2'] = {}
    >>> pdict['beam_input_2']['polarization']='0.0 1.0'
    >>> pdict['beam_input_2']['USER_spectrum_mode'] = -11
    >>> wh.setFullParameterDict(pdict)
    
    The first key corresponds to the sections of the whizard.in, while the second corresponds to the possible parameters.
    All keys/values can be found in the WHIZARD documentation: U{http://projects.hepforge.org/whizard/manual_w1/manual005.html#toc11}
    
    @param dict: Dictionnary of parameters
    @type dict: dict
    """
    self._checkArgs( {
        'dict' : types.DictType
      } )

    self.optionsdict = dict
    self._wo.changeAndReturn(dict)
  
  def setModel(self,model):
    """ Optional: Define Model
    
    @param model: Model to use for generation. Predefined list available in GeneratorModels class.
    @type model: string
    """  
    self._checkArgs( {
        'model' : types.StringTypes
      } )

    self. model = model
    
  def setJobIndex(self,index):
    """ Optional: Define Job Index. Added in the file name between the event type and the extension.
    
    @param index: Index to use for generation
    @type index: string
    """  
    self._checkArgs( {
        'index' : types.StringTypes
      } )

    self.jobindex = index
    
  def _checkConsistency(self):

    self._wo = WhizardOptions(self.model)

    if not self.optionsdict:
      if not self.energy :
        return S_ERROR('Energy not set')
      
      if not self.nbevts :
        return S_ERROR('Number of events not set!')
    
      if not self.evttype:
        return S_ERROR("Process not defined")
    else:
      res = self._wo.checkFields(self.optionsdict)
      if not res['OK']:
        return res
      res = self._wo.getValue("process_input/process_id")
      if not len(res['Value']):
        if self.evttype:
          if not self.optionsdict.has_key('process_input'):
            self.optionsdict['process_input'] = {}
          self.optionsdict['process_input']['process_id']=self.evttype
        else:
          return S_ERROR("Event type not specified")
      self.evttype = res['Value']
      
      res = self._wo.getValue("process_input/sqrts")
      if type(res['Value']) == type(3) or type(res['Value']) == type(3.):
        energy = res['Value']
      else:
        energy = eval(res['Value'])
      if not energy:
        if self.energy:
          if not self.optionsdict.has_key('process_input'):
            self.optionsdict['process_input'] = {}
          self.optionsdict['process_input']['sqrts']=self.energy
          energy = self.energy
        else:
          return S_ERROR("Energy set to 0")
      self.energy = energy
      
      res = self._wo.getValue("simulation_input/n_events")
      if type(res['Value']) == type(3) or type(res['Value']) == type(3.):
        nbevts = res['Value']
      else:
        nbevts = eval(res['Value'])      
      if not nbevts:
        if self.nbevts:
          if not self.optionsdict.has_key('simulation_input'):
            self.optionsdict['simulation_input'] = {}
          self.optionsdict['simulation_input']['n_events']=self.nbevts
          nbevts = self.nbevts
        else:
          return S_ERROR("Number of events set to 0")
      self.nbevts = nbevts
      
    if not self._processlist:
      return S_ERROR("Process list was not given")
    
    if self.evttype:
      processes = self.evttype.split()
      for process in processes:
        if not self._processlist.existsProcess(process)['Value']:
          self._log.info("Available processes are:")
          self._processlist.printProcesses()
          return S_ERROR('Process does no exists')
        else:
          cspath = self._processlist.getCSPath(process)
          whiz_file = os.path.basename(cspath)
          version = whiz_file.replace(".tar.gz","").replace(".tgz","").replace("whizard","")
          if self.version:
            if self.version != version:
              return S_ERROR("All processes to consider are not available in the same WHIZARD version")
          self.version = version
          self._log.info("Found the process %s in whizard %s"%(process,self.version))
        
    if not self.version:
      return S_ERROR('No version found')
      
    if self.model:
      if not self._generatormodels.hasModel(self.model)['OK']:
        return S_ERROR("Unknown model %s"%self.model)

    if not self.outputFile and self._jobtype == 'User':
      self.outputFile = self.evttype
      if self.jobindex :
        self.outputFile += "_"+self.jobindex
      self.outputFile += "_gen.stdhep"  

    if not self._jobtype == 'User':
      self._listofoutput.append({"outputFile":"@{OutputFile}","outputPath":"@{OutputPath}","outputDataSE":'@{OutputSE}'})    
   
    if not self.optionsdict and  self.parameterdict:
      for key in self.parameterdict.keys():
        if not key in self._allowedparams:
          return S_ERROR("Unknown parameter %s"%key)

      if not self.parameterdict.has_key('PNAME1'):
        self._log.info("Assuming incoming beam 1 to be electrons")
        self.parameters.append('PNAME1=e1')
      else:
        self.parameters.append("PNAME1=%s" %self.parameterdict["PNAME1"] )
      
      if not self.parameterdict.has_key('PNAME2'):
        self._log.info("Assuming incoming beam 2 to be positrons")
        self.parameters.append('PNAME2=E1')
      else:
        self.parameters.append("PNAME2=%s" %self.parameterdict["PNAME2"] )
       
      if not self.parameterdict.has_key('POLAB1'):
        self._log.info("Assuming no polarization for beam 1")
        self.parameters.append('POLAB1=0.0 0.0')
      else:
        self.parameters.append("POLAB1=%s" % self.parameterdict["POLAB1"])
          
      if not self.parameterdict.has_key('POLAB2'):
        self._log.info("Assuming no polarization for beam 2")
        self.parameters.append('POLAB2=0.0 0.0')
      else:
        self.parameters.append("POLAB2=%s" % self.parameterdict["POLAB2"])
          
      if not self.parameterdict.has_key('USERB1'):
        self._log.info("Will put beam spectrum to True for beam 1")
        self.parameters.append('USERB1=T')
      else:
        self.parameters.append("USERB1=%s" % self.parameterdict["USERB1"])
          
      if not self.parameterdict.has_key('USERB2'):
        self._log.info("Will put beam spectrum to True for beam 2")
        self.parameters.append('USERB2=T')
      else:
        self.parameters.append("USERB2=%s" % self.parameterdict["USERB2"])
          
      if not self.parameterdict.has_key('ISRB1'):
        self._log.info("Will put ISR to True for beam 1")
        self.parameters.append('ISRB1=T')
      else:
        self.parameters.append("ISRB1=%s" % self.parameterdict["ISRB1"])
          
      if not self.parameterdict.has_key('ISRB2'):
        self._log.info("Will put ISR to True for beam 2")
        self.parameters.append('ISRB2=T')
      else:
        self.parameters.append("ISRB2=%s" % self.parameterdict["ISRB2"])
          
      if not self.parameterdict.has_key('EPAB1'):
        self._log.info("Will put EPA to False for beam 1")
        self.parameters.append('EPAB1=F')
      else:
        self.parameters.append("EPAB1=%s" % self.parameterdict["EPAB1"])
          
      if not self.parameterdict.has_key('EPAB2'):
        self._log.info("Will put EPA to False for beam 2")
        self.parameters.append('EPAB2=F')
      else:
        self.parameters.append("EPAB2=%s" % self.parameterdict["EPAB2"])
         
      if not self.parameterdict.has_key('RECOIL'):
        self._log.info("Will set Beam_recoil to False")
        self.parameters.append('RECOIL=F')
      else:
        self.parameters.append("RECOIL=%s" % self.parameterdict["RECOIL"])
          
      if not self.parameterdict.has_key('INITIALS'):
        self._log.info("Will set keep_initials to False")
        self.parameters.append('INITIALS=F')
      else:
        self.parameters.append("INITIALS=%s" % self.parameterdict["INITIALS"])
          
      if not self.parameterdict.has_key('USERSPECTRUM'):
        self._log.info("Will set USER_spectrum_on to +-11")
        self.parameters.append('USERSPECTRUM=11')
      else:
        self.parameters.append("USERSPECTRUM=%s" % self.parameterdict["USERSPECTRUM"])
      
      self.parameters = string.join(self.parameters, ";")
    elif self.optionsdict:
      self._optionsdictstr = str(self.optionsdict)
      
    return S_OK()  

  def _applicationModule(self):
    md1 = self._createModuleDefinition()
    md1.addParameter(Parameter("evttype",     "", "string", "", "", False, False, "Process to generate"))
    md1.addParameter(Parameter("RandomSeed",   0,    "int", "", "", False, False, "Random seed for the generator"))
    md1.addParameter(Parameter("Lumi",         0,  "float", "", "", False, False, "Luminosity of beam"))
    md1.addParameter(Parameter("Model",       "", "string", "", "", False, False, "Model for generation"))
    md1.addParameter(Parameter("SteeringFile","", "string", "", "", False, False, "Steering file"))
    md1.addParameter(Parameter("JobIndex",    "", "string", "", "", False, False, "Job Index"))
    md1.addParameter(Parameter("steeringparameters",  "", "string", "", "", False, False, "Specific steering parameters"))
    md1.addParameter(Parameter("OptionsDictStr",      "", "string", "", "", False, False, "Options dict to create full whizard.in on the fly"))
    md1.addParameter(Parameter("debug",    False,   "bool", "", "", False, False, "debug mode"))
    return md1

  
  def _applicationModuleValues(self,moduleinstance):

    moduleinstance.setValue("evttype",      self.evttype)
    moduleinstance.setValue("RandomSeed",   self.seed)
    moduleinstance.setValue("Lumi",         self.lumi)
    moduleinstance.setValue("Model",        self.model)
    moduleinstance.setValue("SteeringFile", self.steeringfile)
    moduleinstance.setValue("JobIndex",     self.jobindex)
    moduleinstance.setValue("steeringparameters",   self.parameters)
    moduleinstance.setValue("OptionsDictStr", self._optionsdictstr)
    moduleinstance.setValue("debug",        self.debug)
    
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()

    
  
#################################################################
#            PYTHIA: Second Generator application
#################################################################    
class Pythia(Application):
  """ Call pythia.
  
  Usage:
  
  >>> py = Pythia()
  >>> py.setVersion("tt_500gev_V2")
  >>> py.setEnergy(500) #Can look like a duplication of info, but trust me, it's needed.
  >>> py.setNbEvts(50)
  >>> py.setOutputFile("myfile.stdhep")

  """
  def __init__(self,paramdict = None):
    self.evttype = ''
    Application.__init__(self,paramdict)
    self.appname = 'pythia'
    self._modulename = 'PythiaAnalysis'
    self._moduledescription = 'Module to run PYTHIA'
    self.datatype = 'gen'

  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    return m1  

  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()
      
  def _checkConsistency(self):
    if not self.version:
      return S_ERROR("Version not specified")
    
    #Resolve event type, needed for production jobs
    self.evttype = self.version.split("_")[0]
    
    if not self.nbevts:
      return S_ERROR("Number of events to generate not defined")

    if not self.outputFile:
      return S_ERROR("Output File not defined")
    
    if not self._jobtype == 'User':
      self._listofoutput.append({"outputFile":"@{OutputFile}","outputPath":"@{OutputPath}","outputDataSE":'@{OutputSE}'})

    return S_OK()
 
 
#################################################################
#     PostGenSelection : Helper to filter generator selection 
#################################################################  
class PostGenSelection(Application):
  """ Helper to filter generator selection
  
  Example:
  
  >>> postGenSel = PostGenSelection()
  >>> postGenSel.setNbEvtsToKeep(30)

  
  """
  def __init__(self, paramdict = None):

    self.NbEvtsToKeep = 0
    Application.__init__(self, paramdict)
    self._modulename = "PostGenSelection"
    self.appname = 'postgensel'
    self._moduledescription = 'Helper to filter generator selection'
      
  def setNbEvtsToKeep(self,NbEvtsToKeep):
    """ Set the number of events to keep in the input file
    
    @param NbEvtsToKeep: number of events to keep in the input file. Must be inferior to the number of events.
    @type NbEvtsToKeep: int
    
    """  
    self._checkArgs( {
        'NbEvtsToKeep' : types.IntType
      } )
    
    self.NbEvtsToKeep = NbEvtsToKeep
    return S_OK()


  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter( Parameter( "NbEvtsKept",           0,   "int", "", "", False, False, "Number of events to keep" ) )
    m1.addParameter( Parameter( "debug",            False,  "bool", "", "", False, False, "debug mode"))
    return m1
  

  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue('NbEvtsKept',                  self.NbEvtsToKeep)
    moduleinstance.setValue('debug',                       self.debug)
   
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()    

  def _checkConsistency(self):
    """ Checks that all needed parameters are set
    """ 
      
    if not self.NbEvtsToKeep :
      return S_ERROR('Number of events to keep was not given! Throw your brain to the trash and try again!')
    
    res = self._checkRequiredApp() ##Check that job order is correct
    if not res['OK']:
      return res      
    
    return S_OK()  
  
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK()   
  
##########################################################################
#            StdhepCut: apply generator level cuts after pythia or whizard
##########################################################################
class StdhepCut(Application): 
  """ Call stdhep cut after whizard of pythia
  
  Usage:
  
  >>> py = Pythia()
  ...
  >>> cut = StdhepCut()
  >>> cut.getInputFromApp(py)
  >>> cut.setSteeringFile("mycut.cfg")
  >>> cut setMaxNbEvts(10)
  >>> cut.setNbEvtsPerFile(10)
  
  """
  def __init__(self, paramdict = None):
    self.maxevts = 0
    self.nbevtsperfile = 0
    Application.__init__(self,paramdict)

    self.appname = 'stdhepcut'
    self._modulename = 'StdHepCut'
    self._moduledescription = 'Module to cut on Generator (Whizard of PYTHIA)'

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
    m1.addParameter(Parameter("debug", False, "bool", "", "", False, False, "debug mode"))

    return m1

  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue("MaxNbEvts",self.maxevts)
    moduleinstance.setValue("debug",    self.debug)

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
  
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK()  
    
    
##########################################################################
#            Mokka: Simulation after Whizard or StdHepCut
##########################################################################
class Mokka(Application): 
  """ Call Mokka simulator (after Whizard, Pythia or StdHepCut)
  
  To ensure reproductibility, the RandomSeed is used as mcRunNumber. By default it's the jobID.
  
  Usage:
  
  >>> wh = Whizard()
  ...
  >>> mo = Mokka()
  >>> mo.getInputFromApp(wh)
  >>> mo.setSteeringFile("mysteer.steer")
  >>> mo.setMacFile('MyMacFile.mac')
  >>> mo.setStartFrom(10)
  
  """
  def __init__(self, paramdict = None):

    self.startFrom = 0
    self.macFile = ''
    self.seed = 0
    self.runnumber = 0
    self.dbSlice = ''
    self.detectorModel = ''
    self.processID = ''
    Application.__init__(self,paramdict)
    ##Those 5 need to come after default constructor
    self._modulename = 'MokkaAnalysis'
    self._moduledescription = 'Module to run MOKKA'
    self.appname = 'mokka'    
    self.datatype = 'SIM'
    self.detectortype = 'ILD'
     
  def setRandomSeed(self,seed):
    """ Optional: Define random seed to use. Default is JobID. 
    
    Also used as mcRunNumber.
    
    @param seed: Seed to use during integration and generation. Default is Job ID.
    @type seed: int
    """
    self._checkArgs( {
        'seed' : types.IntType
      } )

    self.seed = seed    
    
  def setmcRunNumber(self,runnumber):
    """ Optional: Define mcRunNumber to use. Default is 0. In Production jobs, is equal to RandomSeed
        
    @param runnumber: mcRunNumber parameter of Mokka
    @type runnumber: int
    """
    self._checkArgs( {
        'runnumber' : types.IntType
      } )

    self.runnumber = runnumber    
    
  def setDetectorModel(self,detectorModel):
    """ Define detector to use for Mokka simulation 
    
    @param detectorModel: Detector Model to use for Mokka simulation. Default is ??????
    @type detectorModel: string
    """
    self._checkArgs( {
        'detectorModel' : types.StringTypes
      } )

    self.detectorModel = detectorModel    
    
  def setMacFile(self,macfile):
    """ Optional: Define Mac File. Useful if using particle gun.
    
    @param macfile: Mac file for Mokka
    @type macfile: string
    """
    self._checkArgs( {
        'macfile' : types.StringTypes
      } )
    self.macFile = macfile
    if os.path.exists(macfile) or macfile.lower().count("lfn:"):
      self.inputSB.append(macfile)
    else:
      self._log.info("Mac file not found locally and is not an lfn, I hope you know what you are doing...")  
    
    
  def setStartFrom(self,startfrom):
    """ Optional: Define from where mokka starts to read in the generator file
    
    @param startfrom: from how mokka start to read the input file
    @type startfrom: int
    """
    self._checkArgs( {
        'startfrom' : types.IntType
      } )
    self.startFrom = startfrom  
    
    
  def setProcessID(self,processID):
    """ Optional: Define the processID. This is added to the event header.
    
    @param processID: ID's process
    @type processID: string
    """
    self._checkArgs( {
        'processID' : types.StringTypes
      } )
    self.processID = processID
    
    
  def setDbSlice(self,dbSlice):
    """ Optional: Define the data base that will use mokka
    
    @param dbSlice: data base used by mokka
    @type dbSlice: string
    """
    self._checkArgs( {
        'dbSlice' : types.StringTypes
      } )
    self.dbSlice = dbSlice
    if os.path.exists(dbSlice) or dbSlice.lower().count("lfn:"):
      self.inputSB.append(dbSlice)
    else:
      self._log.info("DB slice not found locally and is not an lfn, I hope you know what you are doing...")  
      
    
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()
  
  def _checkConsistency(self):

    if not self.version:
      return S_ERROR('No version found')   
    
    if not self.steeringfile :
      return S_ERROR('No Steering File') 
    
    if not os.path.exists(self.steeringfile) and not self.steeringfile.lower().count("lfn:"):
      res = Exists(self.steeringfile)
      if not res['OK']:
        return res  
    
    res = self._checkRequiredApp()
    if not res['OK']:
      return res

    if not self._jobtype == 'User':
      self._listofoutput.append({"outputFile":"@{OutputFile}","outputPath":"@{OutputPath}","outputDataSE":'@{OutputSE}'})
   
    return S_OK()  
  
  def _applicationModule(self):
    
    md1 = self._createModuleDefinition()
    md1.addParameter(Parameter("RandomSeed",           0,    "int", "", "", False, False, "Random seed for the generator"))
    md1.addParameter(Parameter("mcRunNumber",          0,    "int", "", "", False, False, "mcRunNumber parameter for Mokka"))
    md1.addParameter(Parameter("detectorModel",       "", "string", "", "", False, False, "Detecor model for simulation"))
    md1.addParameter(Parameter("macFile",             "", "string", "", "", False, False, "Mac file"))
    md1.addParameter(Parameter("startFrom",            0,    "int", "", "", False, False, "From where Mokka start to read the input file"))
    md1.addParameter(Parameter("dbSlice",             "", "string", "", "", False, False, "Data base used"))
    md1.addParameter(Parameter("ProcessID",           "", "string", "", "", False, False, "Process ID"))
    md1.addParameter(Parameter("debug",            False,   "bool", "", "", False, False, "debug mode"))
    return md1
  
  def _applicationModuleValues(self,moduleinstance):

    moduleinstance.setValue("RandomSeed",      self.seed)
    moduleinstance.setValue("detectorModel",   self.detectorModel)
    moduleinstance.setValue("mcRunNumber",     self.runnumber)
    moduleinstance.setValue("macFile",         self.macFile)
    moduleinstance.setValue("startFrom",       self.startFrom)
    moduleinstance.setValue("dbSlice",         self.dbSlice)
    moduleinstance.setValue("ProcessID",       self.processID)
    moduleinstance.setValue("debug",           self.debug)

    
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK() 
  


##########################################################################
#            SLIC : Simulation after Whizard or StdHepCut
##########################################################################
class SLIC(Application): 
  """ Call SLIC simulator (after Whizard, Pythia or StdHepCut)
  
  Usage:
  
  >>> wh = Whizard()
  >>> slic = SLIC()
  >>> slic.getInputFromApp(wh)
  >>> slic.setSteeringFile("mymacrofile.mac")
  >>> slic.setStartFrom(10)
  
  """
  def __init__(self, paramdict = None):

    self.startFrom = 0
    self.seed = 0
    self.detectorModel = ''
    Application.__init__(self,paramdict)
    ##Those 5 need to come after default constructor
    self._modulename = 'SLICAnalysis'
    self._moduledescription = 'Module to run SLIC'
    self.appname = 'slic'    
    self.datatype = 'SIM'
    self.detectortype = 'SID'
     
  def setRandomSeed(self,seed):
    """ Optional: Define random seed to use. Default is Job ID.
    
    @param seed: Seed to use during simulation. 
    @type seed: int
    """
    self._checkArgs( {
        'seed' : types.IntType
      } )

    self.seed = seed    
    
  def setDetectorModel(self,detectorModel):
    """ Define detector to use for Slic simulation 
    
    @param detectorModel: Detector Model to use for Slic simulation. Default is ??????
    @type detectorModel: string
    """
    self._checkArgs( {
        'detectorModel' : types.StringTypes
      } )
    if detectorModel.lower().count("lfn:"):
      self.inputSB.append(detectorModel)
    elif detectorModel.lower().count(".zip"):
      if os.path.exists(detectorModel):
        self.inputSB.append(detectorModel)
      else:
        self._log.info("Specified detector model does not exist locally, I hope you know what you're doing")
    
    
    self.detectorModel = os.path.basename(detectorModel).replace(".zip","")
    
    
  def setStartFrom(self,startfrom):
    """ Optional: Define from how slic start to read in the input file
    
    @param startfrom: from how slic start to read the input file
    @type startfrom: int
    """
    self._checkArgs( {
        'startfrom' : types.IntType
      } )
    self.startFrom = startfrom  
    
    
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()
  
  def _checkConsistency(self):

    if not self.version:
      return S_ERROR('No version found')   
    if self.steeringfile:
      if not os.path.exists(self.steeringfile) and not self.steeringfile.lower().count("lfn:"):
        res = Exists(self.steeringfile)
        if not res['OK']:
          return res  
    
    res = self._checkRequiredApp()
    if not res['OK']:
      return res

    if not self._jobtype == 'User':
      self._listofoutput.append({"outputFile":"@{OutputFile}","outputPath":"@{OutputPath}","outputDataSE":'@{OutputSE}'})
   
    if not self.startFrom :
      self._log.info('No startFrom define for Slic : start from the begining')
    
    return S_OK()  
  
  def _applicationModule(self):
    
    md1 = self._createModuleDefinition()
    md1.addParameter(Parameter("RandomSeed",           0,    "int", "", "", False, False, "Random seed for the generator"))
    md1.addParameter(Parameter("detectorModel",       "", "string", "", "", False, False, "Detecor model for simulation"))
    md1.addParameter(Parameter("startFrom",            0,    "int", "", "", False, False, "From how Slic start to read the input file"))
    md1.addParameter(Parameter("debug",            False,   "bool", "", "", False, False, "debug mode"))
    return md1
  
  def _applicationModuleValues(self,moduleinstance):

    moduleinstance.setValue("RandomSeed",      self.seed)
    moduleinstance.setValue("detectorModel",   self.detectorModel)
    moduleinstance.setValue("startFrom",       self.startFrom)
    moduleinstance.setValue("debug",           self.debug)

    
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK()   
  
  
#################################################################
#            OverlayInput : Helper call to define 
#              Overlay processor/driver inputs
#################################################################  
class OverlayInput(Application):
  """ Helper call to define Overlay processor/driver inputs. 
  
  Example:
  
  >>> over = OverlayInput()
  >>> over.setBXOverlay(300)
  >>> over.setGGToHadInt(3.2)
  >>> over.setNbSigEvtsPerJob(10)
  
  """
  def __init__(self, paramdict = None):
    self.BXOverlay = None
    self.ggtohadint = 0
    self.NbSigEvtsPerJob = 0
    self.BkgEvtType = ''
    self.inputenergy = ''
    self.prodid = 0
    Application.__init__(self, paramdict)
    self._modulename = "OverlayInput"
    self.appname = self._modulename
    self._moduledescription = 'Helper call to define Overlay processor/driver inputs'

  def setProdID(self,pid):
    self._checkArgs( {'pid': types.IntType})
    self.prodid = pid
    return S_OK()
      
  def setBXOverlay(self,bxoverlay):
    """ Define bunch crossings to overlay
    
    @param bxoverlay: Bunch crossings to overlay.
    @type bxoverlay: float
    """
    self._checkArgs( {
        'bxoverlay' : types.IntType
      } )
    self.BXOverlay = bxoverlay
    return S_OK()
    
  def setGGToHadInt(self,ggtohadint):
    """ Define the optional number of gamma gamma -> hadrons interactions per bunch crossing, default is 3.2
    
    @param ggtohadint: optional number of gamma gamma -> hadrons interactions per bunch crossing
    @type ggtohadint: float
    
    """
    self._checkArgs( {
        'ggtohadint' : types.FloatType
      } )  
    self.ggtohadint = ggtohadint
    return S_OK()
      
  def setNbSigEvtsPerJob(self,nbsigevtsperjob):
    """ Set the number of signal events per job
    
    @param nbsigevtsperjob: Number of signal events per job
    @type nbsigevtsperjob: int
    
    """  
    self._checkArgs( {
        'nbsigevtsperjob' : types.IntType
      } )
    
    self.NbSigEvtsPerJob = nbsigevtsperjob
    return S_OK()


  def setDetectorType(self,detectortype):
    """ Set the detector type. Must be 'ILD' or 'SID'
    
    @param detectortype: Detector type. Must be 'ILD' or 'SID'
    @type detectortype: string
    
    """  
    self._checkArgs( {
        'detectortype' : types.StringTypes
      } )
    
    self.detectortype = detectortype
    return S_OK()


  def setBkgEvtType(self,BkgEvtType):
    """ Optional: Define the background type. Default is gg -> had. For the moment only gghad is used.
    
    @param BkgEvtType: Background type. Default is gg -> had 
    @type BkgEvtType: string
    
    """  
    self._checkArgs( {
        'BkgEvtType' : types.StringTypes
      } )
    
    self.BkgEvtType = BkgEvtType
    return S_OK()
  
#  def setProdIDToUse(self,prodid):
#    """ Optional parameter: Define the production ID to use as input
#    
#    @param prodid: Production ID
#    @type prodid: int
#    """
#    self._checkArgs({"prodid" : types.IntType})
#    self.prodid = prodid
#    return S_OK()

  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter(Parameter("BXOverlay",            0,  "float", "", "", False, False, "Bunch crossings to overlay"))
    m1.addParameter(Parameter("ggtohadint",           0,  "float", "", "", False, False, "Optional number of gamma gamma -> hadrons interactions per bunch crossing, default is 3.2"))
    m1.addParameter(Parameter("NbSigEvtsPerJob",      0,    "int", "", "", False, False, "Number of signal events per job"))
    m1.addParameter(Parameter("prodid",               0,    "int", "", "", False, False, "ProdID to use"))
    m1.addParameter(Parameter("BkgEvtType",          "", "string", "", "", False, False, "Background type. Default is gg -> had"))
    m1.addParameter(Parameter("detector",            "", "string", "", "", False, False, "Detector model. Must be ILD or SID"))
    m1.addParameter(Parameter("debug",            False,   "bool", "", "", False, False, "debug mode"))
    return m1
  

  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue("BXOverlay",         self.BXOverlay)
    moduleinstance.setValue('ggtohadint',        self.ggtohadint)
    moduleinstance.setValue('NbSigEvtsPerJob',   self.NbSigEvtsPerJob)
    moduleinstance.setValue('prodid',            self.prodid)
    moduleinstance.setValue('BkgEvtType',        self.BkgEvtType)
    moduleinstance.setValue('detector',          self.detectortype)
    moduleinstance.setValue('debug',             self.debug)
  
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    if not res1["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    if not res1["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()    

  def _addParametersToStep(self,stepdefinition):
    res = self._addBaseParameters(stepdefinition)
    if not res["OK"]:
      return S_ERROR("Failed to set base parameters")
    return S_OK()
      
  def _checkConsistency(self):
    """ Checks that all needed parameters are set
    """
    if not self.BXOverlay :
      self.BXOverlay = 60
      self._log.info("Using default number of BX to overlay: 60")
      
    if self._jobtype == 'User' :
      if not self.NbSigEvtsPerJob :
        return S_ERROR("Number of signal event per job is not defined")    
      
    if not self.ggtohadint :
      self.ggtohadint = 3.2
      self._log.info("Number of GG -> had is set to 3.2 by default")  
      
    if not self.BkgEvtType :
      self.BkgEvtType = 'gghad'
      self._log.info("Background event type is gg -> had by default")
      
    if not self.detectortype in ['ILD','SID'] :
      return S_ERROR('Detector type not set or wrong detector type. Allowed are ILD or SID.')
    
    return S_OK() 
  
  def _checkFinalConsistency(self):
    """ Final check of consistency: the overlay files for the specifed energy must exist
    """
    if not self.energy:
      return  S_ERROR("Energy MUST be spcified for the overlay")
    res = gConfig.getSections("/Operations/Overlay/%s"%self.detectortype)
    if not res['OK']:
      return S_ERROR("Could not find the detector type")
    if int(self.energy)/1000:
      energytouse = "%stev"%(int(self.energy)/1000)
    else:
      energytouse = "%sgev"%(int(self.energy))
    if not energytouse in res['Value']:
      return S_ERROR("No overlay files corresponding to %s"%energytouse)
    return S_OK()
  
  
##########################################################################
#            Marlin: Reconstructor after Mokka
##########################################################################
class Marlin(Application): 
  """ Call Marlin reconstructor (after Mokka simulator)
  
  Usage:
  
  >>> mo = Mokka()
  >>> marlin = Marlin()
  >>> marlin.getInputFromApp(mo)
  >>> marlin.setSteeringfile('SteeringFile.xml')
  >>> marlin.setOutputRecFile('MyOutputRecFile.rec')
  >>> marlin.setOutputDstFile('MyOutputDstFile.dst')
  
  """
  def __init__(self, paramdict = None):

    self.outputDstPath = ''
    self.outputDstFile = ''
    self.outputRecPath = ''
    self.outputRecFile = ''
    self.inputGearFile = ''
    Application.__init__(self,paramdict)
    ##Those 5 need to come after default constructor
    self._modulename = 'MarlinAnalysis'
    self._moduledescription = 'Module to run MARLIN'
    self.appname = 'marlin'    
    self.datatype = 'REC'
    self.detectortype = 'ILD'
    if not self.nbevts:
      self.nbevts = -1
     
    
  def setGearFile(self,GearFile):
    """ Define input gear file for Marlin
    
    @param GearFile: input gear file for Marlin reconstrcutor
    @type GearFile: string
    """
    self._checkArgs( {
        'GearFile' : types.StringTypes
      } )

    self.inputGearFile = GearFile
    if os.path.exists(GearFile) or GearFile.lower().count("lfn:"):
      self.inputSB.append(GearFile) 
    
  def setOutputRecFile(self,outputRecFile, path = None):
    """ Optional: Define output rec file for Marlin
    
    @param outputRecFile: output rec file for Marlin
    @type outputRecFile: string
    @param path: Path where to store the file. Used only in prouction context. Use setOutputData if you want to keep the file on the grid.
    @type path: string
    """
    self._checkArgs( {
        'outputRecFile' : types.StringTypes
      } )
    self.outputRecFile = outputRecFile
    self.prodparameters[self.outputRecFile] = {}
    self.prodparameters[self.outputRecFile]['datatype']= 'REC'
    if path:
      self.outputRecPath = path      
    
  def setOutputDstFile(self,outputDstFile, path = None):
    """ Optional: Define output dst file for Marlin
    
    @param outputDstFile: output dst file for Marlin
    @type outputDstFile: string
    @param path: Path where to store the file. Used only in prouction context. Use setOutputData if you want to keep the file on the grid.
    @type path: string
    """
    self._checkArgs( {
        'outputDstFile' : types.StringTypes
      } )
    self.outputDstFile = outputDstFile
    self.prodparameters[self.outputDstFile] = {}
    self.prodparameters[self.outputDstFile]['datatype']= 'DST'
    if path:
      self.outputDstPath = path    
      
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    
    ## Here one needs to take care of listoutput
    if self.outputPath:
      self._listofoutput.append({'OutputFile':'@{OutputFile}',"outputPath":"@{OutputPath}","outputDataSE":self.outputSE})
    
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()
  
  def _checkConsistency(self):

    if not self.nbevts :
      self._log.error('Number of events set to 0 !')
        
    if not self.version:
      return S_ERROR('Version not set!')   

    if self.steeringfile:
      if not os.path.exists(self.steeringfile) and not self.steeringfile.lower().count("lfn:"):
        res = Exists(self.steeringfile)
        if not res['OK']:
          return res  
    
    if not self.inputGearFile :
      self._log.warn('GEAR file not given, will use GearOutput.xml (default from Mokka, CLIC_ILD_CDR model)')
    if self.inputGearFile:
      if not os.path.exists(self.inputGearFile) and not self.inputGearFile.lower().count("lfn:"):
        res = Exists(self.inputGearFile)
        if not res['OK']:
          return res  

    res = self._checkRequiredApp()
    if not res['OK']:
      return res

    if not self.inputGearFile:
      self.inputGearFile = 'GearOutput.xml'

    if not self._jobtype == 'User' :
      if not self.outputFile:
        self._listofoutput.append({"outputFile":"@{outputREC}","outputPath":"@{outputPathREC}","outputDataSE":'@{OutputSE}'})
        self._listofoutput.append({"outputFile":"@{outputDST}","outputPath":"@{outputPathDST}","outputDataSE":'@{OutputSE}'})
     
    return S_OK()  
  
  def _applicationModule(self):
    
    md1 = self._createModuleDefinition()
    md1.addParameter(Parameter("inputGEAR",     '', "string", "", "", False, False, "Input GEAR file"))
    md1.addParameter(Parameter("debug",      False,   "bool", "", "", False, False, "debug mode"))
    return md1
  
  def _applicationModuleValues(self,moduleinstance):

    moduleinstance.setValue("inputGEAR",         self.inputGearFile)
    moduleinstance.setValue("debug",             self.debug)

    
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK() 
  
##########################################################################
#            LCSIM: Reconstruction after SLIC Simulation
##########################################################################
class LCSIM(Application): 
  """ Call LCSIM Reconstructor (after SLIC Simulation)
  
  Usage:
  
  >>> slic = SLIC()
  >>> lcsim = LCSIM()
  >>> lcsim.getInputFromApp(slic)
  >>> lcsim.setSteeringFile("MySteeringFile.xml")
  >>> lcsim.setStartFrom(10)
  
  """
  def __init__(self, paramdict = None):

    self.extraParams = ''
    self.aliasProperties = ''
    Application.__init__(self,paramdict)
    ##Those 5 need to come after default constructor
    self._modulename = 'LCSIMAnalysis'
    self._moduledescription = 'Module to run LCSIM'
    self.appname = 'lcsim'
    self.datatype = 'REC'
    self.detectortype = 'SID'
    self.detectorModel = ''
     
  def setOutputRecFile(self,outputRecFile, path = None):
    """ Optional: Define output rec file for LCSIM
    
    @param outputRecFile: output rec file for LCSIM
    @type outputRecFile: string
    @param path: Path where to store the file. Used only in prouction context. Use setOutputData if you want to keep the file on the grid.
    @type path: string
    """
    self._checkArgs( {
        'outputRecFile' : types.StringTypes
                       } )
    self.outputRecFile = outputRecFile
    self.prodparameters[self.outputRecFile] = {}
    self.prodparameters[self.outputRecFile]['datatype']= 'REC'
    if path:
      self.outputRecPath = path
    
  def setOutputDstFile(self,outputDstFile, path = None):
    """ Optional: Define output dst file for LCSIM
    
    @param outputDstFile: output dst file for LCSIM
    @type outputDstFile: string
    @param path: Path where to store the file. Used only in prouction context. Use setOutputData if you want to keep the file on the grid.
    @type path: string
    """
    self._checkArgs( {
        'outputDstFile' : types.StringTypes
      } )
    self.outputDstFile = outputDstFile 
    self.prodparameters[self.outputDstFile] = {}
    self.prodparameters[self.outputDstFile]['datatype']= 'DST'
    if path:
      self.outputDstPath = path            
    
  def setAliasProperties(self,alias):
    """ Optional: Define the path to the alias.properties file name that will be used 
    
    @param alias: Path to the alias.properties file name that will be used
    @type alias: string
    """
    self._checkArgs( {
        'alias' : types.StringTypes
      } )

    self.aliasProperties = alias     
    if os.path.exists(alias) or alias.lower().count("lfn:"):
      self.inputSB.append(alias) 
  
  def setDetectorModel(self,model):
    self._checkArgs( {
        'model' : types.StringTypes
      } )    
    self.detectorModel = model
    if os.path.exists(model) or model.lower().count("lfn:"):
      self.inputSB.append(model)
    
  def setExtraParams(self,extraparams):
    """ Optional: Define command line parameters to pass to java
    
    @param extraparams: Command line parameters to pass to java
    @type extraparams: string
    """
    self._checkArgs( {
        'extraparams' : types.StringTypes
      } )

    self.extraParams = extraparams     
    
    
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()
  
  def _checkConsistency(self):

    if not self.energy :
      self._log.error('Energy set to 0 !')
      
    if not self.nbevts :
      self._log.error('Number of events set to 0 !')
        
    if not self.version:
      return S_ERROR('No version found')   

    if self.steeringfile:
      if not os.path.exists(self.steeringfile) and not self.steeringfile.lower().count("lfn:"):
        res = Exists(self.steeringfile)
        if not res['OK']:
          return res  
    
    if self.detectorModel:
      if not self.detectorModel.lower().count(".zip"):
        return S_ERROR("setDetectorModel: You HAVE to pass an existing .zip file, either as local file or as LFN. Or use the alias.properties.")
        
    res = self._checkRequiredApp()
    if not res['OK']:
      return res
    
    if not self._jobtype =='User':
      #slicp = False
      if self._inputapp and not self.outputFile:
        for app in self._inputapp:
          if app.appname == 'slicpandora':
            self._listofoutput.append({"outputFile":"@{outputREC}","outputPath":"@{outputPathREC}","outputDataSE":'@{OutputSE}'})
            self._listofoutput.append({"outputFile":"@{outputDST}","outputPath":"@{outputPathDST}","outputDataSE":'@{OutputSE}'})
            #slicp = True
            break
      #if not slicp:
      #  self._listofoutput.append({"outputFile":"@{OutputFile}","outputPath":"@{OutputPath}","outputDataSE":'@{OutputSE}'})    
      
      
    return S_OK()  
  
  def _applicationModule(self):
    
    md1 = self._createModuleDefinition()
    md1.addParameter(Parameter("extraparams",           "", "string", "", "", False, False, "Command line parameters to pass to java"))
    md1.addParameter(Parameter("aliasproperties",       "", "string", "", "", False, False, "Path to the alias.properties file name that will be used"))
    md1.addParameter(Parameter("debug",              False,   "bool", "", "", False, False, "debug mode"))
    md1.addParameter(Parameter("detectorModel",         "", "string", "", "", False, False, "detector model zip file"))
    return md1
  
  def _applicationModuleValues(self,moduleinstance):

    moduleinstance.setValue("extraparams",        self.extraParams)
    moduleinstance.setValue("aliasproperties",    self.aliasProperties)
    moduleinstance.setValue("debug",              self.debug)
    moduleinstance.setValue("detectorModel",      self.detectorModel)
    
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK()
  
##########################################################################
#            SLICPandora : Run Pandora in the SID context
##########################################################################
class SLICPandora(Application): 
  """ Call SLICPandora 
  
  Usage:
  
  >>> lcsim = LCSIM()
  ...
  >>> slicpandora = SLICPandora()
  >>> slicpandora.getInputFromApp(lcsim)
  >>> slicpandora.setPandoraSettings("~/GreatPathToHeaven/MyPandoraSettings.xml")
  >>> slicpandora.setStartFrom(10)
  
  """
  def __init__(self, paramdict = None):

    self.startFrom = 0
    self.pandoraSettings = ''
    self.detectorModel = ''
    Application.__init__(self,paramdict)
    ##Those 5 need to come after default constructor
    self._modulename = 'SLICPandoraAnalysis'
    self._moduledescription = 'Module to run SLICPANDORA'
    self.appname = 'slicpandora'    
    self.datatype = 'REC'
    self.detectortype = 'SID'
        
    
  def setDetectorModel(self,detectorModel):
    """ Define detector to use for SlicPandora simulation 
    
    @param detectorModel: Detector Model to use for SlicPandora simulation. Default is ??????
    @type detectorModel: string
    """
    self._checkArgs( {
        'detectorModel' : types.StringTypes
      } )

    self.detectorModel = detectorModel    
    if os.path.exists(detectorModel) or detectorModel.lower().count("lfn:"):
      self.inputSB.append(detectorModel)   
    
  def setStartFrom(self,startfrom):
    """ Optional: Define from where slicpandora start to read in the input file
    
    @param startfrom: from how slicpandora start to read the input file
    @type startfrom: int
    """
    self._checkArgs( {
        'startfrom' : types.IntType
      } )
    self.startfrom = startfrom     
    
  def setPandoraSettings(self,pandoraSettings):
    """ Optional: Define the path where pandora settings are
    
    @param pandoraSettings: path where pandora settings are
    @type pandoraSettings: string
    """
    self._checkArgs( {
        'pandoraSettings' : types.StringTypes
      } )
    self.pandoraSettings = pandoraSettings  
    if os.path.exists(pandoraSettings) or pandoraSettings.lower().count("lfn:"):
      self.inputSB.append(pandoraSettings)    
    
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()
  
  def _checkConsistency(self):

    if not self.version:
      return S_ERROR('No version found')   

    if self.steeringfile:
      if not os.path.exists(self.steeringfile) and not self.steeringfile.lower().count("lfn:"):
        res = Exists(self.steeringfile)
        if not res['OK']:
          return res  
    
    res = self._checkRequiredApp()
    if not res['OK']:
      return res
      
    if not self.startFrom :
      self._log.info('No startFrom define for SlicPandora : start from the begining')
      
    return S_OK()  
  
  def _applicationModule(self):
    
    md1 = self._createModuleDefinition()
    md1.addParameter(Parameter("pandorasettings",   "", "string", "", "", False, False, "Random seed for the generator"))
    md1.addParameter(Parameter("detectorxml",       "", "string", "", "", False, False, "Detecor model for simulation"))
    md1.addParameter(Parameter("startFrom",          0,    "int", "", "", False, False, "From how SlicPandora start to read the input file"))
    md1.addParameter(Parameter("debug",          False,   "bool", "", "", False, False, "debug mode"))
    return md1
  
  def _applicationModuleValues(self,moduleinstance):

    moduleinstance.setValue("pandorasettings",    self.pandoraSettings)
    moduleinstance.setValue("detectorxml",        self.detectorModel)
    moduleinstance.setValue("startFrom",          self.startFrom)
    moduleinstance.setValue("debug",              self.debug)

    
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK()


#################################################################
#            CheckCollection : Helper to check collection 
#################################################################  
class CheckCollections(Application):
  """ Helper to check collection 
  
  Example:
  
  >>> check = OverlayInput()
  >>> check.setInputFile( [slcioFile_1.slcio , slcioFile_2.slcio , slcioFile_3.slcio] )
  >>> check.setCollections( ["some_collection_name"] )
  
  """
  def __init__(self, paramdict = None):
    self.collections = []
    Application.__init__(self, paramdict)
    if not self.version:
      self.version = 'HEAD'
    self._modulename = "CheckCollections"
    self.appname = 'lcio'
    self._moduledescription = 'Helper call to define Overlay processor/driver inputs'

  def setCollections(self,CollectionList):
    """ Set collections. Must be a list
    
    @param CollectionList: Collections. Must be a list
    @type CollectionList: list
    
    """  
    self._checkArgs( {
        'CollectionList' : types.ListType
      } )
    
    self.collections = CollectionList
    return S_OK()


  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter( Parameter( "collections",         [], "list", "", "", False, False, "Collections to check for" ) )
    m1.addParameter( Parameter( "debug",            False, "bool", "", "", False, False, "debug mode"))
    return m1
  

  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue('collections',             self.collections)
    moduleinstance.setValue('debug',                   self.debug)
  
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()    

  def _checkConsistency(self):
    """ Checks that all needed parameters are set
    """

    if not self.collections :
      return S_ERROR('No collections to check')

    res = self._checkRequiredApp()
    if not res['OK']:
      return res
      
    return S_OK()
  
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK()
  
#################################################################
#     SLCIOConcatenate : Helper to concatenate SLCIO files 
#################################################################  
class SLCIOConcatenate(Application):
  """ Helper to concatenate slcio files
  
  Example:
  
  >>> slcioconcat = SLCIOConcatenate()
  >>> slcioconcat.setInputFile( ["slcioFile_1.slcio" , "slcioFile_2.slcio" , "slcioFile_3.slcio"] )
  >>> slcioconcat.setOutputFile("myNewSLCIOFile.slcio")
  
  """
  def __init__(self, paramdict = None):

    Application.__init__(self, paramdict)
    if not self.version:
      self.version = 'HEAD'
    self._modulename = "LCIOConcatenate"
    self.appname = 'lcio'
    self._moduledescription = 'Helper call to concatenate SLCIO files'

  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter( Parameter( "debug",            False,  "bool", "", "", False, False, "debug mode"))
    return m1

  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue('debug',                       self.debug)
   
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()    

  def _checkConsistency(self):
    """ Checks that all needed parameters are set
    """
      
    if not self.outputFile and self._jobtype =='User' :
      self.setOutputFile('LCIOFileConcatenated.slcio')
      self._log.info('No output file name specified. Output file : LCIOFileConcatenated.slcio')

    if not self._jobtype == 'User':
      self._listofoutput.append({"outputFile":"@{OutputFile}","outputPath":"@{OutputPath}","outputDataSE":'@{OutputSE}'})

    res = self._checkRequiredApp()
    if not res['OK']:
      return res
      
    return S_OK()
  
  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK()
  
#################################################################
#     Tomato : Helper to filter generator selection 
#################################################################  
class Tomato(Application):
  """ Helper application over Tomato analysis
  
  Example:
  
  >>> cannedTomato = Tomato()
  >>> cannedTomato.setInputFile ( [pouette_1.slcio , pouette_2.slcio] )
  >>> cannedTomato.setSteeringFile ( MySteeringFile.xml )
  >>> cannedTomato.setLibTomato ( MyUserVersionOfTomato )

  
  """
  def __init__(self, paramdict = None):

    self.libTomato = ''
    Application.__init__(self, paramdict)
    if not self.version:
      self.version = 'HEAD'
    self._modulename = "TomatoAnalysis"
    self.appname = 'tomato'
    self._moduledescription = 'Helper Application over Marlin reconstruction'
      
  def setLibTomato(self,libTomato):
    """ Optional: Set the the optional Tomato library with the user version
    
    @param libTomato: Tomato library
    @type libTomato: string
    
    """  
    self._checkArgs( {
        'libTomato' : types.StringTypes
      } )
    
    self.libTomato = libTomato
    return S_OK()


  def _applicationModule(self):
    m1 = self._createModuleDefinition()
    m1.addParameter( Parameter( "libTomato",           '',   "string", "", "", False, False, "Tomato library" ))
    m1.addParameter( Parameter( "debug",            False,     "bool", "", "", False, False, "debug mode"))
    return m1
  

  def _applicationModuleValues(self,moduleinstance):
    moduleinstance.setValue('libTomato',     self.libTomato)
    moduleinstance.setValue('debug',         self.debug)
   
  def _userjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setUserJobFinalization(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('userjobmodules failed')
    return S_OK() 

  def _prodjobmodules(self,stepdefinition):
    res1 = self._setApplicationModuleAndParameters(stepdefinition)
    res2 = self._setOutputComputeDataList(stepdefinition)
    if not res1["OK"] or not res2["OK"] :
      return S_ERROR('prodjobmodules failed')
    return S_OK()    

  def _checkConsistency(self):
    """ Checks that all needed parameters are set
    """ 

    if not self.version:
      return S_ERROR("You need to specify which version of Marlin to use.")
    
    if not self.libTomato :
      self._log.info('Tomato library not given. It will run without it')

    res = self._checkRequiredApp()
    if not res['OK']:
      return res
      
    return S_OK()  

  def _resolveLinkedStepParameters(self,stepinstance):
    if self._inputappstep:
      stepinstance.setLink("InputFile",self._inputappstep.getType(),"OutputFile")
    return S_OK()
  