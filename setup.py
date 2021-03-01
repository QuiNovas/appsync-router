#!/usr/bin/env python3.8
import io
from setuptools import setup, find_packages


setup(
    name='appsync-router',
    version='2.0.3',
    description='Routers appsync requests to the correct route.',
    author='Mathew Moon',
    author_email='mmoon@quinovas.com',
    url='https://github.com/QuiNovas/appsync-tools',
    license='Apache 2.0',
    long_description=io.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    scripts=["src/scripts/appsync-app-builder"],
    install_requires=["typeguard", "appsync-tools"],
    python_requires=">=3.8",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.8',
    ],
)
