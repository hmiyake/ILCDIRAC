import subprocess, unittest, os, tempfile, shutil, filecmp, sys
from mock import patch, MagicMock as Mock
from DIRAC.Core.Security import ProxyInfo
from DIRAC.Core.Base import Script

__RCSID__ = "$Id$"


class SETestCase( unittest.TestCase ):
  """ Base class for the test cases of the storage elements.
  requires dirac proxy
  """


  localtestfile = 'testfile'
  lfntestfilename = "testfile.txt"
  lfntestfilepath = "lfn:/ilc/user/"
  lfntestfile = ''
  storageelements = ["CERN-DIP-4", "CERN-SRM", "CERN-DST-EOS"]
  #storageelements = [ "CERN-DST-EOS" ]


  @classmethod
  def setUpClass( cls ):
    # destroy kerberos token
    #try:
    #  subprocess.call(['kdestroy'])
    #except subprocess.CalledProcessError as err:
    #  print "WARNING: kdestroy did not succeed."
    #  print err.output
    # Constants for the tests
    Script.parseCommandLine()
    user = ProxyInfo.getProxyInfo()['Value']['username']
    SETestCase.lfntestfilepath += '%s/%s/' % (user[0], user)
    print "Using lfn %s" % SETestCase.lfntestfilepath
    SETestCase.lfntestfile = SETestCase.lfntestfilepath + SETestCase.lfntestfilename


  def setUp( self ):
    """set up the objects"""
    # Check if file exists already
    try:
      subprocess.check_output(["dirac-dms-remove-files", self.lfntestfile])
      print "WARN Warning: file already existed on SE"
    except subprocess.CalledProcessError:
      sys.exc_clear()
      
    # Make temporary dir to run test in
    self.curdir = os.getcwd()
    self.tmpdir = tempfile.mkdtemp("", dir = "./")
    os.chdir(self.tmpdir)
    
    # Create testfile with random bits
    with open(self.localtestfile, 'wb') as fout:
      fout.write(" My random testfile ")
      fout.write(os.urandom(1024*1024))
    

  def tearDown ( self ):
    self.removeFileAllowFailing()
    os.chdir(self.curdir)
    shutil.rmtree( self.tmpdir )

#For python < 2.7 (executes cmd and grabs output)
#proc = subprocess.Popen(['python', 'printbob.py',  'arg1 arg2 arg3 arg4'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#print proc.communicate()[0]

  def test_storing_all( self ):
    print "Testing on sites:"
    for site in self.storageelements:
      print site
      self.storing_test(site)


  def storing_test( self, site ):
    """Uploads the file to a given SE, then retrieves it and checks for equality
    """
    self.uploadFile(site)
    # get file from SE, check for equivalence
    result = subprocess.check_output(["dirac-dms-get-file", "-ddd", self.lfntestfile])
    self.assertOperationSuccessful(result, "Retrieval of random file from storage element to local failed: " + result)
    
    self.assertTrue(filecmp.cmp(self.localtestfile, self.lfntestfilename), "Received wrong file")
    self.removeFile()

    
  #@unittest.skip("demonstrating skipping")
  def test_replication_all( self ):
    for (site1, site2) in self.getDistinctPairsOfSites():
      print "Testing for sites %s, %s" % (site1, site2)
      self.replication_test( site1, site2 )
      self.removeFile()
        
  def replication_test( self, site1, site2 ):
    """Replicates file to other SE, checks if it is replicated there.
    """
    self.uploadFile(site1)
    # Replicate file to SE2, remove replica from SE1, get file, rm from all
    self.replicateTo(site2)

    result = subprocess.check_output(["dirac-dms-remove-replicas", self.lfntestfile[4:], site1])
    self.assertTrue(result.count("Successfully removed") == 1, "Failed removing replica of random file: " + result)

    result = subprocess.check_output(["dirac-dms-get-file", self.lfntestfile])
    self.assertOperationSuccessful(result, "Retrieval of random file from storage element to local failed: " + result)
    
    self.assertTrue(filecmp.cmp(self.localtestfile, self.lfntestfilename), "Received wrong file")

  
  #@unittest.skip("demonstrating skipping")
  def test_removal_all( self ):
    for (site1, site2) in self.getDistinctPairsOfSites():
      print "Testing for sites %s, %s" % (site1, site2)
      self.removal_test(site1, site2)
        
  def removal_test( self, site1, site2 ):
    """Uploads file to SE1, replicates to SE2, removes file and checks if retreive fails
    """
    self.uploadFile(site1)
    self.replicateTo(site2)
 
    result = subprocess.check_output(["dirac-dms-remove-files", self.lfntestfile])
    self.assertTrue(result.count("Successfully removed 1 files") == 1, "Removal of random file failed: " + result)
    
    try:
      result = subprocess.check_output(["dirac-dms-get-file", self.lfntestfile])
      self.fail("Get file should not succeed")
    except subprocess.CalledProcessError as err:
      self.assertTrue(err.output.count("ERROR") >= 1, "File not removed from SE even though it should be: " + err.output)


  def uploadFile( self, site ):
    """Adds the local random file to the storage elements
    """
    try:
      result = subprocess.check_output(["dirac-dms-add-file", "-ddd", self.lfntestfile, self.localtestfile, site])
    except subprocess.CalledProcessError as err:
      print err.output
    self.assertTrue(result.count("Successfully uploaded ") == 1, "Upload of random file failed")

  def removeFile ( self ):
    """Removes the random file from the storage elements
    """
    result = subprocess.check_output(["dirac-dms-remove-files", self.lfntestfile])
    self.assertTrue(result.count("Successfully removed 1 files") == 1, "Removal of random file failed: " + result)
    
  def assertOperationSuccessful( self, result, message ):
    """Checks if the DMS operation completed successfully. This is indicated by the first line consisting of "'Failed: {}'"
    and the second line consisting of "'Successful': {" followed by the filename (not checked)
    """
    self.assertTrue(result.count("'Failed': {}") == 1 & result.count("'Successful': {'") == 1, message)

  def replicateTo( self, site ):
    """Replicates the random file to another storage element and checks if it worked
    """
    try:
      result = subprocess.check_output(["dirac-dms-replicate-lfn", self.lfntestfile[4:], site, "-ddd"])
    except subprocess.CalledProcessError as err:
      print err.output
      raise subprocess.CalledProcessError("1", "substitute cmd")
    self.assertOperationSuccessful(result, "Failed replicating file")

  def removeFileAllowFailing ( self ):
    """Removes the random file from the storage elements, if it exists.
    If it doesn't exist, nothing happens
    """
    try:
      subprocess.check_output(["dirac-dms-remove-files", self.lfntestfile])
    except subprocess.CalledProcessError:
      sys.exc_clear()

  def getDistinctPairsOfSites( self ):
    """Returns a list containing all pairs of different sites in self.storageelements.
    Contains (a,b) and (b,a)
    """
    return [(site1, site2) for site1 in self.storageelements for site2 in self.storageelements if site1 != site2]
