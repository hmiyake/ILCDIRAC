"""Contains general utility methods for unit testing.
"""

__RCSID__ = "$Id$"

def assertEqualsImproved( val1, val2, assertobject ):
  """Asserts that val1 and val2 are equal and automatically generates a meaningful error message. Only disadvantage is that you have to check 1 method up in the stacktrace.

  :param T val1: First value to be compared
  :param T val2: Second value, compared to val1
  :param TestCase assertobject: Testcase object, used to gain the base assertEquals method.
  """
  assertobject.assertEquals( val1, val2, "Test expected these values to be the same, but they were not!\n First value = %s,\n Second value = %s" % (repr(val1), repr(val2)) )

def assertInImproved( val1, val2, assertobject ):
  """Asserts that val1 is contained in val2 and automatically generates a meaningful error message. Only disadvantage is that you have to check 1 method up in the stacktrace.

  :param T val1: First value
  :param S val2: Second value, can contain val1
  :param TestCase assertobject: Testcase object, used to gain the base assertEquals method.
  """
  assertobject.assertIn( val1, val2, "Test expected these values to be the same, but they were not!\n First value = %s,\n Second value = %s" % (repr(val1), repr(val2)) )

def assertEqualsXml( elem1, elem2, assertobject ):
  """Asserts that the two passed XMLTree Elements are equal, i.e. have the same content, name, etc.
  """
  assertEqualsImproved( elem1.tag, elem2.tag, assertobject )
  assertEqualsImproved( elem1.text, elem2.text, assertobject )
  assertEqualsImproved( elem1.tail, elem2.tail, assertobject )
  assertEqualsImproved( elem1.attrib, elem2.attrib, assertobject )

def assertDiracFailsWith( result, errorstring, assertobject):
  """Asserts that result, which is the return value of a dirac method call, is an S_ERROR with errorstring contained in the error message (case insensitive).

  :param dict result: Structure (expected to be S_ERROR) returned by the dirac call
  :param string errorstring: String expected to be contained in the error message
  :param TestCase assertobject: Testcase object, used to gain the assertX methods.
  """
  assertobject.assertFalse( result['OK'] )
  assertobject.assertIn( errorstring.lower(), result['Message'].lower() )

def assertDiracSucceeds( result, assertobject ):
  """Asserts that result, which is the return value of a dirac method call, is an S_OK, else print out the error message.

  :param dict result: Structure (expected to be S_OK) returned by the dirac call
  :param TestCase assertobject: Testcase object, used to gain the assertX methods.
  """
  assertobject.assertTrue( result['OK'], result.get('Message', ''))

def assertDiracSucceedsWith( result, expected_val, assertobject ):
  """Asserts that result, which is the return value of a dirac method call, is an S_OK with expected_val in the returned value.

  :param dict result: Structure (expected to be S_OK) returned by the dirac call
  :param ? expected_val: Part of the value in the S_OK structure (checked with `in`)
  :param TestCase assertobject: Testcase object, used to gain the assertX methods.
  """
  assertDiracSucceeds( result, assertobject )
  assertobject.assertIn( expected_val, result['Value'] )

def assertDiracSucceedsWith_equals( result, expected_res, assertobject ):
  """Asserts that result, which is the return value of a dirac method call, is an S_OK containing exactly expected_res.

  :param dict result: Structure (expected to be S_OK) returned by the dirac call
  :param ? expected_res: Value that should be contained in the result.
  :param TestCase assertobject: Testcase object, used to gain the assertX methods.
  """
  assertDiracSucceeds( result, assertobject )
  assertobject.assertEquals( expected_res, result['Value'] )
