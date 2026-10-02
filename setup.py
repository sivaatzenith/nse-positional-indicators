"""
setup.py
~~~~~~~~
Installation script for the nse_positional_indicators library.

Install (editable / development mode)
--------------------------------------
    pip install -e .

Install from source tarball
----------------------------
    pip install .
"""

from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nse_positional_indicators",
    version="1.0.0",
    author="NSE Positional Indicators",
    description=(
        "Fetch NSE stock data and compute positional trading indicators "
        "(SMA50/200, RSI, MACD, ADX, OBV) with a BUY/SELL/HOLD advisor."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "yfinance>=0.2.0",
        "pandas>=1.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    keywords="nse stock indicators sma rsi macd adx obv positional trading",
)
