#!/usr/bin/env python
from distutils.core import setup

setup(name='freki',
      version='1.0',
      description='PDF-Extraction helper for RiPLEs pipeline.',
      author='Michael Goodman, Ryan Georgi',
      author_email='goodmami@uw.edu, rgeorgi@uw.edu',
      url='https://github.com/xigt/freki',
      packages=['freki', 'freki.readers'],
     )