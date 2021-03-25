#!/usr/bin/env python3.8
import io
from setuptools import setup


setup(
    name='appsync-router',
    version='0.1.1',
    description='A framework for building, testing, and deploying  an Appsync backend using AWS Lambda',
    author='Mathew Moon',
    author_email='mmoon@quinovas.com',
    url='https://github.com/QuiNovas/appsync-router',
    license='Apache 2.0',
    long_description=io.open('README.rst', encoding='utf-8').read(),
    long_description_content_type='text/x-rst',
    packages=['appsync_router'],
    package_dir={'appsync_router': 'src/appsync_router'},
    install_requires=["typeguard", "appsync-tools"],
    scripts=["src/appsync_router/scripts/appsync-router"],
    python_requires=">=3.8",
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.8',
    ],
)
