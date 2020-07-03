
from setuptools import setup

setup(name='servicemanager',
      version='1.8.3',
      description='A python tool to manage developing and testing with lots of microservices',
      url='https://github.com/hmrc/service-manager',
      author='hmrc-web-operations',
      license='Apache Licence 2.0',
      packages=['servicemanager', 'servicemanager.actions', 'servicemanager.server', 'servicemanager.service', 'servicemanager.thirdparty'],
      install_requires=['requests~=2.20','pymongo==3.0.1','bottle==0.12.4','pytest==4.6.11','argcomplete==0.8.1'],
      scripts=['bin/sm', 'bin/smserver'],
      zip_safe=False)
