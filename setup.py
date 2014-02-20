import os
import sys
from setuptools import setup
from setuptools.command.install_lib import install_lib as _install_lib


with open('requirements.txt') as f:
    required = f.read().splitlines()


class install_lib(_install_lib):
    def run(self):
        from django.core.management.commands.compilemessages \
            import compile_messages
        os.chdir('bingo')
        compile_messages(sys.stderr)
        os.chdir("..")

setup(name='django-bingo',
      description='Bingo',
      long_description='Bingo game implemented in django',
      author='Alexander Schier',
      author_email='allo@laxu.de',
      version='1.3.2',
      packages=['bingo'],
      package_data={'bingo': ['templates/bingo/*.*',
                              'static/bingo/*.*',
                              'static/bingo/js/*.*',
                              'locale/*/LC_MESSAGES/*.*']},
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
