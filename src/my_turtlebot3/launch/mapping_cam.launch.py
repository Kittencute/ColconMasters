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

    keepout_info_server = Node(
        package='nav2_map_server',
        executable='costmap_filter_info_server',
        name='keepout_costmap_filter_info_server',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'type': 0,
            'filter_info_topic': '/keepout_costmap_filter_info',
            'mask_topic': '/keepout_filter_mask',
            'base': 0.0,
            'multiplier': 1.0,
        }]
    )


    keepout_lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_keepout',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': [
                'keepout_costmap_filter_info_server'
            ]
        }]
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
        keepout_info_server,
        keepout_lifecycle_manager,
        rviz,
    ])