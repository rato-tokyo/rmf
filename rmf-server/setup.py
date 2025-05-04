from setuptools import setup, find_packages

setup(
    name="rmf-server",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rmf-core>=0.1.0",
        "fastapi>=0.103.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.3.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-aiohttp>=1.0.0",
            "aioresponses>=0.7.0",
            "coverage>=6.0.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "rmf-server=rmf_server.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Remote MCP Fetcher Server",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rmf-server",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.8",
) 