# Part 2 - Building the command line application
#
# Now that you've built and trained a deep neural network on the flower data set, it's time to convert it into an application that others can use. Your application should be a 
# pair of Python scripts that run from the command line. For testing, you should use the checkpoint you saved in the first part.
# The second file, predict.py, uses a trained network to predict the class for an input image. Feel free to create as many other files as you need.
# Predict flower name from an image with predict.py along with the probability of that name. That is, you'll pass in a single image /path/to/image and return the flower name and class probability.
# Basic usage: python predict.py /path/to/image checkpoint
# Options:
# - Return top KK most likely classes: python predict.py input checkpoint --top_k 3
# - Use a mapping of categories to real names: python predict.py input checkpoint --category_names cat_to_name.json
# - Use GPU for inference: python predict.py input checkpoint --gpu

# python predict.py --image_path flowers/test/11/image_03098.jpg --checkpoint_path checkpoints/checkpoint.pth --top_k 5 --category_names cat_to_name.json --gpu

import os

import numpy as np

import matplotlib.pyplot as plt

import torch
from torch import nn
from torch import optim
import torch.nn.functional as F
from torch.autograd import Variable

import torchvision
from torchvision import datasets, transforms, models

from collections import OrderedDict

import json

import time

from PIL import Image

import argparse


def parse_input_arguments():
    parser = argparse.ArgumentParser(description = "Predict using a deep neural network")
    parser.add_argument('--image_path', type = str, help = 'Dataset path')
    parser.add_argument('--checkpoint_path', type = str, help = 'Path to load trained model checkpoint')
    parser.add_argument('--top_k', type = int, default = 5, help = 'Top K most likely classes')
    parser.add_argument('--category_names', type = str, help = 'File .json for the mapping of categories to real names')
    parser.add_argument('--gpu', action = "store_true", default = True, help = 'Use GPU if available')

    args = parser.parse_args()
    #print(args)

    return args.image_path, args.checkpoint_path, args.top_k, args.category_names, args.gpu


def load_checkpoint(file_path):
    checkpoint = torch.load(file_path)
    learning_rate = checkpoint['learning_rate']
    model = getattr(torchvision.models, checkpoint['network'])(pretrained = True)
    model.classifier = checkpoint['classifier']
    model.epochs = checkpoint['epochs']
    model.optimizer = checkpoint['optimizer']
    model.load_state_dict(checkpoint['state_dict'])
    model.class_to_idx = checkpoint['class_to_idx']
    
    return model


def process_image(pil_image):
    ''' Scales, crops, and normalizes a PIL image for a PyTorch model,
        returns an Numpy array
    '''
    
    size_crop = 224
    size_resize = 256
    normalize_mean = [0.485, 0.456, 0.406]
    normalize_std = [0.229, 0.224, 0.225]
    
    img_loader = transforms.Compose([transforms.Resize(size_resize),
                                     transforms.CenterCrop(size_crop), 
                                     transforms.ToTensor()])
    
    #pil_image = Image.open(image)
    pil_image = img_loader(pil_image).float()
    
    np_image = np.array(pil_image)    
    
    mean = np.array(normalize_mean)
    std = np.array(normalize_std)
    np_image = (np.transpose(np_image, (1, 2, 0)) - mean) / std    
    np_image = np.transpose(np_image, (2, 0, 1))
            
    return np_image


def predict(pil_image, model, top_k_probabilities = 5):
    ''' Predict the class (or classes) of an image using a trained deep learning model.
    '''
    
    # Use GPU if it's available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    #print(device)

    model.to(device)
    model.eval()
    
    np_image = process_image(pil_image)
    tensor_image = torch.from_numpy(np_image)
    
    inputs = Variable(tensor_image)
    
    if torch.cuda.is_available():
        inputs = Variable(tensor_image.float().cuda())           
        
    inputs = inputs.unsqueeze(dim = 0)
    log_probabilities = model.forward(inputs)
    probabilities = torch.exp(log_probabilities)    

    top_probabilities, top_classes = probabilities.topk(top_k_probabilities, dim = 1)
    #print(top_probabilities)
    #print(top_classes)
    
    class_to_idx_inverted = {model.class_to_idx[c]: c for c in model.class_to_idx}
    top_mapped_classes = list()
    
    for label in top_classes.cpu().detach().numpy()[0]:
        top_mapped_classes.append(class_to_idx_inverted[label])
    
    return top_probabilities.cpu().detach().numpy()[0], top_mapped_classes


if __name__ == "__main__":

    image_path, checkpoint_path, top_k, category_names, gpu = parse_input_arguments()
    # print(image_path)
    # print(checkpoint_path)
    # print(top_k)
    # print(category_names)
    # print(gpu)
    
    if image_path == None:
        print('Please insert the image path')
        exit()
    else:
        # Load the model
        print('Load the checkpoint from {}'.format(checkpoint_path))
        model = load_checkpoint(checkpoint_path)
        # print(model)

        path_parts = image_path.split('/')
        real_category = path_parts[-2] # we know the directory structure so the penultimate component of the path is the categoryh path/category/image.jpg
        
        pil_image = Image.open(image_path)
        #plt.imshow(pil_image) 

        # Load .json mapping file from category label to category name
        with open('cat_to_name.json', 'r') as f:
            category_label_to_name = json.load(f)
            # print(category_label_to_name)

        top_probabilities, top_classes = predict(pil_image, model, top_k_probabilities = top_k)

        print('Probabilities: ', top_probabilities)
        #print(top_classes)
        print('Categories:    ', [category_label_to_name[c] for c in top_classes])
        print('True category: ', category_label_to_name[real_category])
else:
    print("Error: script can not run as imported module")


