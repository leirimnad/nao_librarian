# coding=utf-8

import cv2
import numpy as np


def get_warped_image(img, debug=False):
    try:
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_blur = cv2.GaussianBlur(img_gray, (3, 3), 0)

        edges = cv2.Canny(image=img_blur, threshold1=100, threshold2=200)  # Canny Edge Detection

        if debug:
            # Display Canny Edge Detection Image
            cv2.imshow('Canny Edge Detection', edges)
            cv2.waitKey(0)

        def get_lines(threshold):
            hough_lines = cv2.HoughLines(edges, 1, np.pi / 180 * 0.5, threshold)

            if hough_lines is None:
                return []

            # remove lines with close values
            lines = []
            for line in hough_lines:
                rho, theta = line[0]
                if len(lines) == 0:
                    lines.append(line)
                else:
                    for line2 in lines:
                        rho2, theta2 = line2[0]
                        if abs(rho - rho2) < 20 and abs(theta - theta2) < 0.2:
                            break
                    else:
                        lines.append(line)
            return lines

        th = 100
        res_lines = get_lines(th)
        while len(res_lines) > 4:
            th += 1
            res_lines = get_lines(th)

        def get_points(lines):
            intersection_points = []
            for i in range(len(lines)):
                for j in range(i + 1, len(lines)):
                    rho1, theta1 = lines[i][0]
                    rho2, theta2 = lines[j][0]
                    ar_1 = np.array([
                        [np.cos(theta1), np.sin(theta1)],
                        [np.cos(theta2), np.sin(theta2)]
                    ])
                    ar_2 = np.array([[rho1], [rho2]])
                    x0, y0 = np.linalg.solve(ar_1, ar_2)
                    x0, y0 = int(np.round(x0)), int(np.round(y0))
                    intersection_points.append((x0, y0))

            # Delete insane points
            intersection_points = [point for point in intersection_points if
                                0 < point[0] < img.shape[1] and 0 < point[1] < img.shape[0]]
            return intersection_points

        res_points = get_points(res_lines)

        if debug:
            img_copy = img.copy()
            # Draw lines on the image
            for line_ in res_lines:
                rho_, theta_ = line_[0]
                a = np.cos(theta_)
                b = np.sin(theta_)
                x0_ = a * rho_
                y0_ = b * rho_
                x1_ = int(x0_ + 10000 * (-b))
                y1_ = int(y0_ + 10000 * a)
                x2_ = int(x0_ - 10000 * (-b))
                y2_ = int(y0_ - 10000 * a)

                cv2.line(img_copy, (x1_, y1_), (x2_, y2_), (0, 0, 255), 2)

            # Draw intersection points
            for x, y in res_points:
                cv2.circle(img_copy, center=(x, y), radius=3, color=(0, 255, 0), thickness=-1)

            cv2.imshow('Hough Lines', img_copy)
            cv2.waitKey(0)

        def order_points(pts):
            rect = np.zeros((4, 2), dtype="float32")
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
            return rect

        def four_point_transform(image, pts):
            rect = order_points(pts)
            tl, tr, br, bl = rect
            width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            max_width = max(int(width_a), int(width_b))
            height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            max_height = max(int(height_a), int(height_b))
            dst = np.array([
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1]], dtype="float32")
            m = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(image, m, (max_width, max_height))
            return warped

        if len(res_points) != 4:
            return None
        warped_image = four_point_transform(img, np.array(res_points))

        if debug:
            cv2.imshow('Warped', warped_image)
            cv2.waitKey(0)

            cv2.destroyAllWindows()

        return warped_image
    except:
        return None