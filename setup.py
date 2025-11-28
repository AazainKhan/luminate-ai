from setuptools import setup, find_packages

setup(
    name="edututor",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'chromadb>=0.3.0',
        'sentence-transformers',
        'beautifulsoup4',
        'python-dotenv',
        'pydantic',
        'requests',
        'sympy',
        'google-generativeai',
    ],
    python_requires='>=3.8',
)
