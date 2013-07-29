import os
from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name='django-bingo',
      description='Bingo',
      long_description='Bingo game implemented in django',
      author='Alexander Schier',
      author_email='allo@laxu.de',
      version='0.0.1',
      packages=['bingo'],
      include_package_data=True,
      install_requires=required,
      classifiers=[
          'Framework :: Django',
          'Topic :: Games/Entertainment :: Board Games',
          'License :: OSI Approved :: GNU Affero General Public License v3',
          'Operating System :: OS Independent',
          'Programming Language :: Python'
      ]
      )
