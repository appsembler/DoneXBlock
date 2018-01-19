"""Setup for done XBlock."""

import os
from setuptools import setup


def package_data(pkg, root):
    """Generic function to find package_data for `pkg` under `root`."""
    data = []
    for dirname, _, files in os.walk(os.path.join(pkg, root)):
        for fname in files:
            data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='done-xblock',
    version='0.2.0-unreleased',
    description='done XBlock',   # TODO: write a better description.
    packages=[
        'done',
    ],
    dependency_links=[
        # At the moment of writing PyPI hosts outdated version of xblock-utils, hence git
        # Replace dependency links with numbered versions when it's released on PyPI
        'git+https://github.com/edx/xblock-utils.git@v1.0.2#egg=xblock-utils-1.0.2',
        'git+https://github.com/edx/xblock-utils.git@v1.0.3#egg=xblock-utils-1.0.3',
    ],
    install_requires=[
        'XBlock>=0.4.10,<2.0.0',
        'xblock-utils>=1.0.2,<=1.0.3',
    ],
    entry_points={
        'xblock.v1': [
            'done = done:DoneXBlock',
        ]
    },
    package_data=package_data("done", "static"),
)