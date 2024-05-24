"""
    This file installs Cappy - making it available directly from the command line:
    'sudo Cappy'

    To uninstall Cappy run:
    'sudo pip3 uninstall Cappy'
"""

from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import shutil

class PostInstallCommand(install):
    """Post-installation for installation."""
    def run(self):
        install.run(self)
        main_dir = '/usr/local/share/Cappy'
        if not os.path.exists(main_dir):
            os.makedirs(main_dir)
        source = 'templates'
        destination = os.path.join(main_dir, source)
        if not os.path.exists(destination):
            os.makedirs(destination)
        for template in ["google", "Valentines", "mrhacker", "mcd"]:
            if not os.path.exists(os.path.join(destination, template)):
                shutil.copytree(f"{source}/{template}", f"{destination}/{template}")

setup(
    name='Cappy',
    version='1.0.0',
    author='FLOCK4H',
    url='github.com/FLOCK4H/Cappy',
    description='Cappy, the Evil Twin framework',
    license="MIT",
    packages=find_packages(),
    scripts=['Cappy'],
    cmdclass={
        'install': PostInstallCommand,
    }
)
