import doctest
import unittest

import cached_property as cached_property_module
from cached_property import cached_property


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(cached_property_module))
    return tests


class Tests(unittest.TestCase):
    def test(self):
        value = object()
        prop_call_count = 0

        class Class:
            @cached_property
            def prop(self):
                nonlocal prop_call_count
                prop_call_count += 1
                return value

        self.assertIsInstance(Class.prop, cached_property)
        self.assertEqual(Class.prop.__name__, "prop")

        instance = Class()

        self.assertNotIn("prop", instance.__dict__)

        computed_value = instance.prop
        self.assertIn("prop", instance.__dict__)
        self.assertIs(computed_value, value)
        self.assertEqual(prop_call_count, 1)

        computed_value = instance.prop
        self.assertIn("prop", instance.__dict__)
        self.assertIs(computed_value, value)
        self.assertEqual(prop_call_count, 1)

        del instance.prop
        self.assertNotIn("prop", instance.__dict__)
        self.assertEqual(prop_call_count, 1)

        computed_value = instance.prop
        self.assertIn("prop", instance.__dict__)
        self.assertIs(computed_value, value)
        self.assertEqual(prop_call_count, 2)
