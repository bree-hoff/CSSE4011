'''
No need to run this file, learner should be exported to export.pkl.
But maybe good to check on other file systems I suppose?

Adapted from fast.ai course.
'''
import os
import ssl
import fastai
from fastcore.all import *
from fastai.data.all import *
from fastai.vision.all import *


types = 'call', 'dislike','fist','four','like','mute','ok','one','palm','peace', 'peace_inverted', 'rock', 'stop', 'stop_inverted', 'three', 'three2', 'two_up', 'two_up_inverted', 'relaxed'


path = '/Users/brianna/Documents/2024/Semester 1/CSSE4011/Project/project_repo/CSSE4011/training_images/'
dls = DataBlock(
    blocks=(ImageBlock, CategoryBlock), 
    get_items=get_image_files, 
    splitter=RandomSplitter(valid_pct=0.2, seed=42),
    get_y=parent_label,
    item_tfms=[Resize(192, method='squish')]
).dataloaders(path, bs=32)

dls.show_batch(max_n=6)

learn = vision_learner(dls, resnet18, metrics=error_rate)
learn.fine_tune(3)

learn.export(fname="different_export.pkl")