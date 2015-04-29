#!/usr/bin/python3

import png
from sys import argv
#from tkfiledialog import askopenfilename
import tkinter
#import imagetk
#from PIL import Image, ImageTk
import numpy as np


NEW_FILE_SUFFIX = "FIXED"

def showUsage():
    print("Usage:", argv[0], "filename")

def writeToFile(targetFilename, theWidth, theHeight, pixels):
    """Expects pixels in boxed row flat pixel form"""
    with open(targetFilename, 'wb') as f:
        png.Writer(width=theWidth, height=theHeight).write(f, p) 

theImage = None

def getCornerCoordinates(theFilename, width, height, pixels):
    """
    Prompt user for corners of a square on the image.
    Returned as a 4-tuple of 2-tuple image coordinate pairs.
    """
    root = tkinter.Tk()
    #w = tkinter.Label(root, text="Hello")
    #w.pack()
    #w.mainloop()
    frame = tkinter.Frame(root, bd=2, relief=tkinter.SUNKEN)
    #frame.grid_rowconfigure(0, weight=1)
    #frame.grid_columnconfigure(0, weight=1)
    #xscroll = tkinter.Scrollbar(frame, orient=tkinter.HORIZONTAL)
    #xscroll.grid(row=1, column=0, sticky=tkinter.E+tkinter.W)
    #yscroll = tkinter.Scrollbar(frame)
    #yscroll.grid(row=0, column=1, sticky=tkinter.N+tkinter.S)

    
    #canvas = tkinter.Canvas(frame, bd=0, xscrollcommand=xscroll.set,
    #    yscrollcommand=yscroll.set)
    canvas = tkinter.Canvas(frame, bd=0)
    frame.pack(fill=tkinter.NONE)  

    # Keep a reference to image to prevent it from being garbage collected
    global theImage

    theImage = tkinter.PhotoImage(file=theFilename)
    canvas.create_image(10,10, image=theImage, anchor="nw")
    canvas.image = theImage
    #canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
    canvas.pack(expand=True, fill=tkinter.X)
    canvas.config(scrollregion=canvas.bbox(tkinter.ALL))
    
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
    (width, height, pixels, meta) = png.Reader(filename = theFilename).asRGB() 

    #assert len(pixels) / 3 == height

    imgList = [[],[],[]]
    colorList = [[],[],[]]

    for y in range(height):
        print("Writing row", y)
        row = next(pixels)

        assert len(row) / 3 == width

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
            
            colorList[0].append(row[x*3])
            colorList[1].append(row[x*3 + 1])
            colorList[2].append(row[x*3 + 2])

    print("len(imgList[0]", len(imgList[0]))
    print("len(colorList[1]", len(colorList[1]))
    print("width", width)
    print("height", height)
    print("width * height", width * height)

    assert len(imgList[0]) == (width * height)

    return (np.array(imgList), np.array(colorList))

if __name__ == "__main__":
    if len(argv) < 2:
        showUsage()
        exit()

    theFilename = argv[1]
    print("Processing file:", theFilename)
    
    #(w, h, p, m) = png.Reader(filename = theFilename).asRGB() 
    #(w,h,p,m) = (None,None,None,None)

    (cameraPoints, cameraColors) = fileToMatrices(theFilename)

    print("cameraPoints", cameraPoints)
    print("cameraColors", cameraColors)

    #print("w:", w)
    #print("h:", h)
    #assert len(p) == h
    #assert (len(next(p)) / 3) == w
    #print("p len next:", len(next(p)))
    #print("p next:", next(p))
    #print("m next:", next(p))

    #(c0, c1, c2, c3) = getCornerCoordinates(theFilename, w, h, p)
    
    # Test points for board.png
    (c0, c1, c2, c3) = ((358,36),(329,597),(592,157),(580,483))
    print("Corners", c0, c1, c2, c3)

    wVec = np.array([1,0,0,0,0,0,0,0,0])

    equationsList = [
        makeEquationsForPoints(c0[0], c0[1], 0, 0)[0],
        makeEquationsForPoints(c0[0], c0[1], 0, 0)[1],
        makeEquationsForPoints(c1[0], c1[1], 0, 1)[0],
        makeEquationsForPoints(c1[0], c1[1], 0, 1)[1],
        makeEquationsForPoints(c2[0], c2[1], 1, 0)[0],
        makeEquationsForPoints(c2[0], c2[1], 1, 0)[1],
        makeEquationsForPoints(c3[0], c3[1], 1, 1)[0],
        makeEquationsForPoints(c3[0], c3[1], 1, 1)[1],
        wVec
    ] 
    #print("Got equationsList", equationsList)
    #for equation in equationsList:
    #    print(equation)

    #lMat = np.concatenate(equationsList)
    lMat = np.vstack(equationsList)
    b = np.array([0,0,0,0,0,0,0,0,1])

    print("lMat:\n", lMat)
    print("b:\n", b)

 
    # Solve L * H = b
    hVec = np.linalg.lstsq(lMat, b)[0]

    print("hVec:\n", hVec)

    rotatedPoints = hVec * cameraPoints

    print("rotatedPoints", rotatedPoints)


    splitFilename = theFilename.split('.')
    newFilename= ".".join(splitFilename[:-1]) + "." + NEW_FILE_SUFFIX + \
        "." + splitFilename[-1]

    print("Saving new image as", newFilename)

    writeToFile(newFilename, w, h, p)
   
     
