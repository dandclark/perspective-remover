#!/usr/bin/python3
#
# perspectiveRemover.py
#
# Copyright (C) 2015 Daniel Clark
#
# LICENSE (The MIT License)
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
Python script for removing perspective from an image taken at an angle
with respect to the subject.
The user provides corners of a rectangle in the angled image through mouse
clicks.  The script creates the corresponding image in a new coordinate
frame such that the image is rotated to directly face the camera.

Uses the method developed in the Perspective Removal lab of Philip Klein's
excellent Linear Algebra course at https://www.coursera.org/course/matrix

Uses Johann C Rocholl's png.py PNG encoder/decoder.
"""

import argparse
from sys import argv
import tkinter
import numpy as np

import png


DEFAULT_NEW_FILE_SUFFIX = "FIXED"

# Color for pixels in corrected PNG not covered by a rotated
# pixel from the original image
DEFAULT_IMAGE_BACKGROUND_RGB = (0, 0, 0) 

# Cap the size of each axis of the adjusted image at this number of pixels
MAX_IMAGE_SIZE = 2000


def getArgs():
    """
    Reads and validates command line parameters from sys.argv.  Halts the program
    if any invalid values are received.
    """
    argParser = argparse.ArgumentParser(description="Remove perspective from image of a flat surface.")
    argParser.add_argument("-s", "--suffix", type=str, default=DEFAULT_NEW_FILE_SUFFIX,
        help="Suffix for altered image")
    argParser.add_argument("filename", type=str, help="Filename of image to alter")
    argParser.add_argument("-b", "--backgroundRGB", type=int, nargs=3,
        default=DEFAULT_IMAGE_BACKGROUND_RGB, help="0-255 R,G,B channel values for altered image background")
    args = argParser.parse_args()
    print(args)

    for color in args.backgroundRGB:
        if color < 0 or color > 255:
            print("Invalid value for backgroundRGB.  Requires a 0-255 value for each RGB channel.")
            exit()

    return args


def writeToFile(targetFilename, theWidth, theHeight, pixels):
    """Expects pixels in boxed row flat pixel form"""
    with open(targetFilename, 'wb') as f:
        png.Writer(width=theWidth, height=theHeight).write(f, p) 

theImage = None

def getCornerCoordinates(theFilename):
    """
    Prompt user for corners of a square on the image.
    Returned as a 4-tuple of 2-tuple image coordinate pairs.
    """
    root = tkinter.Tk()
    frame = tkinter.Frame(root, bd=2, relief=tkinter.SUNKEN)

    # Keep a reference to image to prevent it from being garbage collected
    # while we wait for the corner clicks
    global theImage
    theImage = tkinter.PhotoImage(file=theFilename)
    
    canvas = tkinter.Canvas(frame, bd=0, width=theImage.width(), height=theImage.height())
    frame.pack(fill=tkinter.NONE)  

    canvas.create_image(10,10, image=theImage, anchor="nw")
    canvas.image = theImage
    canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand='yes')
    
    corners = [] 
    
    def printCoords(event):
        nonlocal root, corners
        print (event.x, event.y)
        print("Clicked corner at (%d,%d)" % (event.x, event.y))
        corners.append((event.x, event.y))
        if(len(corners) == 4):
            root.quit()

    canvas.bind("<Button 1>", printCoords)
    
    print("Click the corners of a rectangle in the image") 
    root.mainloop()

    return (corner for corner in corners)

def makeEquationsForPoints(imageX, imageY, w1, w2):
    """
    Input: An (imageX, imageY) point on the image, and a (w1, w2) coordinate pair s.t.
    w1=realX/realZ, w2=realY/realZ where (realX,realY,realZ) is the corresponding
    point in the real world coordinate system. 
    
    Output: List [u,v] of D-vecs that define linear equations u*h == 0, v*h == 0
    """
    u = np.array([-imageX,-imageY,-1,0,0,0,w1*imageX,w1*imageY,w1])
    v = np.array([0,0,0,-imageX,-imageY,-1,w2*imageX,w2*imageY,w2])
    return [u,v]

def fileToMatrices(theFilename):
    """
    Input: Name of png file
    Output: (points, colors) tuple.
    
    points is a 3xN matrix where each column is a point in the
    original (W,H) image (1,1)(1,2)...(W,H) and the column labels
    are the 3 x1,x2,x3 dimensions of the point in the camera
    coordinate system.
   
    colors is the corresponding 3xN matrix of colors for each point in the
    original image, where the columns again correspond to
    each point and the rows are the R,G,B values of each pixel. 
    """
    
    # We retrieve the alpha channel here even though we're not going to use it
    # because asRGB (which doesn't provide the alpha channel) will throw if
    # given an image with an alpha channel.
    # TODO Should we actually make use of the alpha channel as well?
    (width, height, pixels, meta) = png.Reader(filename = theFilename).asRGBA() 

    imgList = [[],[],[]]
    colorList = [[],[],[]]

    for y in range(height):
        row = next(pixels)

        # Each pixel has R, G, B, and Alpha.
        assert len(row) / 4 == width

        for x in range(0, width):
            pixelIndex = y*width + x
            # Memory locality/cache performance is probably terrible
            # for this, should reevalutate if this turns out to
            # be a perf issue as there are definitely better ways
            # to set up these matrices.
            imgList[0].append(x)
            imgList[1].append(y)
            imgList[2].append(1)
            
            colorList[0].append(row[x*4])
            colorList[1].append(row[x*4 + 1])
            colorList[2].append(row[x*4 + 2])
            # ...and we skip the alpha channel

    assert len(imgList[0]) == (width * height)

    return (width, height, pixels, np.array(imgList), np.array(colorList))

def projectToImagePlane(points):
    """
    Input: A 3xN numpy array of (r0, r1, r2) points, where each column is
    a point in rotated coordinates

    Output: A 3xN numpy array of points, where each column is the point
    in the corresponding column in the input array, projected onto
    the image plane such that r2 == 1
    """
    projectedPoints = np.copy(points)

    for i in range(len(projectedPoints[0])):
        projectedPoints[0][i] /= projectedPoints[2][i] 
        projectedPoints[1][i] /= projectedPoints[2][i] 
        projectedPoints[2][i] = 1

    return projectedPoints


def pointsToImage(points, colors, width, height, shouldInterpolateMissingPixels, backgroundRGB):
    """
    Input: Points and colors arrays, where points is a 3xN matrix whose 
    columns are each a point in the rotated coordinate space.
    
    width and height are the dimensions of the original image, and will be
    considered when calculating the rotated image's size.

    If shouldInterpolateMissingPixels == True, then we'll do some averaging
    to figure out values for missing pixels in the rotated image, else
    we'll fill these in with default values.

    colors is the corresponding 3xN matrix of colors for each point in the
    point matrix, where the columns again correspond to
    each point and the rows are the R,G,B values of each pixel.

    Output: Returns the resulting image in boxed row flat pixel format.
    """
    assert len(points[0]) > 0
    assert len(points[0]) == len(colors[0])

    minX, maxX, minY, maxY = points[0][0], points[0][0], points[1][0], points[1][0]
    for i in range(len(points[0])):
        if points[0][i] < minX: minX = points[0][i]
        if points[0][i] > maxX: maxX = points[0][i]
        if points[1][i] < minY: minY = points[1][i]
        if points[1][i] > maxY: maxY = points[1][i]

    # We scale all points by the average for both axes of the ratio of the original
    # axis size and the magnitude of the range of points with respect to that axis
    # among the converted image points. 
    scalingFactor = ((width / (maxX - minX)) + (height / (maxY - minY))) / 2
    print("Using scalingFactor", scalingFactor)

    newWidth = int((maxX - minX) * scalingFactor) + 3
    newHeight = int((maxY - minY) * scalingFactor) + 2

    # Cap the new image at a maximum size
    newWidth = min(newWidth, MAX_IMAGE_SIZE)
    newHeight = min(newHeight, MAX_IMAGE_SIZE)

    print("min, max X: %f, %f" % (minX, maxX))
    print("min, max Y: %f, %f" % (minY, maxY))
    print("newWidth, newHeight %f, %f" % (newWidth, newHeight))
    
    # Set up the image background
    pixels = []
    for y in range(newHeight):
        pixels.append([])
        for x in range(newWidth):
            if shouldInterpolateMissingPixels:
                # We'll fill these in later
                pixels[-1].append(None)
                pixels[-1].append(None)
                pixels[-1].append(None)
            else:
                pixels[-1].append(backgroundRGB[0])
                pixels[-1].append(backgroundRGB[1])
                pixels[-1].append(backgroundRGB[2])

    for i in range(len(points[0])):
        assert points[2][i] == 1
        y = (points[1][i] - minY) * scalingFactor
        x = (points[0][i] - minX) * scalingFactor

        # Round to integers
        y = int(y + 0.5)
        x = 3 * min(int(x + 0.5), newWidth - 1)

        assert x >= 0 and x < newWidth * 3 and y >= 0 and y < newHeight
        pixels[y][x] = colors[0][i]
        pixels[y][x+1] = colors[1][i]
        pixels[y][x+2] = colors[2][i]

    if shouldInterpolateMissingPixels:
        pixels = interpolateMissingPixels(newWidth, newHeight, pixels, backgroundRGB)

    return pixels
 

def interpolateMissingPixels(width, height, image, backgroundRGB):
    """
    Input: Image of dimensions (width,height) in boxed row flat pixel format, potentially
    with some pixels with RGB values of (None, None, None).

    Output: The same image with the missing pixels filled in from an average of the
    surrounding pixels
    """
    for y in range(height):
        for x in range(width):
           if image[y][x*3] is None:
                colorTotal = [0, 0, 0]
                numAdjacentPixels = 0
                if y > 0:
                    if x > 0 and image[y-1][x*3-3] is not None:
                        colorTotal = [t + c for t,c in zip(colorTotal, image[y-1][x*3-3:x*3])]
                        numAdjacentPixels += 1
                    if x < width - 1 and image[y-1][x*3+3] is not None:
                        colorTotal = [t + c for t,c in zip(colorTotal, image[y-1][x*3+3:x*3+6])]
                        numAdjacentPixels += 1
                if y < height - 1:
                    if x > 0 and image[y+1][x*3-3] is not None:
                        colorTotal = [t + c for t,c in zip(colorTotal, image[y+1][x*3-3:x*3])]
                        numAdjacentPixels += 1
                    if x < width - 1 and image[y+1][x*3+3] is not None:
                        colorTotal = [t + c for t,c in zip(colorTotal, image[y+1][x*3+3:x*3+6])]
                        numAdjacentPixels += 1

                if numAdjacentPixels > 0:
                    colorAverage = [int(c / numAdjacentPixels) for c in colorTotal]
                else:
                    colorAverage = backgroundRGB

                image[y][x*3] = colorAverage[0]
                image[y][x*3 + 1] = colorAverage[1]
                image[y][x*3 + 2] = colorAverage[2]
    return image


if __name__ == "__main__":

    args = getArgs()

    print("Processing file:", args.filename)
    (width, height, pixelArray, cameraPoints, cameraColors) = fileToMatrices(args.filename)

    print("cameraPoints", cameraPoints)
    print("cameraColors", cameraColors)
    
    (c0, c1, c2, c3) = getCornerCoordinates(args.filename)
    print("Corners", c0, c1, c2, c3)

    wVec = np.array([1,0,0,0,0,0,0,0,0])

    equationsList = [
        makeEquationsForPoints(c0[0], c0[1], 0, 0)[0],
        makeEquationsForPoints(c0[0], c0[1], 0, 0)[1],
        makeEquationsForPoints(c1[0], c1[1], 1, 0)[0],
        makeEquationsForPoints(c1[0], c1[1], 1, 0)[1],
        makeEquationsForPoints(c2[0], c2[1], 1, 1)[0],
        makeEquationsForPoints(c2[0], c2[1], 1, 1)[1],
        makeEquationsForPoints(c3[0], c3[1], 0, 1)[0],
        makeEquationsForPoints(c3[0], c3[1], 0, 1)[1],
        wVec
    ] 

    lMat = np.vstack(equationsList)
    b = np.array([0,0,0,0,0,0,0,0,1])

    # Solve L * H = b
    hVec = np.linalg.lstsq(lMat, b)[0]

    hVec = hVec.reshape((3,3))

    rotatedPoints = np.dot(hVec, cameraPoints)
    rotatedAndProjectedPoints = projectToImagePlane(rotatedPoints)

    print("rotatedPoints", rotatedPoints)
    print("rotatedAndProjectedPoints", rotatedAndProjectedPoints)

    splitFilename = args.filename.split('.')
    newFilename= ".".join(splitFilename[:-1]) + "." + args.suffix + \
        "." + splitFilename[-1]

    print("Saving new image as", newFilename)

    image = pointsToImage(rotatedAndProjectedPoints, cameraColors, width, height, True, args.backgroundRGB)
    assert len(image[0]) % 3 == 0

    with open(newFilename, 'wb') as f:
        png.Writer(width=int(len(image[0]) / 3), height=len(image)).write(f, image) 
   
