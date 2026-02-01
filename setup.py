
"""Setup metadata for the growattServer package."""

from pathlib import Path

import setuptools

long_description = Path("README.md").read_text(encoding="utf8")

setuptools.setup(
    name="growattServer",
    version="1.8.0",
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
