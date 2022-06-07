# Automatically created by: gerapy
from setuptools import setup, find_packages
setup(
    name='health_redis',
    version='1.0',
    packages=find_packages(),
    entry_points={'scrapy':['settings=health_redis.settings']},
)