import pdf2image
import os
import shutil


'''
Converts the PDF to a folder of images
'''
def PDFToImage(pdfPath, res=400):
    imageList = pdf2image.convert_from_path(pdfPath, res, poppler_path='/opt/homebrew/bin')

    nameWithExtension = pdfPath.rsplit('/')[-1]
    filename = nameWithExtension.rsplit(".")[0].replace(" ", "_")

    try:
        os.mkdir(os.getcwd() + '/' +filename)
    except FileExistsError:
        print("Folder already exists")
        shutil.rmtree(os.getcwd() + '/' +filename)
        os.mkdir(os.getcwd() + '/' + filename)

    for i, image in enumerate(imageList):
        image.save(f'{os.getcwd() + "/" + filename}/{filename}_{i}.png', 'PNG')


def grayscale(dir):
    for filename in os.listdir(dir):
        f = cv2.imread(dir+"/"+filename)

        gray_image = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        thresh, im_bw = cv2.threshold(gray_image, 160,230, cv2.THRESH_BINARY)
        cv2.imwrite(dir + '/'+ filename, im_bw)


'''
Code to straighten the pdf
'''
def getSkewAngle(cvImage) -> float:
    # Prep image, copy, convert to gray scale, blur, and threshold
    newImage = cvImage.copy()
    gray = cv2.cvtColor(newImage, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Apply dilate to merge text into meaningful lines/paragraphs.
    # Use larger kernel on X axis to merge characters into single line, cancelling out any spaces.
    # But use smaller kernel on Y axis to separate between different blocks of text
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
    dilate = cv2.dilate(thresh, kernel, iterations=2)

    # Find all contours
    contours, hierarchy = cv2.findContours(dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)
    for c in contours:
        rect = cv2.boundingRect(c)
        x,y,w,h = rect
        cv2.rectangle(newImage,(x,y),(x+w,y+h),(0,255,0),2)

    # Find largest contour and surround in min area box
    largestContour = contours[0]
    print (len(contours))
    minAreaRect = cv2.minAreaRect(largestContour)
    cv2.imwrite("temp/boxes.jpg", newImage)
    # Determine the angle. Convert it to the value that was originally used to obtain skewed image
    angle = minAreaRect[-1]
    if angle < -45:
        angle = 90 + angle
    return -1.0 * angle
# Rotate the image around its center
def rotateImage(cvImage, angle: float):
    newImage = cvImage.copy()
    (h, w) = newImage.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    newImage = cv2.warpAffine(newImage, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return newImage

# Deskew image
def deskew(cvImage):
    angle = getSkewAngle(cvImage)
    return rotateImage(cvImage, -1.0 * angle)

def finalDeskew(dir):
    for filename in os.listdir(dir):
        f = cv2.imread(dir + "/" + filename)

        straight = deskew(f)
        cv2.imwrite(dir + "/" + filename, straight)



import pytesseract
import cv2
from PIL import Image

#Uses a modifer to use rows instead of columnms
pytesseract.pytesseract.tesseract_cmd = r'/opt/local/bin/tesseract'
custom_config_psm6 = r'--oem 3 --psm 6 -c page_separator='''


if __name__ == '__main__':
    folder_path = '/Users/gautamnair/PycharmProjects/pdfReader/PDFS'
    try:
        os.mkdir(folder_path + "_Text")
    except FileExistsError:
        print("Folder already exists")
        shutil.rmtree(folder_path + "_Text")
        os.mkdir(folder_path + "_Text")
    for fn in os.listdir(folder_path):
        PDFToImage(folder_path + '/' + fn)
        realFile = fn.rsplit(".")[0].replace(" ", "_")
        grayscale(os.getcwd() + '/' + realFile)
        finalDeskew(os.getcwd() + '/' + realFile)

        for imageFile in os.listdir(os.getcwd() + '/' + realFile):
            img = Image.open(os.getcwd() + '/' + realFile + "/" + imageFile)
            ocr_result = pytesseract.image_to_string(img, config=custom_config_psm6)

            with open(folder_path + "_Text" + '/' + realFile + '.txt', 'a') as f:
                f.write(str(ocr_result))
                f.write("\n\n")
        shutil.rmtree(realFile)
