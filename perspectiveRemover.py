#!/usr/bin/python3

import png
from sys import argv
#from tkfiledialog import askopenfilename
import tkinter
#import imagetk
#from PIL import Image, ImageTk
import numpy as np


NEW_FILE_SUFFIX = "FIXED"

# Color for pixels in corrected PNG not covered by a rotated
# pixel from the original image
DEFAULT_IMAGE_BACKGROUND_RGB = (0, 0, 255) 

# Cap the size of each axis of the adjusted image at this number of pixels
MAX_IMAGE_SIZE = 2000


def showUsage():
    print("Usage:", argv[0], "filename")

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
    print("Got image corners")

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

def fileToMatrices(filename):
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
    # TODO Should we use the alpha channel as well?
    (width, height, pixels, meta) = png.Reader(filename = theFilename).asRGBA() 

    imgList = [[],[],[]]
    colorList = [[],[],[]]

    for y in range(height):
        row = next(pixels)

        # Each pixel has R, G, B, and Alpha.
        assert len(row) / 4 == width

        for x in range(0, width):
            pixelIndex = y*width + x
            #print("Writing pixel at (%i, %i)" % (x, y))
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
            # And we skip the alpha channel

    print("len(imgList[0]", len(imgList[0]))
    print("len(colorList[1]", len(colorList[1]))
    print("width", width)
    print("height", height)
    print("width * height", width * height)

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


def matricesToFile(points, colors, width, height, filename):
    """
    Translates point locations and colors to a flat image and
    saves it to a png.
    TODO Should the flattening of points to the image plane
    be refactored out of this function?

    Input: Takes points and colors arrays specified as follows,
    and a filename.
    
    points is a 3xN matrix where each column is a point in the
    rotated coordinate space.

    colors is the corresponding 3xN matrix of colors for each point in the
    point matrix. Where the columns again correspond to
    each point and the rows are the R,G,B values of each pixel. 
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

    newWidth = int((maxX - minX) * scalingFactor) + 1
    newHeight = int((maxY - minY) * scalingFactor) + 1

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
            pixels[-1].append(255)
            pixels[-1].append(0)
            pixels[-1].append(0)

    for i in range(len(points[0])):
        assert points[2][i] == 1
        y = (points[1][i] - minY) * scalingFactor
        x = (points[0][i] - minX) * scalingFactor

        # Round to integers
        y = int(y + 0.5)
        x = 3 * min(int(x + 0.5), newWidth - 1)

        # Only project the point if it lies between the image bounds
        # TODO Should calculate image size based on extremes of
        # rotated points.
        if x >= 0 and x < newWidth * 3 and y >= 0 and y < newHeight:
            pixels[y][x] = colors[0][i]
            pixels[y][x+1] = colors[1][i]
            pixels[y][x+2] = colors[2][i]
        else:
            print("x,y (%i,%i)" % (x,y))
            print("newWidth, newHeight %i,%i" % (newWidth, newHeight))
            print("newWidth * 3", newWidth * 3) 
            print("minX, maxX %f,%f" % (minX, maxX))
            print("minY, maxY %f,%f" % (minY, maxY))
            print("points[0][i]", points[0][i])
            print("points[1][i]", points[1][i])
            assert False

    
    with open(filename, 'wb') as f:
        png.Writer(width=newWidth, height=newHeight).write(f, pixels) 

if __name__ == "__main__":
    if len(argv) < 2:
        showUsage()
        exit()

    theFilename = argv[1]
    print("Processing file:", theFilename)
    
    #(w, h, p, m) = png.Reader(filename = theFilename).asRGB() 
    #(w,h,p,m) = (None,None,None,None)

    (width, height, pixelArray, cameraPoints, cameraColors) = fileToMatrices(theFilename)

    print("cameraPoints", cameraPoints)
    print("cameraColors", cameraColors)

    #print("w:", w)
    #print("h:", h)
    #assert len(p) == h
    #assert (len(next(p)) / 3) == w
    #print("p len next:", len(next(p)))
    #print("p next:", next(p))
    #print("m next:", next(p))

    
    # Test points for board.png
    #(c0, c1, c2, c3) = ((358,36),(592,157),(580,483),(329,597))
    (c0, c1, c2, c3) = getCornerCoordinates(theFilename)
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

    print("lMat:\n", lMat)
    print("b:\n", b)

    # Solve L * H = b
    hVec = np.linalg.lstsq(lMat, b)[0]

    hVec = hVec.reshape((3,3))

    print("hVec:\n", hVec)

    rotatedPoints = np.dot(hVec, cameraPoints)
    rotatedAndProjectedPoints = projectToImagePlane(rotatedPoints)

    print("rotatedPoints", rotatedPoints)
    print("rotatedAndProjectedPoints", rotatedAndProjectedPoints)

    splitFilename = theFilename.split('.')
    newFilename= ".".join(splitFilename[:-1]) + "." + NEW_FILE_SUFFIX + \
        "." + splitFilename[-1]

    print("Saving new image as", newFilename)

    matricesToFile(rotatedAndProjectedPoints, cameraColors, width, height, newFilename)

    #writeToFile(newFilename, w, h, p)
   
     
