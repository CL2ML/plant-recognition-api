print('setting the environment...')
# Import env variables
import os
from dotenv import load_dotenv
from config import config
# Load environmental variables from .env in development stage
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# import libraries
print('importing libraries...')
import time
# import fastai libs
from fastai import *
from fastai.vision import *

# import settings
from resources.settings import * # import

print('done! Setting up the directories and the model structure...\n')


#-----------------------------------
# Prior wrangling and model setup

# set dir structure
def make_dirs(labels, data_dir):
	root_dir = os.getcwd()
	#make_dirs = ['train', 'valid', 'test']
	make_dirs = ['data']
	for n in make_dirs:
		name = os.path.join(root_dir, data_dir, n)
		for each in labels:
			os.makedirs(os.path.join(name, each), exist_ok=True)

make_dirs(labels=labels, data_dir=data_dir) # comes from settings.py
path = Path(data_dir)

# download model weights if not already saved (model can be stored elsewhere if needed)
path_to_model = os.path.join(data_dir, 'models', trained_model_file) # MOdel name taken from settings.py
print(path_to_model,'\n')
if not os.path.exists(path_to_model):
	print('done! Model weights were not found, downloading them...\n')
	os.makedirs(os.path.join(data_dir, 'models'), exist_ok=True)
	filename = Path(path_to_model)
	r = requests.get(MODEL_URL)
	filename.write_bytes(r.content)

print('done! Loading up the saved model weights...\n')

defaults.device = torch.device('cpu') # run inference on cpu
empty_data = ImageDataBunch.single_from_classes(
	path, labels, ds_tfms=get_transforms(), size=224, num_workers=0).normalize(imagenet_stats)
learn = cnn_learner(empty_data, base_arch = models.resnet34, pretrained=False) # model_type coming from settings.py
learn = load_learner(path = os.path.join(data_dir, 'models'), file = trained_model_file)

print('done! Initiating the model...\n')

#-------------------------------------------
# The Flask App routings
from flask import Flask, request, jsonify
#from PIL import Image

app = Flask(__name__)

# Pass loading the config environment variable when rendered on render.com
# For render.com the default options are then applied, i.e. production mode
try:
    app.config.from_object(config[os.environ.get('FLASK_CONFIG')])
except Exception as:
    pass

@app.route("/")
def hello():
	return "Image classification API v1.0\n"

@app.route('/api/v1.0/classify', methods=['POST'])
def predict():

	file = request.files['image']

	img = open_image(file)
	print('Image opened succesfully with Fastai open_image()...')

	app.logger.info("Classifying image")
	t = time.time() # get execution time

	pred_class, pred_idx, outputs = learn.predict(img)

	confidence = float(outputs[pred_idx])
	
	print('The predicted plant class is: ', pred_class)

	print('pred_idx', pred_idx)

	print('outputs', confidence)

	dt = time.time() - t
	app.logger.info("Execution time: %0.02f seconds" % (dt))
	app.logger.info("Image classified as %s with a confidence level of %s" % (str(pred_class), str(confidence)))

	return jsonify({'plant_class':str(pred_class), 'confidence':confidence})


if __name__ == '__main__':
	app.run()



