import os
from tkinter import Image
import cv2
import numpy as np
from PIL import ImageDraw, Image, ImageFont
import pyrebase
from flask import Flask, request, render_template, send_from_directory
from matplotlib import image

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

firebaseConfig = {
  "apiKey": "AIzaSyDx_6xMeQy8C4H6suV9U0WYoKvZgY_vbj4",
  "authDomain": "paddydetection.firebaseapp.com",
  "projectId": "paddydetection",
  "storageBucket": "paddydetection.appspot.com",
  "messagingSenderId": "608821823972",
  "appId": "1:608821823972:web:fde37577d32a8a89355ff1",
  "measurementId": "G-F7F1YCQF34",
  "databaseURL": ""
};
firebase = pyrebase.initialize_app(firebaseConfig)
storage = firebase.storage()
__author__ = 'ibininja'

app = Flask(__name__)


APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@app.route("/")
def index():
    return render_template("upload.html")
def getSize(txt, font):
    testImg = Image.new('RGB', (2, 2))
    testDraw = ImageDraw.Draw(testImg)
    return testDraw.textsize(txt, font)


@app.route("/upload", methods=["POST"])
def upload():
    target = os.path.join(APP_ROOT, 'images/')
    print(target)
    if not os.path.isdir(target):
            os.mkdir(target)
    else:
        print("Couldn't create upload directory: {}".format(target))
    print(request.files.getlist("file"))
    for upload in request.files.getlist("file"):
        print(upload)
        print("{} is the file name".format(upload.filename))
        filename = upload.filename
        citra = Image.open(upload.stream)
        citra.save("test.png")
        destination = "/".join([target, filename])
        print ("Accept incoming file:", filename)
        print ("Save it to:", destination)
        upload.save(destination)
        analisis()
    # return send_from_directory("images", filename, as_attachment=True)
    return render_template("complete.html", image_name=filename)

@app.route('/upload/<filename>')
def send_image(filename):
    return send_from_directory("images", filename)

@app.route('/gallery')
def get_gallery():
    image_names = os.listdir('./images')
    print(image_names)
    return render_template("gallery.html", image_names=image_names)

def analisis():
    img = cv2.imread("test.png")

    scalePercent = 0.5

    # hitung ukuran baru
    width = int(img.shape[1] * scalePercent)
    height = int(img.shape[0] * scalePercent)
    newSize = (width, height)

    # tentukan ukuran gambar
    img = cv2.resize(img, newSize, None, None, None, cv2.INTER_AREA)

    # Convert gambar ke HSV
    hsvImage = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # tentukan nilai HSV untuk warna hijau:
    lowerValuesYellow = np.array([10, 70, 100])
    upperValuesYellow = np.array([33, 255, 255])

    # tentukan nilai HSV untuk warna hijau:
    lowerValuesGreen = np.array([30, 73, 10])
    upperValuesGreen = np.array([70, 255, 255])

    # buat mask dari HSV kuning
    hsvMaskYellow = cv2.inRange(hsvImage, lowerValuesYellow, upperValuesYellow)

    # buat mask dari HSV hijau
    hsvMaskGreen = cv2.inRange(hsvImage, lowerValuesGreen, upperValuesGreen)

    # mask dan input gambar
    hsvOutputYellow = cv2.bitwise_and(img, img, mask=hsvMaskYellow)
    hsvOutputGreen = cv2.bitwise_and(img, img, mask=hsvMaskGreen)

    # tampilkan gambar dan mask
    #cv2.imshow("gambar original", img)
    #cv2.imshow("gambar mask kuning", hsvMaskYellow)
    #cv2.imshow("gambar mask hijau", hsvMaskGreen)

    # rasio warna dari gambar
    ratio_yellow = cv2.countNonZero(hsvMaskYellow)/(img.size/1.5)
    ratio_green = cv2.countNonZero(hsvMaskGreen)/(img.size/1.5)

    # hitung persentase warna
    colorPercentYellow = (ratio_yellow * 100) / scalePercent
    colorPercentGreen = (ratio_green * 100) / scalePercent

    # Print nilai persentase kuning dan hijau
    print('Nilai persentase kuning:', np.round(colorPercentYellow, 2))
    print('Nilai persentase hijau:', np.round(colorPercentGreen, 2))
    kuning = np.round(colorPercentYellow, 2)
    hijau = np.round(colorPercentGreen, 2)

    if np.round(colorPercentGreen) < np.round(colorPercentYellow):
        print("Padi matang")
        hasil = "Padi matang"
        text = f"Nilai persentase kuning: {np.round(colorPercentYellow, 2)} \nNilai persentase hijau: {np.round(colorPercentGreen, 2)} \nHasil: {hasil}"
    else:
        print("Padi tidak matang")
        hasil = "Padi tidak matang"
        text = f"Nilai persentase kuning: {np.round(colorPercentYellow, 2)} \nNilai persentase hijau: {np.round(colorPercentGreen, 2)} \nHasil: {hasil}"
    fontname = "arial.ttf"
    fontsize = 36   

    
    colorText = "black"
    #colorOutline = "red"
    colorBackground = "white"

    font = ImageFont.truetype(fontname, fontsize)
    width, height = getSize(text, font)
    img = Image.new('RGB', (width+1000, height+1000), colorBackground)
    d = ImageDraw.Draw(img)
    d.text((3, height/2), text, fill=colorText, font=font)
    #d.rectangle((0, 0, width+1000, height+1000), outline=colorOutline)
    
    img.save("images/image.png")
    db.collection('output').document('hasil').set({'kuning': kuning, 'hijau': hijau, 'hasil': hasil})
    # tampilkan gambar
    #cv2.imshow("gambar untuk warna kuning", np.hstack([img, hsvOutputYellow]))
    #cv2.imshow("gambar untuk warna hijau", np.hstack([img, hsvOutputGreen]))
    #cv2.waitKey(0)
    doc_ref = db.collection(u'cities').document(u'SF')
    storage.child('images/image.png').put('images/image.png')

    doc = doc_ref.get()
    if doc.exists:
        print(f'Document data: {doc.to_dict()}')
    else:
        print(u'No such document!')
        
if __name__ == "__main__":
    app.run(port=4555, debug=True)