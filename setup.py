#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pythonico",
    version="1.0.0",
    author="André Machado",
    author_email="machaddr@falanet.org",
    description="A lightweight Python IDE for modern development",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/machaddr/pythonico",
    packages=find_packages(),
    py_modules=["pythonico"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Integrated Development Environments (IDE)",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "pythonico=pythonico:main",
        ],
    },
    data_files=[
        ("share/applications", ["debian/pythonico.desktop"]),
        ("share/icons/hicolor/256x256/apps", ["icons/main.png"]),
        ("share/doc/pythonico", ["README.md", "LICENSE"]),
    ],
    include_package_data=True,
    zip_safe=False,
)
