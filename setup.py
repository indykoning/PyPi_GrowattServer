import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="growattServer",
    version="0.0.1",
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
