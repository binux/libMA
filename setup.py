from setuptools import setup

setup(name='libMA',
      version='1.1',
      description='ma',
      author='Roy Binux',
      author_email='roy@binux.com',
      url='https://github.com/binux/libMA',
      install_requires=[
          'requests>=1.2.3',
          'gevent>=1.0',
          'gevent-websocket>=0.3.6',
          'lxml>=3.2.3',
          'WebOb>=1.2.3',
          'pycrypto>=2.6'],
     )
