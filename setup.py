from setuptools import setup, find_packages

setup(
    name="mycommand",  # Your package name
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "mycommand=mycommand.main:main",  # Format: command_name=module:function
        ],
    },
    install_requires=[],  # Any dependencies
    author="Your Name",
    author_email="your.email@example.com",
    description="A brief description of your command",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mycommand",  # GitHub or project URL
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
