##############################################################################
#
# Copyright (c) 2012 Zope Foundation and Contributors.
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
import doctest
import unittest

# pylint:disable=protected-access

class ConformanceMixin(object):

    def _getTargetClass(self):
        raise NotImplementedError

    def _getTargetInterface(self):
        raise NotImplementedError

    def _makeOne(self, *args, **kwargs):
        return self._makeOneFromClass(self._getTargetClass(),
                                      *args,
                                      **kwargs)

    def _makeOneFromClass(self, cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def test_class_conforms_to_iface(self):
        from zope.interface.verify import verifyClass
        cls = self._getTargetClass()
        __traceback_info__ = cls
        verifyClass(self._getTargetInterface(), cls)
        return verifyClass

    def test_instance_conforms_to_iface(self):
        from zope.interface.verify import verifyObject
        instance = self._makeOne()
        __traceback_info__ = instance
        verifyObject(self._getTargetInterface(), instance)
        return verifyObject


class EqualityTestsMixin(ConformanceMixin):

    def test_is_hashable(self):
        field = self._makeOne()
        hash(field)  # doesn't raise

    def test_equal_instances_have_same_hash(self):
        # Equal objects should have equal hashes
        field1 = self._makeOne()
        field2 = self._makeOne()
        self.assertIsNot(field1, field2)
        self.assertEqual(field1, field2)
        self.assertEqual(hash(field1), hash(field2))

    def test_instances_in_different_interfaces_not_equal(self):
        from zope import interface

        field1 = self._makeOne()
        field2 = self._makeOne()
        self.assertEqual(field1, field2)
        self.assertEqual(hash(field1), hash(field2))

        class IOne(interface.Interface):
            one = field1

        class ITwo(interface.Interface):
            two = field2

        self.assertEqual(field1, field1)
        self.assertEqual(field2, field2)
        self.assertNotEqual(field1, field2)
        self.assertNotEqual(hash(field1), hash(field2))

    def test_hash_across_unequal_instances(self):
        # Hash equality does not imply equal objects.
        # Our implementation only considers property names,
        # not values. That's OK, a dict still does the right thing.
        field1 = self._makeOne(title=u'foo')
        field2 = self._makeOne(title=u'bar')
        self.assertIsNot(field1, field2)
        self.assertNotEqual(field1, field2)
        self.assertEqual(hash(field1), hash(field2))

        d = {field1: 42}
        self.assertIn(field1, d)
        self.assertEqual(42, d[field1])
        self.assertNotIn(field2, d)
        with self.assertRaises(KeyError):
            d.__getitem__(field2)

    def test___eq___different_type(self):
        left = self._makeOne()

        class Derived(self._getTargetClass()):
            pass
        right = self._makeOneFromClass(Derived)
        self.assertNotEqual(left, right)
        self.assertTrue(left != right)

    def test___eq___same_type_different_attrs(self):
        left = self._makeOne(required=True)
        right = self._makeOne(required=False)
        self.assertNotEqual(left, right)
        self.assertTrue(left != right)

    def test___eq___same_type_same_attrs(self):
        left = self._makeOne()
        self.assertEqual(left, left)

        right = self._makeOne()
        self.assertEqual(left, right)
        self.assertFalse(left != right)


class OrderableMissingValueMixin(EqualityTestsMixin):
    mvm_missing_value = -1
    mvm_default = 0

    def test_missing_value_no_min_or_max(self):
        # We should be able to provide a missing_value without
        # also providing a min or max. But note that we must still
        # provide a default.
        # See https://github.com/zopefoundation/zope.schema/issues/9
        Kind = self._getTargetClass()
        self.assertTrue(Kind.min._allow_none)
        self.assertTrue(Kind.max._allow_none)

        field = self._makeOne(missing_value=self.mvm_missing_value,
                              default=self.mvm_default)
        self.assertIsNone(field.min)
        self.assertIsNone(field.max)
        self.assertEqual(self.mvm_missing_value, field.missing_value)


class ValidatedPropertyTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import ValidatedProperty
        return ValidatedProperty

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test___set___not_missing_w_check(self):
        _checked = []

        def _check(inst, value):
            _checked.append((inst, value))

        class Test(DummyInst):
            _prop = None
            prop = self._makeOne('_prop', _check)
        inst = Test()
        inst.prop = 'PROP'
        self.assertEqual(inst._prop, 'PROP')
        self.assertEqual(_checked, [(inst, 'PROP')])

    def test___set___not_missing_wo_check(self):
        class Test(DummyInst):
            _prop = None
            prop = self._makeOne('_prop')
        inst = Test(ValueError)

        def _provoke(inst):
            inst.prop = 'PROP'
        self.assertRaises(ValueError, _provoke, inst)
        self.assertEqual(inst._prop, None)

    def test___set___w_missing_wo_check(self):
        class Test(DummyInst):
            _prop = None
            prop = self._makeOne('_prop')
        inst = Test(ValueError)
        inst.prop = DummyInst.missing_value
        self.assertEqual(inst._prop, DummyInst.missing_value)

    def test___get__(self):
        class Test(DummyInst):
            _prop = None
            prop = self._makeOne('_prop')
        inst = Test()
        inst._prop = 'PROP'
        self.assertEqual(inst.prop, 'PROP')


class DefaultPropertyTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import DefaultProperty
        return DefaultProperty

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test___get___wo_defaultFactory_miss(self):
        class Test(DummyInst):
            _prop = None
            prop = self._makeOne('_prop')
        inst = Test()
        inst.defaultFactory = None

        def _provoke(inst):
            return inst.prop
        self.assertRaises(KeyError, _provoke, inst)

    def test___get___wo_defaultFactory_hit(self):
        class Test(DummyInst):
            _prop = None
            prop = self._makeOne('_prop')
        inst = Test()
        inst.defaultFactory = None
        inst._prop = 'PROP'
        self.assertEqual(inst.prop, 'PROP')

    def test__get___wo_defaultFactory_in_dict(self):
        class Test(DummyInst):
            _prop = None
            prop = self._makeOne('_prop')
        inst = Test()
        inst._prop = 'PROP'
        self.assertEqual(inst.prop, 'PROP')

    def test___get___w_defaultFactory_not_ICAF_no_check(self):
        class Test(DummyInst):
            _prop = None
            prop = self._makeOne('_prop')
        inst = Test(ValueError)

        def _factory():
            return 'PROP'
        inst.defaultFactory = _factory

        def _provoke(inst):
            return inst.prop
        self.assertRaises(ValueError, _provoke, inst)

    def test___get___w_defaultFactory_w_ICAF_w_check(self):
        from zope.interface import directlyProvides
        from zope.schema._bootstrapinterfaces \
            import IContextAwareDefaultFactory
        _checked = []

        def _check(inst, value):
            _checked.append((inst, value))

        class Test(DummyInst):
            _prop = None
            prop = self._makeOne('_prop', _check)
        inst = Test(ValueError)
        inst.context = object()
        _called_with = []

        def _factory(context):
            _called_with.append(context)
            return 'PROP'
        directlyProvides(_factory, IContextAwareDefaultFactory)
        inst.defaultFactory = _factory
        self.assertEqual(inst.prop, 'PROP')
        self.assertEqual(_checked, [(inst, 'PROP')])
        self.assertEqual(_called_with, [inst.context])


class FieldTests(EqualityTestsMixin,
                 unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Field
        return Field

    def _getTargetInterface(self):
        from zope.schema.interfaces import IField
        return IField

    def test_ctor_defaults(self):

        field = self._makeOne()
        self.assertEqual(field.__name__, u'')
        self.assertEqual(field.__doc__, u'')
        self.assertEqual(field.title, u'')
        self.assertEqual(field.description, u'')
        self.assertEqual(field.required, True)
        self.assertEqual(field.readonly, False)
        self.assertEqual(field.constraint(object()), True)
        self.assertEqual(field.default, None)
        self.assertEqual(field.defaultFactory, None)
        self.assertEqual(field.missing_value, None)
        self.assertEqual(field.context, None)

    def test_ctor_w_title_wo_description(self):

        field = self._makeOne(u'TITLE')
        self.assertEqual(field.__name__, u'')
        self.assertEqual(field.__doc__, u'TITLE')
        self.assertEqual(field.title, u'TITLE')
        self.assertEqual(field.description, u'')

    def test_ctor_wo_title_w_description(self):

        field = self._makeOne(description=u'DESC')
        self.assertEqual(field.__name__, u'')
        self.assertEqual(field.__doc__, u'DESC')
        self.assertEqual(field.title, u'')
        self.assertEqual(field.description, u'DESC')

    def test_ctor_w_both_title_and_description(self):

        field = self._makeOne(u'TITLE', u'DESC', u'NAME')
        self.assertEqual(field.__name__, u'NAME')
        self.assertEqual(field.__doc__, u'TITLE\n\nDESC')
        self.assertEqual(field.title, u'TITLE')
        self.assertEqual(field.description, u'DESC')

    def test_ctor_order_madness(self):
        klass = self._getTargetClass()
        order_before = klass.order
        field = self._makeOne()
        order_after = klass.order
        self.assertEqual(order_after, order_before + 1)
        self.assertEqual(field.order, order_after)

    def test_explicit_required_readonly_missingValue(self):
        obj = object()
        field = self._makeOne(required=False, readonly=True, missing_value=obj)
        self.assertEqual(field.required, False)
        self.assertEqual(field.readonly, True)
        self.assertEqual(field.missing_value, obj)

    def test_explicit_constraint_default(self):
        _called_with = []
        obj = object()

        def _constraint(value):
            _called_with.append(value)
            return value is obj
        field = self._makeOne(
            required=False, readonly=True, constraint=_constraint, default=obj
        )
        self.assertEqual(field.required, False)
        self.assertEqual(field.readonly, True)
        self.assertEqual(_called_with, [obj])
        self.assertEqual(field.constraint(self), False)
        self.assertEqual(_called_with, [obj, self])
        self.assertEqual(field.default, obj)

    def test_explicit_defaultFactory(self):
        _called_with = []
        obj = object()

        def _constraint(value):
            _called_with.append(value)
            return value is obj

        def _factory():
            return obj
        field = self._makeOne(
            required=False,
            readonly=True,
            constraint=_constraint,
            defaultFactory=_factory,
        )
        self.assertEqual(field.required, False)
        self.assertEqual(field.readonly, True)
        self.assertEqual(field.constraint(self), False)
        self.assertEqual(_called_with, [self])
        self.assertEqual(field.default, obj)
        self.assertEqual(_called_with, [self, obj])
        self.assertEqual(field.defaultFactory, _factory)

    def test_explicit_defaultFactory_returning_missing_value(self):
        def _factory():
            return None
        field = self._makeOne(required=True,
                              defaultFactory=_factory)
        self.assertEqual(field.default, None)

    def test_bind(self):
        obj = object()
        field = self._makeOne()
        bound = field.bind(obj)
        self.assertEqual(bound.context, obj)
        expected = dict(field.__dict__)
        found = dict(bound.__dict__)
        found.pop('context')
        self.assertEqual(found, expected)
        self.assertEqual(bound.__class__, field.__class__)

    def test_validate_missing_not_required(self):
        missing = object()

        field = self._makeOne(
            required=False, missing_value=missing, constraint=lambda x: False,
        )
        self.assertEqual(field.validate(missing), None)  # doesn't raise

    def test_validate_missing_and_required(self):
        from zope.schema._bootstrapinterfaces import RequiredMissing
        missing = object()

        field = self._makeOne(
            required=True, missing_value=missing, constraint=lambda x: False,
        )
        self.assertRaises(RequiredMissing, field.validate, missing)

    def test_validate_wrong_type(self):
        from zope.schema._bootstrapinterfaces import WrongType

        field = self._makeOne(required=True, constraint=lambda x: False)
        field._type = str
        self.assertRaises(WrongType, field.validate, 1)

    def test_validate_constraint_fails(self):
        from zope.schema._bootstrapinterfaces import ConstraintNotSatisfied

        field = self._makeOne(required=True, constraint=lambda x: False)
        field._type = int
        self.assertRaises(ConstraintNotSatisfied, field.validate, 1)

    def test_validate_constraint_raises_StopValidation(self):
        from zope.schema._bootstrapinterfaces import StopValidation

        def _fail(value):
            raise StopValidation
        field = self._makeOne(required=True, constraint=_fail)
        field._type = int
        field.validate(1)  # doesn't raise

    def test_get_miss(self):
        field = self._makeOne(__name__='nonesuch')
        inst = DummyInst()
        self.assertRaises(AttributeError, field.get, inst)

    def test_get_hit(self):
        field = self._makeOne(__name__='extant')
        inst = DummyInst()
        inst.extant = 'EXTANT'
        self.assertEqual(field.get(inst), 'EXTANT')

    def test_query_miss_no_default(self):
        field = self._makeOne(__name__='nonesuch')
        inst = DummyInst()
        self.assertEqual(field.query(inst), None)

    def test_query_miss_w_default(self):
        field = self._makeOne(__name__='nonesuch')
        inst = DummyInst()
        self.assertEqual(field.query(inst, 'DEFAULT'), 'DEFAULT')

    def test_query_hit(self):
        field = self._makeOne(__name__='extant')
        inst = DummyInst()
        inst.extant = 'EXTANT'
        self.assertEqual(field.query(inst), 'EXTANT')

    def test_set_readonly(self):
        field = self._makeOne(__name__='lirame', readonly=True)
        inst = DummyInst()
        self.assertRaises(TypeError, field.set, inst, 'VALUE')

    def test_set_hit(self):
        field = self._makeOne(__name__='extant')
        inst = DummyInst()
        inst.extant = 'BEFORE'
        field.set(inst, 'AFTER')
        self.assertEqual(inst.extant, 'AFTER')


class ContainerTests(EqualityTestsMixin,
                     unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Container
        return Container

    def _getTargetInterface(self):
        from zope.schema.interfaces import IContainer
        return IContainer

    def test_validate_not_required(self):
        field = self._makeOne(required=False)
        field.validate(None)

    def test_validate_required(self):
        from zope.schema.interfaces import RequiredMissing
        field = self._makeOne()
        self.assertRaises(RequiredMissing, field.validate, None)

    def test__validate_not_collection_not_iterable(self):
        from zope.schema._bootstrapinterfaces import NotAContainer
        cont = self._makeOne()
        bad_value = object()
        with self.assertRaises(NotAContainer) as exc:
            cont._validate(bad_value)

        not_cont = exc.exception
        self.assertIs(not_cont.field, cont)
        self.assertIs(not_cont.value, bad_value)

    def test__validate_collection_but_not_iterable(self):
        cont = self._makeOne()

        class Dummy(object):
            def __contains__(self, item):
                raise AssertionError("Not called")
        cont._validate(Dummy())  # doesn't raise

    def test__validate_not_collection_but_iterable(self):
        cont = self._makeOne()

        class Dummy(object):
            def __iter__(self):
                return iter(())
        cont._validate(Dummy())  # doesn't raise

    def test__validate_w_collections(self):
        cont = self._makeOne()
        cont._validate(())  # doesn't raise
        cont._validate([])  # doesn't raise
        cont._validate('')  # doesn't raise
        cont._validate({})  # doesn't raise


class IterableTests(ContainerTests):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Iterable
        return Iterable

    def _getTargetInterface(self):
        from zope.schema.interfaces import IIterable
        return IIterable

    def test__validate_collection_but_not_iterable(self):
        from zope.schema._bootstrapinterfaces import NotAnIterator
        itr = self._makeOne()

        class Dummy(object):
            def __contains__(self, item):
                raise AssertionError("Not called")
        dummy = Dummy()
        with self.assertRaises(NotAnIterator) as exc:
            itr._validate(dummy)

        not_it = exc.exception
        self.assertIs(not_it.field, itr)
        self.assertIs(not_it.value, dummy)


class OrderableTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Orderable
        return Orderable

    def _makeOne(self, *args, **kw):
        # Orderable is a mixin for a type derived from Field
        from zope.schema._bootstrapfields import Field

        class Mixed(self._getTargetClass(), Field):
            pass
        return Mixed(*args, **kw)

    def test_ctor_defaults(self):
        ordb = self._makeOne()
        self.assertEqual(ordb.min, None)
        self.assertEqual(ordb.max, None)
        self.assertEqual(ordb.default, None)

    def test_ctor_default_too_small(self):
        # This test exercises _validate, too
        from zope.schema._bootstrapinterfaces import TooSmall
        self.assertRaises(TooSmall, self._makeOne, min=0, default=-1)

    def test_ctor_default_too_large(self):
        # This test exercises _validate, too
        from zope.schema._bootstrapinterfaces import TooBig
        self.assertRaises(TooBig, self._makeOne, max=10, default=11)


class MinMaxLenTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import MinMaxLen
        return MinMaxLen

    def _makeOne(self, *args, **kw):
        # MinMaxLen is a mixin for a type derived from Field
        from zope.schema._bootstrapfields import Field

        class Mixed(self._getTargetClass(), Field):
            pass
        return Mixed(*args, **kw)

    def test_ctor_defaults(self):
        mml = self._makeOne()
        self.assertEqual(mml.min_length, 0)
        self.assertEqual(mml.max_length, None)

    def test_validate_too_short(self):
        from zope.schema._bootstrapinterfaces import TooShort
        mml = self._makeOne(min_length=1)
        self.assertRaises(TooShort, mml._validate, ())

    def test_validate_too_long(self):
        from zope.schema._bootstrapinterfaces import TooLong
        mml = self._makeOne(max_length=2)
        self.assertRaises(TooLong, mml._validate, (0, 1, 2))


class TextTests(EqualityTestsMixin,
                unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Text
        return Text

    def _getTargetInterface(self):
        from zope.schema.interfaces import IText
        return IText

    def test_ctor_defaults(self):
        from zope.schema._compat import text_type
        txt = self._makeOne()
        self.assertEqual(txt._type, text_type)

    def test_validate_wrong_types(self):
        from zope.schema.interfaces import WrongType

        field = self._makeOne()
        self.assertRaises(WrongType, field.validate, b'')
        self.assertRaises(WrongType, field.validate, 1)
        self.assertRaises(WrongType, field.validate, 1.0)
        self.assertRaises(WrongType, field.validate, ())
        self.assertRaises(WrongType, field.validate, [])
        self.assertRaises(WrongType, field.validate, {})
        self.assertRaises(WrongType, field.validate, set())
        self.assertRaises(WrongType, field.validate, frozenset())
        self.assertRaises(WrongType, field.validate, object())

    def test_validate_w_invalid_default(self):

        from zope.schema.interfaces import ValidationError
        self.assertRaises(ValidationError, self._makeOne, default=b'')

    def test_validate_not_required(self):

        field = self._makeOne(required=False)
        field.validate(u'')
        field.validate(u'abc')
        field.validate(u'abc\ndef')
        field.validate(None)

    def test_validate_required(self):
        from zope.schema.interfaces import RequiredMissing

        field = self._makeOne()
        field.validate(u'')
        field.validate(u'abc')
        field.validate(u'abc\ndef')
        self.assertRaises(RequiredMissing, field.validate, None)

    def test_fromUnicode_miss(self):
        from zope.schema._bootstrapinterfaces import WrongType

        deadbeef = b'DEADBEEF'
        txt = self._makeOne()
        self.assertRaises(WrongType, txt.fromUnicode, deadbeef)

    def test_fromUnicode_hit(self):

        deadbeef = u'DEADBEEF'
        txt = self._makeOne()
        self.assertEqual(txt.fromUnicode(deadbeef), deadbeef)


class TextLineTests(EqualityTestsMixin,
                    unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._field import TextLine
        return TextLine

    def _getTargetInterface(self):
        from zope.schema.interfaces import ITextLine
        return ITextLine

    def test_validate_wrong_types(self):
        from zope.schema.interfaces import WrongType

        field = self._makeOne()
        self.assertRaises(WrongType, field.validate, b'')
        self.assertRaises(WrongType, field.validate, 1)
        self.assertRaises(WrongType, field.validate, 1.0)
        self.assertRaises(WrongType, field.validate, ())
        self.assertRaises(WrongType, field.validate, [])
        self.assertRaises(WrongType, field.validate, {})
        self.assertRaises(WrongType, field.validate, set())
        self.assertRaises(WrongType, field.validate, frozenset())
        self.assertRaises(WrongType, field.validate, object())

    def test_validate_not_required(self):

        field = self._makeOne(required=False)
        field.validate(u'')
        field.validate(u'abc')
        field.validate(None)

    def test_validate_required(self):
        from zope.schema.interfaces import RequiredMissing

        field = self._makeOne()
        field.validate(u'')
        field.validate(u'abc')
        self.assertRaises(RequiredMissing, field.validate, None)

    def test_constraint(self):

        field = self._makeOne()
        self.assertEqual(field.constraint(u''), True)
        self.assertEqual(field.constraint(u'abc'), True)
        self.assertEqual(field.constraint(u'abc\ndef'), False)


class PasswordTests(EqualityTestsMixin,
                    unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Password
        return Password

    def _getTargetInterface(self):
        from zope.schema.interfaces import IPassword
        return IPassword

    def test_set_unchanged(self):
        klass = self._getTargetClass()
        pw = self._makeOne()
        inst = DummyInst()
        before = dict(inst.__dict__)
        pw.set(inst, klass.UNCHANGED_PASSWORD)  # doesn't raise, doesn't write
        after = dict(inst.__dict__)
        self.assertEqual(after, before)

    def test_set_normal(self):
        pw = self._makeOne(__name__='password')
        inst = DummyInst()
        pw.set(inst, 'PASSWORD')
        self.assertEqual(inst.password, 'PASSWORD')

    def test_validate_not_required(self):

        field = self._makeOne(required=False)
        field.validate(u'')
        field.validate(u'abc')
        field.validate(None)

    def test_validate_required(self):
        from zope.schema.interfaces import RequiredMissing

        field = self._makeOne()
        field.validate(u'')
        field.validate(u'abc')
        self.assertRaises(RequiredMissing, field.validate, None)

    def test_validate_unchanged_not_already_set(self):
        from zope.schema._bootstrapinterfaces import WrongType
        klass = self._getTargetClass()
        inst = DummyInst()
        pw = self._makeOne(__name__='password').bind(inst)
        self.assertRaises(WrongType,
                          pw.validate, klass.UNCHANGED_PASSWORD)

    def test_validate_unchanged_already_set(self):
        klass = self._getTargetClass()
        inst = DummyInst()
        inst.password = 'foobar'
        pw = self._makeOne(__name__='password').bind(inst)
        pw.validate(klass.UNCHANGED_PASSWORD)  # doesn't raise

    def test_constraint(self):

        field = self._makeOne()
        self.assertEqual(field.constraint(u''), True)
        self.assertEqual(field.constraint(u'abc'), True)
        self.assertEqual(field.constraint(u'abc\ndef'), False)


class BoolTests(EqualityTestsMixin,
                unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Bool
        return Bool

    def _getTargetInterface(self):
        from zope.schema.interfaces import IBool
        return IBool

    def test_ctor_defaults(self):
        txt = self._makeOne()
        self.assertEqual(txt._type, bool)

    def test__validate_w_int(self):
        boo = self._makeOne()
        boo._validate(0)  # doesn't raise
        boo._validate(1)  # doesn't raise

    def test_set_w_int(self):
        boo = self._makeOne(__name__='boo')
        inst = DummyInst()
        boo.set(inst, 0)
        self.assertEqual(inst.boo, False)
        boo.set(inst, 1)
        self.assertEqual(inst.boo, True)

    def test_fromUnicode_miss(self):

        txt = self._makeOne()
        self.assertEqual(txt.fromUnicode(u''), False)
        self.assertEqual(txt.fromUnicode(u'0'), False)
        self.assertEqual(txt.fromUnicode(u'1'), False)
        self.assertEqual(txt.fromUnicode(u'False'), False)
        self.assertEqual(txt.fromUnicode(u'false'), False)

    def test_fromUnicode_hit(self):

        txt = self._makeOne()
        self.assertEqual(txt.fromUnicode(u'True'), True)
        self.assertEqual(txt.fromUnicode(u'true'), True)


class NumberTests(OrderableMissingValueMixin,
                  unittest.TestCase):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Number
        return Number

    def _getTargetInterface(self):
        from zope.schema.interfaces import INumber
        return INumber

    def test_class_conforms_to_iface(self):
        from zope.schema._bootstrapinterfaces import IFromUnicode
        verifyClass = super(NumberTests, self).test_class_conforms_to_iface()
        verifyClass(IFromUnicode, self._getTargetClass())

    def test_instance_conforms_to_iface(self):
        from zope.schema._bootstrapinterfaces import IFromUnicode
        verifyObject = super(NumberTests, self).test_instance_conforms_to_iface()
        verifyObject(IFromUnicode, self._makeOne())


class ComplexTests(NumberTests):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Complex
        return Complex

    def _getTargetInterface(self):
        from zope.schema.interfaces import IComplex
        return IComplex

class RealTests(NumberTests):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Real
        return Real

    def _getTargetInterface(self):
        from zope.schema.interfaces import IReal
        return IReal

    def test_ctor_real_min_max(self):
        from zope.schema.interfaces import WrongType
        from zope.schema.interfaces import TooSmall
        from zope.schema.interfaces import TooBig
        from fractions import Fraction

        with self.assertRaises(WrongType):
            self._makeOne(min='')
        with self.assertRaises(WrongType):
            self._makeOne(max='')

        field = self._makeOne(min=Fraction(1, 2), max=2)
        field.validate(1.0)
        field.validate(2.0)
        self.assertRaises(TooSmall, field.validate, 0)
        self.assertRaises(TooSmall, field.validate, 0.4)
        self.assertRaises(TooBig, field.validate, 2.1)

class RationalTests(NumberTests):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Rational
        return Rational

    def _getTargetInterface(self):
        from zope.schema.interfaces import IRational
        return IRational


class IntegralTests(RationalTests):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Integral
        return Integral

    def _getTargetInterface(self):
        from zope.schema.interfaces import IIntegral
        return IIntegral

    def test_validate_not_required(self):
        field = self._makeOne(required=False)
        field.validate(None)
        field.validate(10)
        field.validate(0)
        field.validate(-1)

    def test_validate_required(self):
        from zope.schema.interfaces import RequiredMissing
        field = self._makeOne()
        field.validate(10)
        field.validate(0)
        field.validate(-1)
        self.assertRaises(RequiredMissing, field.validate, None)

    def test_validate_min(self):
        from zope.schema.interfaces import TooSmall
        field = self._makeOne(min=10)
        field.validate(10)
        field.validate(20)
        self.assertRaises(TooSmall, field.validate, 9)
        self.assertRaises(TooSmall, field.validate, -10)

    def test_validate_max(self):
        from zope.schema.interfaces import TooBig
        field = self._makeOne(max=10)
        field.validate(5)
        field.validate(9)
        field.validate(10)
        self.assertRaises(TooBig, field.validate, 11)
        self.assertRaises(TooBig, field.validate, 20)

    def test_validate_min_and_max(self):
        from zope.schema.interfaces import TooBig
        from zope.schema.interfaces import TooSmall
        field = self._makeOne(min=0, max=10)
        field.validate(0)
        field.validate(5)
        field.validate(10)
        self.assertRaises(TooSmall, field.validate, -10)
        self.assertRaises(TooSmall, field.validate, -1)
        self.assertRaises(TooBig, field.validate, 11)
        self.assertRaises(TooBig, field.validate, 20)

    def test_fromUnicode_miss(self):

        txt = self._makeOne()
        self.assertRaises(ValueError, txt.fromUnicode, u'')
        self.assertRaises(ValueError, txt.fromUnicode, u'False')
        self.assertRaises(ValueError, txt.fromUnicode, u'True')

    def test_fromUnicode_hit(self):

        txt = self._makeOne()
        self.assertEqual(txt.fromUnicode(u'0'), 0)
        self.assertEqual(txt.fromUnicode(u'1'), 1)
        self.assertEqual(txt.fromUnicode(u'-1'), -1)


class IntTests(IntegralTests):

    def _getTargetClass(self):
        from zope.schema._bootstrapfields import Int
        return Int

    def _getTargetInterface(self):
        from zope.schema.interfaces import IInt
        return IInt

    def test_ctor_defaults(self):
        from zope.schema._compat import integer_types
        txt = self._makeOne()
        self.assertEqual(txt._type, integer_types)


class DummyInst(object):
    missing_value = object()

    def __init__(self, exc=None):
        self._exc = exc

    def validate(self, value):
        if self._exc is not None:
            raise self._exc()


def test_suite():
    import zope.schema._bootstrapfields
    suite = unittest.defaultTestLoader.loadTestsFromName(__name__)
    suite.addTests(doctest.DocTestSuite(zope.schema._bootstrapfields))
    return suite
