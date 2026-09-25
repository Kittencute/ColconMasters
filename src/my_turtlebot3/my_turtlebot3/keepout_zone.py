#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy
)

from geometry_msgs.msg import PointStamped, Point
from nav_msgs.msg import OccupancyGrid
from visualization_msgs.msg import Marker, MarkerArray
from std_srvs.srv import Trigger


class KeepoutZone(Node):

    def __init__(self):
        super().__init__('keepout_zone')

        self.map_msg = None

        # Size of each keepout square in meters
        self.zone_size = 1.0

        # Every RViz click creates another square
        self.zones = []

        map_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )

        self.map_sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            map_qos
        )

        self.point_sub = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.point_callback,
            10
        )

        self.mask_pub = self.create_publisher(
            OccupancyGrid,
            '/keepout_filter_mask',
            map_qos
        )

        self.marker_pub = self.create_publisher(
            MarkerArray,
            '/keepout_markers',
            10
        )

        self.clear_service = self.create_service(
            Trigger,
            '/keepout_zone/clear',
            self.clear_callback
        )

        self.get_logger().info(
            'Keepout zone node started'
        )

        self.get_logger().info(
            f'Each click creates a '
            f'{self.zone_size:.2f} m x '
            f'{self.zone_size:.2f} m keepout square'
        )


    def map_callback(self, msg):

        self.map_msg = msg

        self.publish_mask()


    def point_callback(self, msg):

        if self.map_msg is None:
            self.get_logger().warning(
                'No /map received yet'
            )
            return

        x = msg.point.x
        y = msg.point.y

        self.zones.append((x, y))

        self.get_logger().info(
            f'Keepout zone {len(self.zones)} created at '
            f'x={x:.2f}, y={y:.2f}'
        )

        self.publish_mask()
        self.publish_markers()


    def publish_mask(self):

        if self.map_msg is None:
            return

        mask = OccupancyGrid()

        mask.header.stamp = (
            self.get_clock().now().to_msg()
        )

        mask.header.frame_id = 'map'

        mask.info = self.map_msg.info

        width = mask.info.width
        height = mask.info.height
        resolution = mask.info.resolution

        origin_x = mask.info.origin.position.x
        origin_y = mask.info.origin.position.y

        data = [0] * (width * height)

        half_size = self.zone_size / 2.0

        for center_x, center_y in self.zones:

            min_x = center_x - half_size
            max_x = center_x + half_size

            min_y = center_y - half_size
            max_y = center_y + half_size

            min_col = max(
                0,
                int((min_x - origin_x) / resolution)
            )

            max_col = min(
                width - 1,
                int((max_x - origin_x) / resolution)
            )

            min_row = max(
                0,
                int((min_y - origin_y) / resolution)
            )

            max_row = min(
                height - 1,
                int((max_y - origin_y) / resolution)
            )

            for row in range(
                min_row,
                max_row + 1
            ):
                for col in range(
                    min_col,
                    max_col + 1
                ):

                    index = row * width + col

                    data[index] = 100

        mask.data = data

        self.mask_pub.publish(mask)


    def publish_markers(self):

        marker_array = MarkerArray()

        for i, (x, y) in enumerate(self.zones):

            marker = Marker()

            marker.header.frame_id = 'map'
            marker.header.stamp = (
                self.get_clock().now().to_msg()
            )

            marker.ns = 'keepout_zones'
            marker.id = i

            marker.type = Marker.CUBE
            marker.action = Marker.ADD

            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = 0.025

            marker.pose.orientation.w = 1.0

            marker.scale.x = self.zone_size
            marker.scale.y = self.zone_size
            marker.scale.z = 0.05

            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0
            marker.color.a = 0.5

            marker_array.markers.append(marker)

        self.marker_pub.publish(marker_array)


    def clear_callback(self, request, response):

        self.zones.clear()

        self.publish_mask()

        delete_marker = Marker()

        delete_marker.header.frame_id = 'map'
        delete_marker.header.stamp = (
            self.get_clock().now().to_msg()
        )

        delete_marker.action = Marker.DELETEALL

        marker_array = MarkerArray()
        marker_array.markers.append(delete_marker)

        self.marker_pub.publish(marker_array)

        response.success = True
        response.message = 'All keepout zones cleared'

        self.get_logger().info(
            'All keepout zones cleared'
        )

        return response


def main(args=None):

    rclpy.init(args=args)

    node = KeepoutZone()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()