# coding=utf-8

import numpy as np


def get_distance(x_pos, y_pos, img):
    h_fov = 60.97
    v_fov = 47.64

    eps_x = img.shape[1] / 2 - x_pos
    lh = img.shape[1] / 2 / np.tan(np.radians(h_fov / 2))
    alpha_h = np.arctan(-eps_x / lh)

    eps = img.shape[0] / 2 - y_pos
    focal_length = img.shape[0] / 2 / np.tan(np.radians(v_fov / 2))
    alpha = np.arctan(abs(eps) / focal_length)
    beta = np.radians(50.3) + alpha * np.sign(eps)  # 50.3 is the default angle
    dist_head = 48 / np.cos(beta)
    vertical_distance = 48 * np.tan(beta)  # 48 is the height of the lower camera
    horizontal_distance = np.tan(alpha_h) * vertical_distance
    distance = vertical_distance / np.cos(alpha_h)

    rotation = np.arctan(horizontal_distance / focal_length)

    return vertical_distance, horizontal_distance, distance, rotation


def save_image(img, file_path):
    # type: (tuple, str) -> None
    rgb_image = img[6]
    np_arr = np.fromstring(rgb_image, np.uint8)
    # np_arr = np_arr.reshape(960, 1280, 3)
    cv2.imwrite(file_path, np_arr)
