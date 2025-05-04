from setuptools import setup, find_packages

setup(
    name="rmf",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "python-dotenv>=0.19.0",
        "pyyaml>=6.0.0",
        "tenacity>=8.0.0",
        "aiohttp-sse>=2.1.0"
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-aiohttp>=1.0.0",
            "aioresponses>=0.7.0",
            "coverage>=6.0.0"
        ]
    }
) 