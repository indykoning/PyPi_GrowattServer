import setuptools
import os

tag = os.environ['LATEST_TAG']
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="growattServer",
    version=tag,
    author="IndyKoning",
    author_email="indykoningnl@gmail.com",
    description="A package to talk to growatt server",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/indykoning/PyPi_GrowattServer",
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
