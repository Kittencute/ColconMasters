import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'my_turtlebot3'

setup(
    name=package_name,
    version='0.0.0',

    packages=find_packages(exclude=['test']),

    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')
        ),
        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')
        ),
        (
            os.path.join('share', package_name, 'urdf'),
            glob('urdf/*')
        ),
        (
            os.path.join('share', package_name, 'rviz'),
            glob('rviz/*.rviz')
        ),
        (
            os.path.join(
                'share',
                package_name,
                'models',
                'turtlebot3_burger_cam'
            ),
            glob('models/turtlebot3_burger_cam/*')
        ),
    ],

    install_requires=['setuptools'],
    zip_safe=True,

    maintainer='rosdev',
    maintainer_email='utbildningkonto2019@gmail.com',

    description='TurtleBot3 simulation with simulated OAK-D camera',
    license='Apache-2.0',

    extras_require={
        'test': [
            'pytest',
        ],
    },

    entry_points={
        'console_scripts': [
        ],
    },
)