from setuptools import setup, find_packages

setup(
    name="gitaccount",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "gitaccount=gitaccount.main:main",
        ],
    },
    install_requires=[],
    author="Keshav Sharma",
    author_email="keshavsharma8000@gmail.com",
    description="A command line utility to manage multiple GitHub accounts",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/keshav1sharma/git-account",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
