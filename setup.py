import os
from setuptools import setup, find_packages, Extension
import numpy

ext_modules = []
cmdclass = {}

try:
    import Cython.Distutils
    print("Cython was found. Compiling from .pyx source.")
    ext = '.pyx'
    cmdclass.update({'build_ext': Cython.Distutils.build_ext})
except ImportError:
    Cython = None
    print("Cython was not found. Building extension from .c source files.")
    ext = '.c'

ext_modules += [
    Extension("varapp.filters.apply_bitwise", sources=[ "varapp/filters/apply_bitwise"+ext ]),
]

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(
    version = '1.0',
    name = 'varapp-backend-py', # name of the archive produced when executing "setup.py sdist"
    cmdclass = cmdclass,
    packages = find_packages(exclude=['tests*', 'benchmark']),
    ext_modules = ext_modules,
    include_dirs = [numpy.get_include()],
    include_package_data = True,  # "read MANIFEST.ini"
    license = 'GPL-2',
    description = 'Genomic variants explorer',
    long_description = README,
    url = 'https://gitlab.isb-sib.ch/groups/varapp',
    author = 'SIB/CHUV',
    author_email = 'julien.delafontaine@isb-sib.ch',
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL-2 License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires = [
        'django>=1.8.1',
        'django-cors-headers>=1.0.0',
        'django-jsonview==0.5.0',
        'django_redis>=2.10.0',
        'pyjwt>=1.4.0',
        #'numpy>=1.10.0',  # install beforehand
        #'mod_wsgi-httpd>=2.4.12.6',  # install beforehand because it hangs
        #'mysqlclient>=1.3.7',  # recommended for Django. Wraps MySQLdb. Install beforehand befcause it hangs.
    ],
    test_suite = "tests",
)


