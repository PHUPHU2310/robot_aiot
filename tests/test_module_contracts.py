import unittest

from hardware.contracts import validate_joints
from hardware.robot_arm import RobotArm
from vision.calibration import HomographyCalibration, LinearCalibration
from vision.contracts import DetectedObject
from vision.detect import normalize_detection


class VisionContractTests(unittest.TestCase):
    def test_detection_with_robot_coordinates(self):
        result = normalize_detection({
            "class_name": "chai_nuoc",
            "confidence": 0.91,
            "x_mm": 180,
            "y_mm": 80,
            "z_mm": 20,
        })
        self.assertEqual(result.to_dict()["x_mm"], 180.0)

    def test_detection_with_pixel_coordinates(self):
        result = normalize_detection({
            "class_name": "chai_nuoc",
            "confidence": 0.91,
            "u": 680,
            "v": 80,
        })
        self.assertEqual((result.x_mm, result.y_mm), (180.0, 80.0))

    def test_invalid_confidence_is_rejected(self):
        with self.assertRaises(ValueError):
            DetectedObject("chai_nuoc", 1.5, 180, 80, 20)

    def test_linear_calibration_contract(self):
        self.assertEqual(LinearCalibration().pixel_to_mm(680, 80), (180.0, 80.0))

    def test_homography_contract(self):
        calibration = HomographyCalibration([
            [1, 0, 10],
            [0, 1, 20],
            [0, 0, 1],
        ])
        self.assertEqual(calibration.pixel_to_mm(5, 7), (15.0, 27.0))


class HardwareContractTests(unittest.TestCase):
    def test_simulator_backend_contract(self):
        robot = RobotArm("simulator")
        self.assertTrue(robot.is_ready())
        self.assertTrue(robot.home_all().success)
        self.assertTrue(robot.move_joints([10, 20, 30, 40]).success)
        self.assertTrue(robot.gripper(open=False).success)
        self.assertEqual(robot.get_pose(), [10.0, 20.0, 30.0, 40.0])

    def test_wrong_joint_count_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_joints([10, 20, 30])


if __name__ == "__main__":
    unittest.main()
