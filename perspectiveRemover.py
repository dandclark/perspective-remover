#!/usr/bin/python3

from sys import argv
import png

NEW_FILE_SUFFIX = "FIXED"

def showUsage():
    print("Usage:", argv[0], "filename")

def writeToFile(targetFilename, theWidth, theHeight, pixels):
    """Expects pixels in boxed row flat pixel form"""
    with open(targetFilename, 'wb') as f:
        png.Writer(width=theWidth, height=theHeight).write(f, p) 


if __name__ == "__main__":
    print("Helloo!")
    if len(argv) < 2:
        showUsage()
        exit()


    theFilename = argv[1]
    print("Processing file:", theFilename)
    
    (w, h, p, m) = png.Reader(filename = theFilename).asRGB() 

    print("w:", w)
    print("h:", h)
    #print("p len next:", len(next(p)))
    #print("m len next:", len(next(p)))
    #print("p next:", next(p))
    #print("m next:", next(p))


    splitFilename = theFilename.split('.')
    newFilename= ".".join(splitFilename[:-1]) + "." + NEW_FILE_SUFFIX + \
        "." + splitFilename[-1]

    print("Saving new image as", newFilename)

    writeToFile(newFilename, w, h, p)
   
     
