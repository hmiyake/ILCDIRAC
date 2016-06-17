"""
Tests for PrepareLibs

"""
import unittest
from mock import mock_open, patch, MagicMock as Mock

from DIRAC import S_OK, S_ERROR
from ILCDIRAC.Core.Utilities.PrepareLibs import removeLibc, main
from ILCDIRAC.Tests.Utilities.GeneralUtils import assertEqualsXml, assertEqualsImproved, assertDiracFailsWith, assertDiracSucceeds, assertDiracSucceedsWith_equals

__RCSID__ = "$Id$"

MODULE_NAME = 'ILCDIRAC.Core.Utilities.PrepareLibs'

class TestPrepareLibs( unittest.TestCase ):
  """ Tests the removeLibc method
  """
  def test_remove_libc( self ):
    with patch( '%s.os.getcwd' % MODULE_NAME, new=Mock(side_effect=[ 'current_dir', 'mytestpath', 'mytestpath', 'mytestpath' ]) ) as getcwd_mock, \
         patch( '%s.os.chdir' % MODULE_NAME, new=Mock(return_value=True) ) as chdir_mock, \
         patch( '%s.os.remove' % MODULE_NAME, new=Mock(return_value=True) ) as remove_mock, \
         patch( '%s.os.listdir' % MODULE_NAME, new=Mock(return_value=[ 'directory_content1.txt', 'libc.so', 'libstdc++.so' ]) ) as listdir_mock:
      result = removeLibc( 'mytestpath' )
      self.assertTrue( result )
      chdir_mock.assert_any_call( 'mytestpath' )
      chdir_mock.assert_called_with( 'current_dir' )
      assertEqualsImproved( len( chdir_mock.mock_calls ), 2, self )
      listdir_mock.assert_called_once_with( 'mytestpath' )
      remove_mock.assert_any_call( 'mytestpath/libc.so' )
      remove_mock.assert_called_with( 'mytestpath/libstdc++.so' )
      assertEqualsImproved( len( remove_mock.mock_calls ), 2, self )
      getcwd_mock.assert_called_with()
      assertEqualsImproved( len( getcwd_mock.mock_calls ), 4, self )

  def test_remove_libc_chdir_fails( self ):
    with patch( '%s.os.getcwd' % MODULE_NAME, new=Mock(side_effect=[ 'current_dir', 'mytestpath', 'mytestpath', 'mytestpath' ]) ) as getcwd_mock, \
         patch( '%s.os.chdir' % MODULE_NAME, new=Mock(side_effect=OSError( 'chdir_test_os_err' )) ) as chdir_mock, \
         patch( '%s.os.remove' % MODULE_NAME, new=Mock(return_value=True) ) as remove_mock, \
         patch( '%s.os.listdir' % MODULE_NAME, new=Mock(return_value=[ 'directory_content1.txt', 'libc.so', 'libstdc++.so' ]) ) as listdir_mock:
      result = removeLibc( 'mytestpath' )
      self.assertTrue( result )
      chdir_mock.assert_called_once_with( 'mytestpath' )
      self.assertFalse( listdir_mock.called )
      self.assertFalse( remove_mock.called )
      getcwd_mock.assert_called_once_with()

  def test_remove_libc_remove_fails( self ):
    with patch( '%s.os.getcwd' % MODULE_NAME, new=Mock(side_effect=[ 'current_dir', 'mytestpath', 'mytestpath', 'mytestpath' ]) ) as getcwd_mock, \
         patch( '%s.os.chdir' % MODULE_NAME, new=Mock(return_value=True) ) as chdir_mock, \
         patch( '%s.os.remove' % MODULE_NAME, new=Mock(side_effect=OSError( 'test_cannot_remove_os_err' )) ) as remove_mock, \
         patch( '%s.os.listdir' % MODULE_NAME, new=Mock(return_value=[ 'directory_content1.txt', 'libc.so', 'libstdc++.so' ]) ) as listdir_mock:
      result = removeLibc( 'mytestpath' )
      self.assertFalse( result )
      chdir_mock.assert_any_call( 'mytestpath' )
      chdir_mock.assert_called_with( 'current_dir' )
      assertEqualsImproved( len( chdir_mock.mock_calls ), 2, self )
      listdir_mock.assert_called_once_with( 'mytestpath' )
      remove_mock.assert_called_once_with( 'mytestpath/libc.so' )
      getcwd_mock.assert_called_with()
      assertEqualsImproved( len( getcwd_mock.mock_calls ), 3, self )

  def test_remove_libc_nothing_to_remove( self ):
    with patch( '%s.os.getcwd' % MODULE_NAME, new=Mock(side_effect=[ 'current_dir', 'mytestpath', 'mytestpath', 'mytestpath' ]) ) as getcwd_mock, \
         patch( '%s.os.chdir' % MODULE_NAME, new=Mock(return_value=True) ) as chdir_mock, \
         patch( '%s.os.remove' % MODULE_NAME, new=Mock(return_value=True) ) as remove_mock, \
         patch( '%s.os.listdir' % MODULE_NAME, new=Mock(return_value=[ 'directory_content1.txt', 'not_a_library.txt', 'dont_delete_me_libsomething.so', 'innocentlibc_.so' ]) ) as listdir_mock:
      result = removeLibc( 'mytestpath' )
      self.assertTrue( result )
      chdir_mock.assert_any_call( 'mytestpath' )
      chdir_mock.assert_called_with( 'current_dir' )
      assertEqualsImproved( len( chdir_mock.mock_calls ), 2, self )
      listdir_mock.assert_called_once_with( 'mytestpath' )
      self.assertFalse( remove_mock.called )
      getcwd_mock.assert_called_with()
      assertEqualsImproved( len( getcwd_mock.mock_calls ), 2, self )

  def test_main( self ):
    with patch('%s.exit' % MODULE_NAME, new=Mock(return_value=True), create=True) as exit_mock, \
         patch('%s.sys.argv' % MODULE_NAME, new=Mock(return_value=[ 'something', 'myothertestpath' ])), \
         patch( '%s.os.getcwd' % MODULE_NAME, new=Mock(side_effect=[ 'current_dir', 'myothertestpath', 'myothertestpath', 'myothertestpath' ]) ), \
         patch( '%s.os.chdir' % MODULE_NAME, new=Mock(return_value=True) ), \
         patch( '%s.os.remove' % MODULE_NAME, new=Mock(return_value=True) ), \
         patch( '%s.os.listdir' % MODULE_NAME, new=Mock(return_value=[ 'directory_content1.txt', 'libc.so', 'libstdc++.so' ]) ):
      main()
      exit_mock.assert_called_once_with( 0 )

  def test_main_no_args( self ):
    with patch('%s.exit' % MODULE_NAME, new=Mock(return_value=True), create=True) as exit_mock, \
         patch('%s.sys.argv' % MODULE_NAME, new=Mock(return_value=[ 'something', 'myothertestpath' ])), \
         patch( '%s.os.getcwd' % MODULE_NAME, new=Mock(side_effect=[ 'current_dir', 'myothertestpath', 'myothertestpath', 'myothertestpath' ]) ), \
         patch( '%s.os.chdir' % MODULE_NAME, new=Mock(return_value=True) ), \
         patch( '%s.os.remove' % MODULE_NAME, new=Mock(return_value=True) ), \
         patch( '%s.os.listdir' % MODULE_NAME, new=Mock(return_value=[ 'directory_content1.txt', 'libc.so', 'libstdc++.so' ]) ):
      main()
      exit_mock.assert_called_once_with( 1 )

  def test_main_remove_fails( self ):
    with patch('%s.exit' % MODULE_NAME, new=Mock(return_value=True), create=True) as exit_mock, \
         patch('%s.sys.argv' % MODULE_NAME, new=Mock(return_value=[ 'something', 'myothertestpath' ])), \
         patch( '%s.os.getcwd' % MODULE_NAME, new=Mock(side_effect=[ 'current_dir', 'myothertestpath', 'myothertestpath', 'myothertestpath' ]) ), \
         patch( '%s.os.chdir' % MODULE_NAME, new=Mock(return_value=True) ), \
         patch( '%s.os.remove' % MODULE_NAME, new=Mock(side_effect=OSError( 'test_cannot_remove_os_err' )) ), \
         patch( '%s.os.listdir' % MODULE_NAME, new=Mock(return_value=[ 'directory_content1.txt', 'libc.so', 'libstdc++.so' ]) ):
      main()
      exit_mock.assert_called_once_with( 1 )

