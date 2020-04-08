#!/bin/sh

rm dist/*
latest_tag=$(git describe --tags)
echo "The tag to be used is: ${latest_tag}."
echo "Is this correct? (y/N)"
read CONTINUE

if [ $CONTINUE != y ]]
then
    echo "Stopping build."
    return 1
fi
python3 setup.py sdist bdist_wheel $latest_tag
python3 -m twine upload dist/*
