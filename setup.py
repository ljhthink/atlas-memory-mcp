from setuptools import setup, find_packages

setup(
    name="atlas-memory-mcp",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.0.0",
        "tree-sitter>=0.21.0",
        "tree-sitter-python>=0.21.0",
    ],
    extras_require={
        "ai": [
            "chromadb>=0.4.0",
            "openai>=1.0.0",
            "tree-sitter>=0.21.0",
        ],
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=5.0.0",
        ],
    },
)
