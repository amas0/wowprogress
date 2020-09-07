from setuptools import setup, find_packages

setup(name='wowprogress',
      description='Python library for pulling data from wowprogress.com',
      version='0.1',
      packages=find_packages(),
      install_requires=[
            'beautifulsoup4',
            'requests'
      ]
      )
