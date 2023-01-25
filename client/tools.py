# coding=utf-8

import numpy as np
import cv2


def get_distance(x_pos, y_pos, img):
    """
    Returns different distances from the camera to the point on image.
    :param x_pos: x position of the point on image
    :param y_pos: y position of the point on image
    :param img: image
    :return: distance from feet on vertical axis, distance from feet on horizontal axis, distance from camera, rotation
    """

    h_fov = 60.97
    v_fov = 47.64
    camera_angle = 50.3
    camera_height = 48

    eps_x = img.shape[1] / 2 - x_pos
    lh = img.shape[1] / 2 / np.tan(np.radians(h_fov / 2))
    alpha_h = np.arctan(-eps_x / lh)

    eps = img.shape[0] / 2 - y_pos
    focal_length = img.shape[0] / 2 / np.tan(np.radians(v_fov / 2))
    alpha = np.arctan(abs(eps) / focal_length)
    beta = np.radians(camera_angle) + alpha * np.sign(eps)
    dist_head = camera_height / np.cos(beta)
    vertical_distance = camera_height * np.tan(beta)
    horizontal_distance = np.tan(alpha_h) * vertical_distance
    distance = vertical_distance / np.cos(alpha_h)

    rotation = np.arctan(horizontal_distance / vertical_distance)

    return vertical_distance, horizontal_distance, distance, rotation


def save_image(img, file_path):
    """Saves image to file path"""
    # type: (tuple, str) -> None
    np_arr = nparr_from_image(img)
    cv2.imwrite(file_path, np_arr)


def nparr_from_image(img):
    """Converts NAO image to numpy array"""
    image = img[6]
    np_arr = np.frombuffer(image, np.uint8)
    np_arr = np_arr.reshape(img[1], img[0], 3)
    return np_arr
