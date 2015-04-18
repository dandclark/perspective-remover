#!/usr/bin/python3

import png
from sys import argv
#from tkfiledialog import askopenfilename
import tkinter
#import imagetk
#from PIL import Image, ImageTk

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
    Returned as a 4-tuple of image coordinate pairs.
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
    
    
    def printCoords(event):
        print (event.x, event.y)

    canvas.bind("<Button 1>", printCoords)
 
    root.mainloop()
    


    return (None, None, None, None)



if __name__ == "__main__":
    print("Helloo!")
    if len(argv) < 2:
        showUsage()
        exit()


    theFilename = argv[1]
    print("Processing file:", theFilename)
    
    #(w, h, p, m) = png.Reader(filename = theFilename).asRGB() 
    (w,h,p,m) = (None,None,None,None)

    print("w:", w)
    print("h:", h)
    #print("p len next:", len(next(p)))
    #print("m len next:", len(next(p)))
    #print("p next:", next(p))
    #print("m next:", next(p))

    (c0, c1, c2, c3) = getCornerCoordinates(theFilename, w, h, p)





    splitFilename = theFilename.split('.')
    newFilename= ".".join(splitFilename[:-1]) + "." + NEW_FILE_SUFFIX + \
        "." + splitFilename[-1]

    print("Saving new image as", newFilename)

    writeToFile(newFilename, w, h, p)
   
     
