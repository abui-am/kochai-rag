from setuptools import setup, find_packages

setup(
    name="fitness_rag",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "openai",
        "langchain",
        "langchain-openai",
        "langchain-community",
        "python-dotenv",
        "faiss-cpu",
        "pydantic",
    ],
) 
 