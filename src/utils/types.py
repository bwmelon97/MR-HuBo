import argparse
from enum import Enum


class RobotType(Enum):
    """
    Enum Type of Robots that we use
    """

    REACHY = "REACHY"
    COMAN = "COMAN"
    NAO = "NAO"


class EvaluateMode(Enum):
    """
    Enum Type of Evaluation
    """

    JOINT = "joint"
    LINK = "link"
    COS = "cos"


# Argument Types
class GenerateDataArgs(argparse.Namespace):
    """
    Arguments for Generating <Robot-Human> Paired Motion Data Python Codes
    """

    robot_type: RobotType
    num_seeds: int
    poses_per_seed: int
    device: str
    restart_idx: int


class SampleArgs(argparse.Namespace):
    """
    Arguments for Sampling Python Codes
    """

    num_seeds: int
    motions_per_seed: int
    robot_type: RobotType
    multi_cpu: bool
    num_cores: int


class Fit2SMPLArgs(argparse.Namespace):
    """
    Arguments for Converting Robot Joints for SMPL Parameters Python Codes
    """

    robot_type: RobotType
    video_result_dir: str
    video_extension: str
    visualize: bool
    verbosity: int
    fps: int
    restart_idx: int
    multi_cpu: bool
    num_cores: int
    collision_free: bool
    device: str


class AdjustNeckArgs(argparse.Namespace):
    """
    Arguments for Adjust neck joints of robot Python Codes
    """

    robot_type: RobotType


class FKWithAnglesArgs(argparse.Namespace):
    """
    Arguments for Forward Kinematics with Angles Python Codes
    """

    robot_type: RobotType
    multi_cpu: bool
    num_cores: int
    start_idx: int


class MakeRobotVideoArgs(argparse.Namespace):
    """
    Arguments for Making Robot Video Python Codes
    """

    motion_path: str
    result_path: str
    tmp_path: str
    fps: int
    resolution: int
    delete: bool
    smooth: bool
    robot_type: RobotType


class TrainArgs(argparse.Namespace):
    robot_type: RobotType
    collision_free: bool
    extreme_filter: bool
    arm_only: bool
    wandb: bool
    device: str


class TestArgs(argparse.Namespace):
    robot_type: RobotType
    human_pose_path: str
    robot_pose_result_path: str


class PybulletRenderArgs(argparse.Namespace):
    robot_type: RobotType
    smooth: bool
    view: str
    robot_pose_path: str
    output_path: str
    extention: str
    fps: int
    ground_truth: bool
    collision_free: bool
    extreme_filter: bool
    motion_idx: str
    arm_only: bool


class PybulletRenderOnePoseArgs(argparse.Namespace):
    robot_type: RobotType
    data_index: int
    pose_index: int


class PlotBaseArgs(argparse.Namespace):
    robot_type: RobotType
    random_pose: bool


class PlotWholeInOneArgs(argparse.Namespace):
    robot_type: RobotType
    data_idx: int
    pose_num: int
    out_extention: str
    fps: int
    collision_free: bool


class ConvertMat2PklArgs(argparse.Namespace):
    robot_type: RobotType


class PickBestModelArgs(argparse.Namespace):
    robot_type: RobotType
    collision_free: bool
    extreme_filter: bool
    evaluate_mode: EvaluateMode
    device: str
    arm_only: bool


class EvaluateOnTestMotionsArgs(argparse.Namespace):
    robot_type: RobotType
    collision_free: bool
    extreme_filter: bool
    evaluate_mode: EvaluateMode
    save_pred_motion: bool
    device: str
    arm_only: bool
