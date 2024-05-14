# import the necessary packages
import argparse
#import imutils
#import cv2
#from skimage.metrics import structural_similarity

def compareBySSMI(image1_path, image2_path):
	"""
	Compares two images using the Structural Similarity Index (SSIM) between them.
	
	Args:
	    image1_path (str): The path to the first input image.
	    image2_path (str): The path to the second input image.
	
	Returns:
	    None.
	
	"""

	# load the two input images
	imageA = cv2.imread(image1_path)
	imageB = cv2.imread(image2_path)
	# convert the images to grayscale
	print("going to get cvt")
	grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
	grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)

	# compute the Structural Similarity Index (SSIM) between the two
	# images, ensuring that the difference image is returned
	print("going to ssmi")
	#(score, diff) = structural_similarity(grayA, grayB)
	(score, diff) = structural_similarity(imageA, imageB)
	diff = (diff * 255).astype("uint8")
	print("SSIM: {}".format(score))

	# threshold the difference image, followed by finding contours to
	# obtain the regions of the two input images that differ
	thresh = cv2.threshold(diff, 0, 255,
		cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)

	# loop over the contours
	for c in cnts:
		# compute the bounding box of the contour and then draw the
		# bounding box on both input images to represent where the two
		# images differ
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(imageA, (x, y), (x + w, y + h), (0, 0, 255), 2)
		cv2.rectangle(imageB, (x, y), (x + w, y + h), (0, 0, 255), 2)

	print("going to show")
	# show the output images
	cv2.imshow("Original", imageA)
	cv2.imshow("Modified", imageB)
	cv2.imshow("Diff", diff)
	cv2.imshow("Thresh", thresh)
	print("done")
	cv2.waitKey(0)



def compare_images(image1_path, image2_path):
    # Read the images
    image1 = cv2.imread(image1_path)
    image2 = cv2.imread(image2_path)
    
    # Check if the images are the same size
    if image1.shape != image2.shape:
        return False
    
    # Compute the difference between the images
    diff = cv2.absdiff(image1, image2)
    
    # Check if the images are identical (i.e., the difference is all zeros)
    return not diff.any()

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--first", required=True,
	help="first input image")
ap.add_argument("-s", "--second", required=True,
	help="second")
args = vars(ap.parse_args())


image1_path = args["first"]
image2_path = args["second"]
diff = compare_images(image1_path, image2_path)
print(diff)
