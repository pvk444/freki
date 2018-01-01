#!/usr/bin/env python
from distutils.core import setup

setup(
    name='freki',
    version='0.3.0',
    description='PDF-Extraction helper for RiPLEs pipeline.',
    author='Michael Goodman, Ryan Georgi',
    author_email='goodmami@uw.edu, rgeorgi@uw.edu',
    url='https://github.com/xigt/freki',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Utilities'
    ],
    keywords='nlp pdf ie text',
    packages=['freki', 'freki.readers', 'freki.analyzers'],
    install_requires=[
        'numpy',
        'matplotlib',
        'chardet'
    ],
    entry_points={
        'console_scripts': [
            'freki=freki.main:main'
        ]
    },

)
