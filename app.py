from PIL import Image, ImageChops, ImageEnhance, ImageOps
import requests
import os
from flask import Flask, redirect, jsonify, render_template, request, send_file, send_from_directory
import werkzeug
import datetime
import uuid

app = Flask(__name__)

ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def process_image(img):
  BLEND_PCT = 0.45

  #open up the mask
  logo = Image.open('mask.png')
  logo = logo.convert('RGBA')

  #open gradient
  gradient = Image.open('mask.jpg')
  gradient = gradient.convert('RGBA')
  gradient = gradient.resize(img.size, Image.ANTIALIAS)

  #make sure logo matches the size of the image
  logo_width = min(img.size) / 4
  logo_aspect = float(logo.size[1]) / logo.size[0]
  logo_size = (logo_width, logo_aspect * logo_width)
  logo = logo.resize(map(int, logo_size), Image.ANTIALIAS)

  #make sure our image has alpha channel
  img = img.convert('RGBA')

  #unique name
  filename = uuid.uuid4().hex + '.png'
  filename = os.path.join('/tmp', filename)

  #put in gradient
  graded = Image.blend(img, gradient, BLEND_PCT)
  #then the logo
  logo_bot_right = map(lambda x: x * .95, graded.size)
  logo_top_left = map(lambda x, y: x - y, logo_bot_right, logo.size)
  graded.paste(logo, map(int, logo_top_left + logo_bot_right), logo)
  graded.save(filename, 'PNG')

  #send it back
  return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hackru', methods=['POST'])
def classify_upload():
  try:
    #get the image from the request
    imagefile = request.files['imagefile']
    filename_ = str(datetime.datetime.now()).replace(' ', '_') + \
            werkzeug.secure_filename(imagefile.filename)
    filename = os.path.join('/tmp', filename_)

    #make sure it has the correct file type
    if not any(ext in filename for ext in ALLOWED_IMAGE_EXTENSIONS):
      return 'Invalid filetype.'

    #save the file to /tmp
    imagefile.save(filename)
    #open the image for Pillow
    image = Image.open(filename)
  except Exception as err:
    #uh oh. Something went wrong.
    print 'Uploaded image open error: ' + err
    return 'Error: ' + err

  #process the image
  resultFilename = process_image(image)
  #send it back
  return send_file(resultFilename, mimetype='image/png', as_attachment=True, attachment_filename='hackrued.png')

@app.route('/templates/<path:path>')
def send_static(path):
    return send_from_directory('templates', path)

if __name__ == '__main__':
  port = int(os.environ.get("PORT", 8000))
  app.run(host='0.0.0.0', debug=True, port=port)
