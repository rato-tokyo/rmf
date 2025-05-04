from setuptools import setup, find_packages

setup(
    name="rmf-core",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "pyyaml>=6.0.0",
        "tenacity>=8.0.0",
        "aiohttp-sse>=2.1.0",
        "backoff>=2.2.0",
        "pydantic>=2.3.0"
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="Remote MCP Fetcher Core Library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rmf-core",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.8",
) 