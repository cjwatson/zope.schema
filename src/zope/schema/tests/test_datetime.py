##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Datetime Field tests
"""
import unittest

from zope.schema.tests.test_field import FieldTestBase

class DatetimeTest(FieldTestBase):
    """Test the Datetime Field."""

    def _getTargetClass(self):
        from zope.schema import Datetime
        return Datetime

    def testValidate(self):
        from datetime import datetime
        from six import u
        field = self._makeOne(title=u('Datetime field'), description=u(''),
                                    readonly=False, required=False)
        field.validate(None)
        field.validate(datetime.now())

    def testValidateRequired(self):
        from datetime import datetime
        from six import u
        from zope.schema.interfaces import RequiredMissing
        field = self._makeOne(title=u('Datetime field'), description=u(''),
                                    readonly=False, required=True)
        field.validate(datetime.now())

        self.assertRaises(RequiredMissing, field.validate, None)

    def testValidateMin(self):
        from datetime import datetime
        from six import u
        from zope.schema.interfaces import TooSmall
        d1 = datetime(2000,10,1)
        d2 = datetime(2000,10,2)
        field = self._makeOne(title=u('Datetime field'), description=u(''),
                                    readonly=False, required=False, min=d1)
        field.validate(None)
        field.validate(d1)
        field.validate(d2)
        field.validate(datetime.now())

        self.assertRaises(TooSmall, field.validate, datetime(2000,9,30))

    def testValidateMax(self):
        from datetime import datetime
        from six import u
        from zope.schema.interfaces import TooBig
        d1 = datetime(2000,10,1)
        d2 = datetime(2000,10,2)
        d3 = datetime(2000,10,3)
        field = self._makeOne(title=u('Datetime field'), description=u(''),
                                    readonly=False, required=False, max=d2)
        field.validate(None)
        field.validate(d1)
        field.validate(d2)

        self.assertRaises(TooBig, field.validate, d3)

    def testValidateMinAndMax(self):
        from datetime import datetime
        from six import u
        from zope.schema.interfaces import TooBig
        from zope.schema.interfaces import TooSmall
        d1 = datetime(2000,10,1)
        d2 = datetime(2000,10,2)
        d3 = datetime(2000,10,3)
        d4 = datetime(2000,10,4)
        d5 = datetime(2000,10,5)

        field = self._makeOne(title=u('Datetime field'), description=u(''),
                                    readonly=False, required=False,
                                    min=d2, max=d4)
        field.validate(None)
        field.validate(d2)
        field.validate(d3)
        field.validate(d4)

        self.assertRaises(TooSmall, field.validate, d1)
        self.assertRaises(TooBig, field.validate, d5)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DatetimeTest),
    ))
