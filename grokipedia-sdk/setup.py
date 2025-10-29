"""Setup configuration for Grokipedia SDK"""

import re
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

# Read version from __init__.py
version = ""
init_file = this_directory / "grokipedia_sdk" / "__init__.py"
with open(init_file, "r", encoding="utf-8") as f:
    version_match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string in __init__.py")

setup(
    name="grokipedia-sdk",
    version=version,
    author="Apple Lamps",
    description="A Python SDK for accessing Grokipedia content",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AppleLamps/grokipedia-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.25.0",
        "beautifulsoup4>=4.12.0",
        "pydantic>=2.0.0",
        "lxml>=4.9.0",
        "rapidfuzz>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
)

