from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    world = LaunchConfiguration('world')

    declare_world = DeclareLaunchArgument(
        'world',
        default_value='turtlebot3_house',
        description='World: turtlebot3_world, or turtlebot3_house'
    )

    set_turtlebot3_model = SetEnvironmentVariable(
        name='TURTLEBOT3_MODEL',
        value='burger_cam'
    )

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

    cartographer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_cartographer'),
                'launch',
                'cartographer.launch.py'
            ])
        ),
        launch_arguments={
            'use_sim_time': 'True',
            'use_rviz': 'False',
        }.items()
    )

    navigation2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('nav2_bringup'),
                'launch',
                'navigation_launch.py'
            ])
        ),
        launch_arguments={
            'use_sim_time': 'True',
            'autostart': 'True',
            'params_file': PathJoinSubstitution([
                FindPackageShare('turtlebot3_navigation2'),
                'param',
                'burger.yaml'
            ]),
        }.items()
    )

    rviz_config = PathJoinSubstitution([
        FindPackageShare('my_turtlebot3'),
        'rviz',
        'burger_cam.rviz'
    ])

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[
            {'use_sim_time': True}
        ]
    )

    return LaunchDescription([
        declare_world,
        set_turtlebot3_model,
        turtlebot3_world,
        turtlebot3_house,
        cartographer,
        navigation2,
        rviz,
    ])