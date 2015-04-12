#!/usr/bin/python3

from sys import argv


def showUsage():
    print("Usage:", argv[0], "filename")

if __name__ == "__main__":
    print("Helloo!")
    if len(argv) < 2:
        showUsage()
        exit()


    filename = argv[0]
    print("Processing file:", filename)
    



