import setuptools
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()
tag = sys.argv[3]

setuptools.setup(
    name="growattServer",
    version=tag,
    author="IndyKoning",
    description="A package to talk to growatt server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/indykoning/PyPi_GrowattServer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
