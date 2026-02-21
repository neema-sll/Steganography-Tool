"""
Setup configuration for Steganography Tool
"""
from setuptools import setup, find_packages
import os

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="steganography-tool",
    version="1.0.0",
    author="Neema Lama",
    author_email="neema.lama@example.com",
    description="Secure Data Hider - A comprehensive steganography tool with GUI and CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/neema-sll/Steganography-Tool",
    project_urls={
        "Bug Tracker": "https://github.com/neema-sll/Steganography-Tool/issues",
        "Documentation": "https://github.com/neema-sll/Steganography-Tool/wiki",
        "Source Code": "https://github.com/neema-sll/Steganography-Tool",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Graphics",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "flake8>=4.0.0",
            "black>=22.0.0",
            "mypy>=0.950",
        ],
        "gui": [
            "Pillow>=9.0.0",  # Already in requirements
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "pytest-xdist>=2.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "stegano-gui=src.gui:main",      # Run GUI: stegano-gui
            "stegano-cli=src.cli:main",      # Run CLI: stegano-cli
            "stegano=run:main",               # Run both: stegano [--cli]
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.yml"],
    },
    zip_safe=False,
)