from setuptools import setup, find_packages, Extension
from pkg_resources import parse_version
import re


VARAPP_VERSION = '1.0.1'


with open('./README.rst') as readme:
    README = readme.read()

with open('./requirements.txt') as reqs:
    REQUIREMENTS = [L.split('#')[0].strip() for L in reqs if not L[0]=='#']
    numpy_req = [r for r in REQUIREMENTS if 'numpy' in r][0]
    numpy_req_version = parse_version(re.split(r'[<>=]', numpy_req)[-1])


## Install numpy if it is not found, before building Extensions requiring it
try:
    import numpy
    if parse_version(numpy.__version__) < numpy_req_version:
        print("numpy {} was found but is too old. Upgrading.".format(numpy.__version__))
        raise ImportError
    print("Numpy was found. Build extensions.")
except ImportError:
    print("Building Cython extensions requires numpy. Installing numpy.")
    import pip
    pip_args = ['install', numpy_req]
    pip.main(pip_args)
    import numpy


## Use Cython to build .pyx sources if it is found, build from precompiled .c otherwise
try:
    import Cython.Distutils
    print("Cython was found. Compiling from .pyx source.")
    USE_CYTHON = True
except ImportError:
    print("Cython was not found. Building extension from .c source files.")
    USE_CYTHON = False

cmdclass = {}

if USE_CYTHON:
    import os
    cmdclass.update({'build_ext': Cython.Distutils.build_ext})
    if os.path.exists("varapp/filters/apply_bitwise.c"):
        os.remove("varapp/filters/apply_bitwise.c")
    ext_modules = [
        Extension("varapp.filters.apply_bitwise", sources=[ "varapp/filters/apply_bitwise.pyx" ]),
    ]
else:
    ext_modules = [
        Extension("varapp.filters.apply_bitwise", sources=[ "varapp/filters/apply_bitwise.c" ]),
    ]


setup(
    version = VARAPP_VERSION,
    name = 'varapp-backend-py', # name of the archive produced when executing "setup.py sdist"
    cmdclass = cmdclass,
    packages = find_packages(exclude=['tests*', 'benchmark']),
    ext_modules = ext_modules,
    include_dirs = [numpy.get_include()],
    include_package_data = True,  # "read MANIFEST.ini"
    license = 'GPL-3',
    description = 'Genomic variants explorer',
    long_description = README,
    url = 'https://github.com/varapp/varapp-backend-py',
    download_url = 'https://github.com/varapp/varapp-backend-py/tarball/'+VARAPP_VERSION,
    keywords = ['variants', 'filter', 'genotype', 'gemini'],
    author = 'Vital-IT/SIB/CHUV',
    author_email = 'julien.delafontaine@sib.swiss',
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires = REQUIREMENTS,
    test_suite = "tests",
)


