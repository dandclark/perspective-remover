# perspective-remover

Python script for transforming an image of a flat surface to remove perspective, synthesizing a new image with the surface appearing head-on.

The user provides corners of a rectangle in the angled image through mouse clicks.  The script creates the corresponding image in a new coordinate frame such that the image is rotated to directly face the camera.  Uses the method developed in the Perspective Removal lab of Philip Klein's excellent Linear Algebra course at https://www.coursera.org/course/matrix 

Uses Johann C Rocholl's png.py PNG encoder/decoder.

Requires numpy to better facilitate some vector/matrix operations.

## Examples

Before | After
------------- | -------------
![Birds, original](https://raw.github.com/dandclark/perspective-remover/master/demo/birds.png) | ![Birds, perspective removed](https://raw.github.com/dandclark/perspective-remover/master/demo/birds.FIXED.png)
![Book, original](https://raw.github.com/dandclark/perspective-remover/master/demo/book.png)  | ![Book, perspective removed](https://raw.github.com/dandclark/perspective-remover/master/demo/book.FIXED.png)

