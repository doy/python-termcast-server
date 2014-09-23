from setuptools import setup, find_packages

setup(
    name="termcast_server",
    version="0.1.0",
    description="allow users to broadcast their terminals for others to watch",
    url="https://github.com/doy/python-termcast-server",
    author="Jesse Luehrs",
    author_email="doy@tozt.net",
    license="MIT",
    install_requires=[
        "vt100",
        "paramiko",
        "tornado",
    ],
    package_data={
        '': ["*.html"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Topic :: Terminals :: Terminal Emulators/X Terminals",
    ],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "termcast_server=termcast_server:main",
        ],
    },
)
