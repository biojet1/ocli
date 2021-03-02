from setuptools import setup, find_packages

setup(
    name="ocli",  # Replace with your own username
    version="0.0.3",
    author="biojet1",
    author_email="biojet1@gmail.com",
    description="Command line app object",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/biojet1/ocli",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
