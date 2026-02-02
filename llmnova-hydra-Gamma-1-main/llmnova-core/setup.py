"""Setup do pacote NovaLLM."""
from setuptools import find_packages, setup

setup(
    name="llmnova",
    version="0.1.0",
    description="Sistema RAG com embeddings e reranking",
    author="LLM Nova Team",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "faiss-cpu>=1.7.4",
        "openai>=1.3.0",
        "sentence-transformers>=2.2.2",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0"
    ],
    python_requires=">=3.8"
)