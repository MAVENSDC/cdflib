#
#To upload the latest version, change "version=0.X.X+1" and type:
#    python setup.py sdist upload
#
#
#

from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='cdflib',
      version='0.3.0',
      description='A python CDF reader toolkit',
      url='http://github.com/MAVENSDC/cdflib',
      author='MAVEN SDC',
      author_email='mavensdc@lasp.colorado.edu',
      license='MIT',
      keywords='CDF maven lasp PDS GSFC',
      packages=['cdflib'],
      install_requires=['numpy'],
      include_package_data=True,
      zip_safe=False)