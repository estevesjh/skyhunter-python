from setuptools import setup, find_packages

setup(
    name="skyhunter",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'astropy',
        'pytz',
        'pyserial',
        'pylint'
    ],
    author="Johnny H. Esteves",
    author_email="jesteves@g.harvard.edu",
    description="A package to control the iOptron SkyHunter mount.",
    url="https://github.com/estevesjh/skyhunter-python",  # Update this to your repository URL
)
