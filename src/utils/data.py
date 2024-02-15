from torch.utils.data import Dataset
import numpy as np
import os.path as osp
import pickle
import torch
from pytorch3d.transforms import matrix_to_rotation_6d
from human_body_prior.tools.rotation_tools import aa2matrot
from human_body_prior.tools.model_loader import load_model
from human_body_prior.models.vposer_model import VPoser
from torch.distributions import multivariate_normal
import random
from tqdm import tqdm
import sys

sys.path.append("./src")
from utils.consts import *


def draw(probs):
    val = random.random()
    csum = np.cumsum(probs)
    i = sum(1 - np.array(csum >= val, dtype=int))
    if i == 2000:
        return -1
    else:
        return i


def split_train_test(
    input_path: str,
    reps_path: str,
    target_path: str,
    num_data: int,
    split_ratio: int = 10,
    sample_vposer: bool = True,
):
    """
    Args:
    ----------
    input_path (str): path to load SMPL parameters
    reps_path (str): path to load robot xyzs and reps
    target_path (str): path to load robot joint angles
    num_data (int): number of total data
    split_ratio (int): ratio of train/test split
    sample_vposer (bool): whether to sample from VPoser latent space
    """
    if sample_vposer:
        vp, ps = load_model(
            VPOSER_PATH,
            model_code=VPoser,
            remove_words_in_model_weights="vp_model.",
            disable_grad=True,
        )
        vp = vp.to(DEVICE)

    test_num = num_data // split_ratio

    all_robot_xyzs = {"train": [], "test": []}
    all_robot_reps = {"train": [], "test": []}
    all_robot_angles = {"train": [], "test": []}
    all_smpl_reps = {"train": [], "test": []}
    all_smpl_rots = {"train": [], "test": []}

    print("Loading data...")
    for idx in tqdm(range(num_data)):
        # print(idx, "/", num_data)
        smpl = np.load(osp.join(input_path, "params_{:04}.npz".format(idx)))
        smpl_pose_body = smpl["pose_body"]
        curr_num = len(smpl_pose_body)
        if sample_vposer:
            z = vp.encode(torch.from_numpy(smpl_pose_body).to(DEVICE))
            z_mean = z.mean.detach().cpu()  # 2000 32
            dim_z = z_mean.shape[1]
            dist = multivariate_normal.MultivariateNormal(
                loc=torch.zeros(dim_z), covariance_matrix=torch.eye(dim_z)
            )
            z_prob = torch.exp(dist.log_prob(z_mean))
            z_prob = z_prob / torch.sum(z_prob)

            n_sample = 500
            sample_idx = []
            while len(sample_idx) < n_sample:
                i = draw(z_prob)
                if i not in sample_idx and i > 0:
                    sample_idx.append(i)

        smpl_aa = smpl_pose_body.reshape(curr_num, -1, 3)
        num_smpl_joints = smpl_aa.shape[1]

        smpl_rot = aa2matrot(
            torch.from_numpy(smpl_aa.reshape(curr_num * num_smpl_joints, 3))
        )
        smpl_rep = matrix_to_rotation_6d(smpl_rot)

        smpl_rot = smpl_rot.reshape(curr_num, num_smpl_joints, 3, 3)
        smpl_rep = smpl_rep.reshape(curr_num, num_smpl_joints, 6)

        smpl_rot = smpl_rot.numpy().reshape(curr_num, -1)
        smpl_rep = smpl_rep.numpy().reshape(curr_num, -1)

        robot_angle = pickle.load(
            open(osp.join(target_path, "angles_{:04}.pkl".format(idx)), "rb")
        )
        angle_chunk = []
        for ra in robot_angle:
            values = []
            for k in sorted(list(ra.keys())):
                values.append(ra[k])
            angle_chunk.append(np.array(values))
        angle_chunk = np.asarray(angle_chunk)

        robot_xyzrep = np.load(osp.join(reps_path, "xyzs+reps_{:04}.npz".format(idx)))
        robot_xyzs = robot_xyzrep["xyzs"]
        robot_reps = robot_xyzrep["reps"]

        robot_xyzs = robot_xyzs.reshape(curr_num, -1)
        robot_reps = robot_reps.reshape(curr_num, -1)

        if idx < test_num:
            target = "test"
        else:
            target = "train"

        if sample_vposer:
            all_robot_xyzs[target].append(robot_xyzs[sample_idx])
            all_robot_reps[target].append(robot_reps[sample_idx])
            all_robot_angles[target].append(angle_chunk[sample_idx])
            all_smpl_reps[target].append(smpl_rep[sample_idx])
            all_smpl_rots[target].append(smpl_rot[sample_idx])
        else:
            all_robot_xyzs[target].append(robot_xyzs)
            all_robot_reps[target].append(robot_reps)
            all_robot_angles[target].append(angle_chunk)
            all_smpl_reps[target].append(smpl_rep)
            all_smpl_rots[target].append(smpl_rot)

    for target in ["test", "train"]:
        all_robot_xyzs[target] = np.concatenate(all_robot_xyzs[target], axis=0)
        all_robot_reps[target] = np.concatenate(all_robot_reps[target], axis=0)
        all_robot_angles[target] = np.concatenate(all_robot_angles[target], axis=0)
        all_smpl_reps[target] = np.concatenate(all_smpl_reps[target], axis=0)
        all_smpl_rots[target] = np.concatenate(all_smpl_rots[target], axis=0)

    return (
        all_robot_xyzs,
        all_robot_reps,
        all_robot_angles,
        all_smpl_reps,
        all_smpl_rots,
    )


class H2RMotionData(Dataset):
    def __init__(self, robot_xyz, robot_rep, robot_angle, smpl_rep, smpl_rot):
        self.robot_xyz = robot_xyz
        self.robot_rep = robot_rep
        self.robot_angle = robot_angle
        self.smpl_rep = smpl_rep
        self.smpl_rot = smpl_rot

    def __len__(self):
        return len(self.smpl_rep)

    def __getitem__(self, idx):
        sample = dict()

        sample["robot_xyz"] = self.robot_xyz[idx]
        sample["robot_rep"] = self.robot_rep[idx]
        sample["robot_angle"] = self.robot_angle[idx]
        sample["smpl_rep"] = self.smpl_rep[idx]
        sample["smpl_rot"] = self.smpl_rot[idx]

        return sample
