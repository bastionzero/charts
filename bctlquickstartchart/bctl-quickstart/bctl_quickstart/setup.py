from setuptools import setup, find_packages
import os

with open('requirements.txt', 'rb') as f:
    install_requires = f.read().decode('utf-8').split('\n')

setup(
    name='bctl-quickstart',
    version=1.0,
    description="Bzero Kube Quickstart",
    author='Sid Premkumar',
    author_email='sid@bastionzero.com',
    install_requires=install_requires,
    packages=find_packages('scripts'),
    entry_points={
        'console_scripts': [
            'bctl-quickstart=bctl_quickstart.main:cli',
        ],
    },
)