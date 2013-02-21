#!/usr/bin/env python
# encoding: utf-8

__author__    = ["Ole Weidner", "Andre Merzky"]
__copyright__ = "Copyright 2012-2013, The SAGA Project"
__license__   = "MIT"

import re
import os
import sys
import glob
import nose

import saga.utils.test_config as sutc
from optparse import OptionParser

"""
This script runs a set of unit tests, which are organized in a directory
structure under ``tests/unittests/`` -- each sub-directory in that hierarchy
represents a test suite to be run.

The test suites expects the python environment to be set up in a way that the
sage module is automatically found.  Also, it needs the ``nose`` module
installed (``easy_install nose`` should do the trick), which provides the
nosetests testing framework.

A set of config files (test_*.cfg) in ``tests/unittests/`` is used to configure
how the individual test suites are run.  The script accepts string parameters
which are interpreted as filters to limit the set of accepted test config files.
For example, the argument *job* would enable the test configuration
*test_local_job.cfg*, but not *test_local_file.cfg*.

The config files are in particular used to accomodate remote unit testing, i.e.
to run the unit tests against arbitrary remote backends.  An example config file
is::

    # this config file will run the job package unit tests against
    # over a local ssh connection

    [saga.tests]
    test_suites        = engine,api/job

    job_service_url    = ssh://localhost/
    filesystem_url     =
    replica_url        =
    advert_url         =

    context_type       = ssh
    context_user_id    = peer_gynt
    context_user_pass  =
    context_user_proxy =
    context_user_cert  =

The above listing includes the complete set of supported attributes -- missing
entries are assumed to be empty strings, and can be left out.  The
``test_suites`` attribute MUST be set to include a list of test suites to run
against the given configuration.

The unit tests in the individual test suites will have access to the same
configuration info, and will use the given URL and context parameters to set up
the test environment.  For example, the api/job/test_service.py unit test will
use the following::

    import saga.utils.test_config as sutc
    ...

    tc = sutc.TestConfig ()
    js = saga.job.Service (tc.js_url, tc.session)

The :class:`saga.utils.test_config.TestConfig` class will expose the currently
active test configuration -- which is activated in the *run_unittests* script
as follows::

    tc = sutc.TestConfig ()
    tc.read_config (sfg_name)

Since :class:`saga.utils.test_config.TestConfig` is
a :class:`saga.utils.singleton.Singleton`, the thusly set state will be shared
with the test suites as shown.

"""


#-----------------------------------------------------------------------------
#
def launch_tests(options):

    # test_cfgs will contain a list of all configuation files
    # that we will use for the tests
    test_cfgs = []

    for config in options.config.split(","):
        if os.path.exists(config):
            if os.path.isdir(config):
                test_cfgs = test_cfgs + glob.glob(config + "/*.cfg")
            else:
                test_cfgs.append(config)
        else:
            print "ERROR: Directory/file '%s' doesn't exist." % config
            return -1

    print "Running the following configurations:"
    for test_cfg in test_cfgs:
        print " * %s" % test_cfg

    # by default run all tests
    cfg_filters = [".*"]

    # the TestConfig singleton is shared with all test suites as they run
    tc = sutc.TestConfig ()

    # now cycle over the found test configs, configure the TestConfig accordingly,
    # and run all specified test_suites
    for sfg_name in test_cfgs :

        # only use this config if it matches the config filters.
        cfg_active = False
        for cfg_filter in cfg_filters :
            if  re.search (cfg_filter, sfg_name) :
                cfg_active = True
                break

        if  not cfg_active :
            # this config file name did not match *any* of the given filters...
            print "skipping %s" % (os.path.basename (sfg_name))
            continue

        
        # initialize the correct test_util singleton (i.e. with the correct configfile)
        tc.read_config (sfg_name)

        # run all test suites from the config
        for test_suite in tc.test_suites :

            # configure the unit test framework
            config = nose.config.Config ()
            
            config.verbosity  = 1
            config.workingDir = test_base + '/' + test_suite
            config.stream     = sys.stderr
            
            # and run tests
            print "______________________________________________________________________"
            print "%s : %s" % (os.path.basename (sfg_name), test_suite)
            result = nose.core.run (config=config)
            print "______________________________________________________________________"

#-----------------------------------------------------------------------------
# entry point
if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("--debug",
                  action="store_true", dest="debug", default=False,
                  help="start the tests in debug mode")
    parser.add_option("-c", "--config", dest="config", metavar="CONFIG",
                  help="either a directory that contains test config files \
or a comma-separated list of individual config files")

    (options, args) = parser.parse_args()
    if options.config == None:
        print "ERROR: You need to provide the -c/--config option."
        sys.exit(-1)

    sys.exit(launch_tests(options=options))
