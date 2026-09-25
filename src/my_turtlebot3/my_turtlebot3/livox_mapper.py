#!/usr/bin/env python3

import os
import struct
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from rclpy.duration import Duration

from sensor_msgs.msg import PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from std_srvs.srv import Trigger

from tf2_ros import Buffer, TransformListener


class LivoxMapper(Node):

    def __init__(self):
        super().__init__('livox_mapper')

        self.map_frame = 'map'

        # Size of each stored 3D cube in meters.
        # 0.10 = 10 cm x 10 cm x 10 cm
        self.voxel_size = 0.10

        # Each entry is (ix, iy, iz).
        # A set prevents duplicate voxels.
        self.voxels = set()

        qos = QoSProfile(
            depth=5,
            reliability=ReliabilityPolicy.BEST_EFFORT
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(
            self.tf_buffer,
            self
        )

        self.subscription = self.create_subscription(
            PointCloud2,
            '/livox/points',
            self.cloud_callback,
            qos
        )

        self.publisher = self.create_publisher(
            PointCloud2,
            '/livox/map_points',
            1
        )

        self.save_service = self.create_service(
            Trigger,
            '/livox_mapper/save_map',
            self.save_map_callback
        )

        self.clear_service = self.create_service(
            Trigger,
            '/livox_mapper/clear_map',
            self.clear_map_callback
        )

        self.get_logger().info(
            'Livox voxel mapper started'
        )

        self.get_logger().info(
            f'Voxel size: {self.voxel_size:.2f} m'
        )

        self.get_logger().info(
            'Input: /livox/points'
        )

        self.get_logger().info(
            'Output: /livox/map_points'
        )


    def cloud_callback(self, msg):

        try:
            transform = self.tf_buffer.lookup_transform(
                self.map_frame,
                msg.header.frame_id,
                rclpy.time.Time(),
                timeout=Duration(seconds=0.2)
            )

        except Exception as e:
            self.get_logger().warning(
                f'Cannot transform '
                f'{msg.header.frame_id} -> {self.map_frame}: {e}',
                throttle_duration_sec=2.0
            )
            return

        tx = transform.transform.translation.x
        ty = transform.transform.translation.y
        tz = transform.transform.translation.z

        qx = transform.transform.rotation.x
        qy = transform.transform.rotation.y
        qz = transform.transform.rotation.z
        qw = transform.transform.rotation.w

        rotation = self.quaternion_matrix(
            qx,
            qy,
            qz,
            qw
        )

        old_count = len(self.voxels)

        for p in point_cloud2.read_points(
            msg,
            field_names=('x', 'y', 'z'),
            skip_nans=True
        ):

            x = float(p[0])
            y = float(p[1])
            z = float(p[2])

            if (
                not np.isfinite(x)
                or not np.isfinite(y)
                or not np.isfinite(z)
            ):
                continue

            local_point = np.array(
                [x, y, z],
                dtype=np.float64
            )

            global_point = rotation @ local_point

            gx = global_point[0] + tx
            gy = global_point[1] + ty
            gz = global_point[2] + tz

            ix = int(
                np.floor(gx / self.voxel_size)
            )

            iy = int(
                np.floor(gy / self.voxel_size)
            )

            iz = int(
                np.floor(gz / self.voxel_size)
            )

            self.voxels.add(
                (ix, iy, iz)
            )

        new_count = len(self.voxels)

        if new_count != old_count:
            self.get_logger().info(
                f'Occupied voxels: {new_count}',
                throttle_duration_sec=2.0
            )

        self.publish_map()


    def quaternion_matrix(self, x, y, z, w):

        return np.array([
            [
                1.0 - 2.0 * (y * y + z * z),
                2.0 * (x * y - z * w),
                2.0 * (x * z + y * w)
            ],
            [
                2.0 * (x * y + z * w),
                1.0 - 2.0 * (x * x + z * z),
                2.0 * (y * z - x * w)
            ],
            [
                2.0 * (x * z - y * w),
                2.0 * (y * z + x * w),
                1.0 - 2.0 * (x * x + y * y)
            ]
        ])


    def voxel_to_point(self, voxel):

        ix, iy, iz = voxel

        x = (ix + 0.5) * self.voxel_size
        y = (iy + 0.5) * self.voxel_size
        z = (iz + 0.5) * self.voxel_size

        return (
            float(x),
            float(y),
            float(z)
        )


    def publish_map(self):

        if not self.voxels:
            return

        points = [
            self.voxel_to_point(voxel)
            for voxel in self.voxels
        ]

        msg = PointCloud2()

        msg.header.stamp = (
            self.get_clock().now().to_msg()
        )

        msg.header.frame_id = self.map_frame

        msg.height = 1
        msg.width = len(points)

        msg.fields = [
            PointField(
                name='x',
                offset=0,
                datatype=PointField.FLOAT32,
                count=1
            ),
            PointField(
                name='y',
                offset=4,
                datatype=PointField.FLOAT32,
                count=1
            ),
            PointField(
                name='z',
                offset=8,
                datatype=PointField.FLOAT32,
                count=1
            )
        ]

        msg.is_bigendian = False
        msg.point_step = 12
        msg.row_step = (
            msg.point_step * msg.width
        )

        msg.is_dense = True

        data = bytearray()

        for x, y, z in points:
            data.extend(
                struct.pack(
                    'fff',
                    x,
                    y,
                    z
                )
            )

        msg.data = bytes(data)

        self.publisher.publish(msg)


    def save_map_callback(
        self,
        request,
        response
    ):

        if not self.voxels:

            response.success = False
            response.message = (
                'No voxels available to save'
            )

            return response

        directory = os.path.expanduser(
            '~/turtlebot3_ws_mx/maps'
        )

        os.makedirs(
            directory,
            exist_ok=True
        )

        filename = os.path.join(
            directory,
            'livox_voxel_map.pcd'
        )

        points = [
            self.voxel_to_point(voxel)
            for voxel in self.voxels
        ]

        with open(
            filename,
            'w'
        ) as f:

            f.write(
                '# .PCD v0.7\n'
            )

            f.write(
                'VERSION 0.7\n'
            )

            f.write(
                'FIELDS x y z\n'
            )

            f.write(
                'SIZE 4 4 4\n'
            )

            f.write(
                'TYPE F F F\n'
            )

            f.write(
                'COUNT 1 1 1\n'
            )

            f.write(
                f'WIDTH {len(points)}\n'
            )

            f.write(
                'HEIGHT 1\n'
            )

            f.write(
                'VIEWPOINT 0 0 0 1 0 0 0\n'
            )

            f.write(
                f'POINTS {len(points)}\n'
            )

            f.write(
                'DATA ascii\n'
            )

            for x, y, z in points:

                f.write(
                    f'{x} {y} {z}\n'
                )

        response.success = True

        response.message = (
            f'Saved {len(points)} voxels '
            f'to {filename}'
        )

        self.get_logger().info(
            response.message
        )

        return response


    def clear_map_callback(
        self,
        request,
        response
    ):

        count = len(self.voxels)

        self.voxels.clear()

        response.success = True

        response.message = (
            f'Cleared {count} voxels'
        )

        self.get_logger().info(
            response.message
        )

        return response


def main(args=None):

    rclpy.init(args=args)

    node = LivoxMapper()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()