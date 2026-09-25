from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # Launch arguments

    model = LaunchConfiguration('model')
    world = LaunchConfiguration('world')

    declare_model = DeclareLaunchArgument(
        'model',
        default_value='burger',
        description='TurtleBot3 model: burger_cam'
    )

    declare_world = DeclareLaunchArgument(
        'world',
        default_value='turtlebot3_world',
        description='World: empty_world, turtlebot3_world, or turtlebot3_house'
    )

    # Set TurtleBot3 model

    set_turtlebot3_model = SetEnvironmentVariable(
        name='TURTLEBOT3_MODEL',
        value=model
    )

    # Gazebo worlds

    # Empty world
    empty_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_gazebo'),
                'launch',
                'empty_world.launch.py'
            ])
        ),
        condition=IfCondition(
            PythonExpression([
                "'", world, "' == 'empty_world'"
            ])
        )
    )

    # TurtleBot3 world
    turtlebot3_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_gazebo'),
                'launch',
                'turtlebot3_world.launch.py'
            ])
        ),
        condition=IfCondition(
            PythonExpression([
                "'", world, "' == 'turtlebot3_world'"
            ])
        )
    )

    # TurtleBot3 house
    turtlebot3_house = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_gazebo'),
                'launch',
                'turtlebot3_house.launch.py'
            ])
        ),
        condition=IfCondition(
            PythonExpression([
                "'", world, "' == 'turtlebot3_house'"
            ])
        )
    )

    # Cartographer

    cartographer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_cartographer'),
                'launch',
                'cartographer.launch.py'
            ])
        ),
        launch_arguments={
            'use_sim_time': 'True'
        }.items()
    )

    # Map file

    map_file = PathJoinSubstitution([
        EnvironmentVariable('HOME'),
        'map.yaml'
    ])

    # Navigation2

    navigation2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_navigation2'),
                'launch',
                'navigation2.launch.py'
            ])
        ),
        launch_arguments={
            'use_sim_time': 'True',
        }.items()
    )

    # Launch everything

    return LaunchDescription([
        # Arguments
        declare_model,
        declare_world,

        # Environment
        set_turtlebot3_model,

        # Gazebo
        empty_world,
        turtlebot3_world,
        turtlebot3_house,

        # Mapping
        #cartographer,

        # Navigation
        #navigation2,
    ])