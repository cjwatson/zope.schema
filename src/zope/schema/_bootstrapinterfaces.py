##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
"""Bootstrap schema interfaces and exceptions
"""
from functools import total_ordering

import zope.interface

from zope.schema._messageid import _


class StopValidation(Exception):
    """Raised if the validation is completed early.

    Note that this exception should be always caught, since it is just
    a way for the validator to save time.
    """


@total_ordering
class ValidationError(zope.interface.Invalid):
    """Raised if the Validation process fails."""

    #: The field that raised the error, if known.
    field = None

    #: The value that failed validation.
    value = None

    def with_field_and_value(self, field, value):
        self.field = field
        self.value = value
        return self

    def doc(self):
        return self.__class__.__doc__

    def __lt__(self, other):
        # There's no particular reason we choose to sort this way,
        # it's just the way we used to do it with __cmp__.
        if not hasattr(other, 'args'):
            return True
        return self.args < other.args

    def __eq__(self, other):
        if not hasattr(other, 'args'):
            return False
        return self.args == other.args

    # XXX : This is probably inconsistent with __eq__, which is
    # a violation of the language spec.
    __hash__ = zope.interface.Invalid.__hash__  # python3

    def __repr__(self):  # pragma: no cover
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join(repr(arg) for arg in self.args))


class RequiredMissing(ValidationError):
    __doc__ = _("""Required input is missing.""")


class WrongType(ValidationError):
    __doc__ = _("""Object is of wrong type.""")


class TooBig(ValidationError):
    __doc__ = _("""Value is too big""")


class TooSmall(ValidationError):
    __doc__ = _("""Value is too small""")


class TooLong(ValidationError):
    __doc__ = _("""Value is too long""")


class TooShort(ValidationError):
    __doc__ = _("""Value is too short""")


class InvalidValue(ValidationError):
    __doc__ = _("""Invalid value""")


class ConstraintNotSatisfied(ValidationError):
    __doc__ = _("""Constraint not satisfied""")


class NotAContainer(ValidationError):
    __doc__ = _("""Not a container""")


class NotAnIterator(ValidationError):
    __doc__ = _("""Not an iterator""")


class IFromUnicode(zope.interface.Interface):
    """Parse a unicode string to a value

    We will often adapt fields to this interface to support views and
    other applications that need to convert raw data as unicode
    values.
    """

    def fromUnicode(str):
        """Convert a unicode string to a value.
        """


class IContextAwareDefaultFactory(zope.interface.Interface):
    """A default factory that requires a context.

    The context is the field context. If the field is not bound, context may
    be ``None``.
    """

    def __call__(context):
        """Returns a default value for the field."""


class NO_VALUE(object):
    def __repr__(self): # pragma: no cover
        return '<NO_VALUE>'

NO_VALUE = NO_VALUE()
