# -*- coding: utf-8 -*-
import os
from setuptools import setup
from pip.req import parse_requirements
from pip.download import PipSession


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
install_reqs = parse_requirements(os.path.join(BASE_PATH, 'requirements.txt'),
                                  session=PipSession())

setup(
    name="simplegexf",
    version="0.1.2",
    description="A simple .gexf parser/writer for python",
    license="MIT",
    url="https://github.com/demux/simplegexf",
    install_requires=[str(ir.req) for ir in install_reqs],
    long_description=open("README.md").read(),
    keywords="simplegexf gephi gexf",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 3 - Alpha",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
    ]
)
