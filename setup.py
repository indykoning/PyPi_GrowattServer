import setuptools
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="growattServerSR",
    version="1.7.0",
    author="Simon Rankine",
    author_email="simon@srankine.uk",
    description="A package to talk to growatt server - forked from the original by @indykoning",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/simonrankine/PyPi_GrowattServer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests",
    ],
)
