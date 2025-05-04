from setuptools import setup, find_packages

setup(
    name="rmf-tests",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rmf-core>=0.1.0",
        "rmf-server>=0.1.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.18.0",
        "pytest-aiohttp>=1.0.0",
        "aioresponses>=0.7.0",
        "coverage>=6.0.0",
        "pytest-cov>=4.1.0",
        "pytest-xdist>=3.3.1",  # 並列テスト実行用
        "pytest-timeout>=2.1.0",  # タイムアウト管理用
        "pytest-mock>=3.10.0",  # モック作成用
        "requests>=2.31.0",  # E2Eテスト用
        "docker>=6.1.0",  # コンテナベースのテスト用
    ],
    extras_require={
        "integration": [
            "docker-compose>=1.29.2",
            "testcontainers>=3.7.1",
        ],
        "e2e": [
            "selenium>=4.11.0",
            "playwright>=1.39.0",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Remote MCP Fetcher Test Suite",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rmf-tests",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.8",
) 