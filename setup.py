from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ndog",
    version="1.0.0",
    author="JohnDaeSo",
    author_email="johndaeso19@gmail.com",
    description="A network utility similar to ncat but designed for public IPs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JohnDaeSo/ndog",
    packages=find_packages(),
    py_modules=["ndog", "ndog_simple"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    install_requires=[
        "colorama",
        "tqdm",
    ],
    entry_points={
        "console_scripts": [
            "ndog=ndog:main",
            "ndog-simple=ndog_simple:main",
        ],
    },
) 