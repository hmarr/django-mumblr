from django.conf import settings
from django.test import TestCase
from django.test.simple import (setup_test_environment, reorder_suite,
                                build_test, build_suite, get_app, get_apps, 
                                teardown_test_environment)
import unittest

def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    """Run the unit tests without using the ORM.
    """
    setup_test_environment()

    settings.DEBUG = False
    settings.DATABASE_SUPPORTS_TRANSACTIONS = False
    suite = unittest.TestSuite()

    if test_labels:
        for label in test_labels:
            if '.' in label:
                suite.addTest(build_test(label))
            else:
                app = get_app(label)
                suite.addTest(build_suite(app))
    else:
        for app in get_apps():
            suite.addTest(build_suite(app))

    for test in extra_tests:
        suite.addTest(test)

    suite = reorder_suite(suite, (TestCase,))

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    teardown_test_environment()

    return len(result.failures) + len(result.errors)
