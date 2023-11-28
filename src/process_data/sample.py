"""
Sample random Reachy poses for training and testing.
Data number: 500 (number of seeds) * 2000 (poses per seed) = 1,000,000

1. Sample random values within the range of each joint (Reachy) -> 17 elements
2. Get xyz pos and rotation (Quaternion Representation) of 31 joints (Reachy) using forward kenematics
3. Quaternion -> 6D rotation
4. Create xyzs4smpl (SMPL) with 21 elements using Reachy joint xyz

=> Store xyzs, reps, xyzs4smpl into xyzs+reps.npy file,
   Store angle into angle.pkl file (Total number of files: 500 + 500).
"""

import numpy as np
import kinpy as kp
from tqdm import tqdm
import os
import os.path as osp
import pickle
import argparse
import sys

sys.path.append("./src")
from utils.transform import quat2rep
from utils.consts import *
from utils.types import RobotType, SampleArgs
from utils.RobotConfig import RobotConfig


def main(args: SampleArgs):
    # load the robot configurations which is matched with the robot type
    robot_config = RobotConfig(args.robot_type)

    # create a directory for saving the robot data
    os.makedirs(robot_config.RAW_DATA_PATH, exist_ok=True)

    # fmt: off
    num_seeds = args.num_seeds                  # how many random seed to be used for sampling
    motions_per_seed = args.motions_per_seed    # how many poses to be sampled for each random seed.
    # fmt: on

    # build a kinematic chain from robot's urdf
    chain = kp.build_chain_from_urdf(open(robot_config.URDF_PATH).read())

    for seed in range(num_seeds):
        # Ensuring that random values are uniform for the same seed,
        # but different for different seeds.
        np.random.seed(seed)

        total_xyzs = []
        total_reps = []
        total_angles = []
        total_xyzs4smpl = []

        for i in tqdm(range(motions_per_seed)):
            # fmt: off
            # angles: list of joints angle dicts (num_iter, joint_num) of {k: joint, v: angle}
            #         (roll, pitch, yaw of joints)
            # k: joint key, v[0]: MIN, v[1]: MAX,
            # v[1] - v[0]: Maximum range of each joint key.
            # np.random.rand() * (MAX - MIN) + MIN: Random value in range (MIN, MAX).
            angles = {
                k: ((np.random.rand() * (v[1] - v[0])) + v[0])
                for k, v in robot_config.joi_range.items()
            }
            # fmt: on

            # fk_result: forward kinematics result of chain (Robot)
            #            keys of each element: pos (xyz position), rot (rotation vector: quaternion representation)
            fk_result = chain.forward_kinematics(angles)

            xyzs = list()
            reps = list()

            for k, v in fk_result.items():
                # fmt: off
                # v.pos should change to 1 2 0 (when create curr_xyz)
                curr_xyz  = v.pos               # xyz position. shape: (3,)
                curr_quat = v.rot               # Quaternion Representation. shape: (4,)
                curr_rep  = quat2rep(curr_quat) # Transform Quaternion into 6D Rotation Representation
                # fmt: on

                xyzs.append(curr_xyz)
                reps.append(curr_rep)
                # xyzs & reps are lists of [# of robot links] elements,
                # each element is a 3D or 6D numpy array.

            # fmt: off
            xyzs = np.vstack(xyzs)                                   # xyzs.shape: (# of robot links, 3)
            reps = np.asarray(reps)                                  # reps.shape: (# of robot links, 6)
            xyzs4smpl = np.asarray(robot_config.convert_xyzs(xyzs))  # shape: (21, 3)
            # fmt: on

            # Append the iteration items into the total list
            total_angles.append(angles)
            total_xyzs.append(xyzs)
            total_reps.append(reps)
            total_xyzs4smpl.append(xyzs4smpl)

        # fmt: off
        total_xyzs = np.asarray(total_xyzs)            # shape: (num_iter, # of robot links, 3)
        total_reps = np.asarray(total_reps)            # shape: (num_iter, # of robot links, 6)
        total_xyzs4smpl = np.asarray(total_xyzs4smpl)  # shape: (num_iter, 21, 3)
        # fmt: on

        # save robot's xyz + rep data file
        # file name: DATA_PATH/xyzs+reps_0000.npz
        # data keys in a file: xyzs, reps, xyzs4smpl
        np.savez(
            osp.join(robot_config.RAW_DATA_PATH, robot_xyzs_reps_path(seed)),
            xyzs=total_xyzs,
            reps=total_reps,
            xyzs4smpl=total_xyzs4smpl,
        )

        # save robot's angle data file
        # file name: DATA_PATH/angles_0000.pkl
        pickle.dump(
            total_angles,
            open(osp.join(robot_config.RAW_DATA_PATH, robot_angles_path(seed)), "wb"),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="args for sampling reachy data")

    parser.add_argument(
        "--robot-type",
        "-r",
        type=RobotType,
        required=True,
        help=f"Select the robot type: {RobotType._member_names_}",
    )
    parser.add_argument(
        "--num-seeds",
        "-s",
        type=int,
        default=NUM_SEEDS,
        help="number of seeds for sampling",
    )
    parser.add_argument(
        "--motions-per-seed",
        "-m",
        type=int,
        default=MOTION_PER_SEED,
        help="number of motion samples for each seed",
    )

    args: SampleArgs = parser.parse_args()

    main(args)
