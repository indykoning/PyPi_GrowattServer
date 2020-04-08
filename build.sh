#!/bin/sh

rm dist/*
export LATEST_TAG=$(git describe --tags)
echo "The tag to be used is: ${LATEST_TAG}."
echo "Is this correct? (y/N)"
read CONTINUE

if [ $CONTINUE != y ]]
then
    echo "Stopping build."
    return 1
fi

python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*
