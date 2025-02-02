import numpy as np
from pyrr import matrix33, matrix44, euler
import os

def get_rpy_from_rotation(T):
    rot_matrix = T[:3, :3]
    yaw = np.arctan2(rot_matrix[1, 0],rot_matrix[0, 0])
    pitch = np.arctan2(-rot_matrix[2, 0], np.sqrt(rot_matrix[2, 1]**2 + rot_matrix[2, 2]**2))
    roll = np.arctan2(rot_matrix[2, 1], rot_matrix[2, 2])
    return np.array([roll, pitch, yaw])

def get_extrinsic_rotation(rpy):
    x_rot = matrix33.create_from_x_rotation(rpy[0])
    y_rot = matrix33.create_from_y_rotation(rpy[1])
    z_rot = matrix33.create_from_z_rotation(rpy[2])
    result = np.eye(4)
    result[:3, :3] = np.matmul(z_rot, np.matmul(y_rot, x_rot))
    return result

def get_extrinsic_tf(rpy, xyz):
    tf = np.eye(4)
    tf[:3, :3] = get_extrinsic_rotation(rpy)[:3, :3]
    tf[:3, 3] = xyz
    return tf

def tf_coordinate(tf, xyz):
    return np.matmul(tf, np.append(xyz, 1.))[:3]

def inv_tf(tf):
    """Get the inverse of a homogeneous transform"""
    inv_tf = np.eye(4)
    inv_tf[0:3, 0:3] = np.transpose(tf[0:3, 0:3])
    inv_tf[0:3, 3] = -1.0 * np.matmul(np.transpose(tf[0:3, 0:3]), tf[0:3, 3])
    return inv_tf

def get_modified_dh_frame(dh_params):
    # alpha, a, theta, d in wikipedia
    alpha, a, theta, d = dh_params
    modified_dh_frame = np.eye(4)
    modified_dh_frame[0, 0] = np.cos(theta)
    modified_dh_frame[0, 1] = -np.sin(theta)
    modified_dh_frame[0, 3] = a

    modified_dh_frame[1, 0] = np.sin(theta)*np.cos(alpha)
    modified_dh_frame[1, 1] = np.cos(theta)*np.cos(alpha)
    modified_dh_frame[1, 2] = -np.sin(alpha)
    modified_dh_frame[1, 3] = -d*np.sin(alpha)

    modified_dh_frame[2, 0] = np.sin(theta)*np.sin(alpha)
    modified_dh_frame[2, 1] = np.cos(theta)*np.sin(alpha)
    modified_dh_frame[2, 2] = np.cos(alpha)
    modified_dh_frame[2, 3] = d*np.cos(alpha)
    return modified_dh_frame

def find_common_vertical_line(point_list, zaxis_list, epsilon=1e-5, log=False):
    # NOTE: under global coordinate
    num = len(point_list)
    xaxis_list = [np.zeros(3)] * num
    origin_list = [np.zeros(3)] * num
    for i in range(num-1):
        zaxis0, zaxis1 = zaxis_list[i], zaxis_list[i+1]
        point0, point1 = point_list[i], point_list[i+1]
        xaxis0 = np.cross(zaxis0, zaxis1)
        if np.linalg.norm(xaxis0) < epsilon:
            # if i==0:
            #     xaxis_list[i] = np.array([1, 0, 0.])
            # else:
            #     xaxis_list[i] = xaxis_list[i-1] #NOTE: parallel case
            # xaxis_list[i+1] = xaxis_list[i]

            a, b, c = np.inner(zaxis0, zaxis1), np.inner(zaxis0, zaxis0), np.inner(zaxis1, zaxis1)
            d, e = np.inner(point1-point0, zaxis0), np.inner(point1-point0, zaxis1)
            origin_list[i] = point0
            t1 = -d/a
            origin_list[i+1] = point1 + zaxis1 * t1
            xaxis_list[i] = origin_list[i+1] - origin_list[i]
            xaxis_list[i+1] = xaxis_list[i]
        else:
            xaxis_list[i] = xaxis0
            xaxis_list[i+1] = xaxis0
            # reference: https://zhuanlan.zhihu.com/p/470278186
            a, b, c = np.inner(zaxis0, zaxis1), np.inner(zaxis0, zaxis0), np.inner(zaxis1, zaxis1)
            d, e = np.inner(point1-point0, zaxis0), np.inner(point1-point0, zaxis1)
            t0 = (a*e-c*d)/(a*a-b*c)
            t1 = b/a*t0-d/a
            # 垂直
            # if np.abs(a) <= epsilon:
            #     origin_list[i] = point1
            #     origin_list[i+1] = point1
            # else:
                # 异面
                # 垂足: point0 + zaxis0 * t1; point1 + zaxis1 * t1
            origin_list[i] = point0 + zaxis0 * t0
            origin_list[i+1] = point1 + zaxis1 * t1
                #dist = origin_list[i+1] - origin_list[i]
                # print("垂直1:{0}, 垂直2:{1}".format(np.inner(dist, zaxis0), np.inner(dist, zaxis1)))
                # print("origin0={0}, origin1={1}".format(origin_list[i], origin_list[i+1]))
    if log:
        print("origin_list=", origin_list)
        print("xaxis_list=", xaxis_list)
    #return modified_dh_params_list
    return origin_list, xaxis_list, zaxis_list

def get_MDH_params(origin_list, xaxis_list, zaxis_list):
    num = len(xaxis_list)
    MDH_params_list = [np.zeros(4)] * (num-1)
    for i in range(num-1):
        zaxis0, zaxis1 = zaxis_list[i], zaxis_list[i+1]
        xaxis0, xaxis1 = xaxis_list[i], xaxis_list[i+1]
        origin0, origin1 = origin_list[i], origin_list[i+1]

        d = np.inner(origin1-origin0, zaxis1) / np.linalg.norm(zaxis1)
        a = np.inner(origin1-origin0, xaxis0) / np.linalg.norm(xaxis0)
        theta = np.arccos(np.clip(np.inner(xaxis0/np.linalg.norm(xaxis0), xaxis1/np.linalg.norm(xaxis1)), -1.0, 1.0))
        if np.inner(np.cross(xaxis0, xaxis1), zaxis1) < 0:
            theta = - theta
        alpha = np.arccos(np.clip(np.inner(zaxis0/np.linalg.norm(zaxis0), zaxis1/np.linalg.norm(zaxis1)), -1.0, 1.0))
        if np.inner(np.cross(zaxis0, zaxis1), xaxis0) < 0:
            alpha = - alpha

        # alpha, a, theta, d in wikipedia
        # also alpha, d, theta, r in symoro
        MDH_params_list[i] = [alpha, a, theta, d]
    return MDH_params_list

def get_MDH_frame(origin_list, xaxis_list, zaxis_list):
    MDH_frame_list = []
    for origin, xaxis, zaxis in zip(origin_list, xaxis_list, zaxis_list):
        yaxis = -np.cross(xaxis, zaxis)
        xaxis = xaxis / np.linalg.norm(xaxis)
        yaxis = yaxis / np.linalg.norm(yaxis)
        zaxis = zaxis / np.linalg.norm(zaxis)
        tf = np.eye(4)
        tf[:3, 0] = xaxis
        tf[:3, 1] = yaxis
        tf[:3, 2] = zaxis
        tf[:3, 3] = origin
        MDH_frame_list.append(tf)
    return MDH_frame_list

def clean_folder(fileName):
        abs_path = os.path.dirname(fileName)
        file_list = os.listdir(abs_path)
        for file in file_list:
            if file.startswith("generated_"):
                os.remove(os.path.join(abs_path, file))