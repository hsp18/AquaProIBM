import numpy as np
import cv2
import requests
import time

def skeletonize(img):
    """
    :param img: input image to be skeletonized
    :return: the skeletonized mask
    """

    # create copies of the image
    img = img.copy()
    skel = img.copy()

    # extract the structural element from the image
    skel[:, :] = 0
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    while True:

        # erode and dilate the image using morphological operation
        eroded = cv2.morphologyEx(img, cv2.MORPH_ERODE, kernel)
        temp = cv2.morphologyEx(eroded, cv2.MORPH_DILATE, kernel)
        temp = cv2.subtract(img, temp)
        skel = cv2.bitwise_or(skel, temp)
        img[:, :] = eroded[:, :]
        if cv2.countNonZero(img) == 0:
            break

    return skel

"""
Find the output mask of the input image
"""
def detectCrack():
    global usermail
    img = cv2.imread("4.jpg")

    # blur the image and extract the edges
    blur_gray = cv2.GaussianBlur(img, (5, 5), 0)
    edges = cv2.Canny(blur_gray, 50, 150, apertureSize=3)

    # shade the border lines that are thick
    lines = cv2.HoughLinesP(image=edges, rho=1, theta=np.pi / 180, threshold=100, lines=np.array([]), minLineLength=100, maxLineGap=80)
    a, b, c = lines.shape
    for i in range(a):
        cv2.line(img, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (169, 169, 169), 3,cv2.LINE_AA)

    # binarize the image after blurring
    median = cv2.medianBlur(img, 5)
    im_bw = cv2.threshold(median, 20, 255, cv2.THRESH_BINARY_INV)[1]
    gray_img = cv2.cvtColor(im_bw, cv2.COLOR_RGB2GRAY)

    # skeletonize the image and save the corresponding output
    global skel
    skel = skeletonize(gray_img)
    cv2.imwrite("mask2.png", skel)

    #check if there's a crack found, by checking for  pixel values

    if np.amax(skel)>0:
        pload = {"msg_from_rpi" : "Crack Detected"}
        r = requests.post("http://localhost:5000/notify/" + usermail,data=pload)
        #http://ip172-18-0-56-budsnbhqckh000fp2g7g-5000.direct.labs.play-with-docker.com/login
        print("Crack Found")
        print(r)

usermail = "harish.s.pukale123@gmail.com"
for i in range(10):
    detectCrack()
    time.sleep(5)

