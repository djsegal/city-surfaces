"""
Copyright 2020 Nvidia Corporation
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
Mapillary Dataset Loader
"""
import os
import json

from collections import namedtuple
from config import cfg
from runx.logx import logx
from datasets.base_loader import BaseLoader
from datasets.utils import make_dataset_folder
from datasets import uniform


Label = namedtuple( 'Label' , [

    'name'        , # The identifier of this label, e.g. 'car', 'person', ... .
    # We use them to uniquely name a class

    'id'          , # An integer ID that is associated with this label.
    # The IDs are used to represent the label in ground truth images
    # An ID of -1 means that this label does not have an ID and thus
    # is ignored when creating ground truth images (e.g. license plate).
    # Do not modify these IDs, since exactly these IDs are expected by the
    # evaluation server.

    'trainId'     , # Feel free to modify these IDs as suitable for your method. Then create
# ground truth images with train IDs, using the tools provided in the
# 'preparation' folder. However, make sure to validate or submit results
# to our evaluation server using the regular IDs above!
# For trainIds, multiple labels might have the same ID. Then, these labels
# are mapped to the same class in the ground truth images. For the inverse
# mapping, we use the label that is defined first in the list below.
# For example, mapping all void-type classes to the same ID in training,
# might make sense for some approaches.
# Max value is 255!
    'color'       , # The color of this label
] )

labels = [
    #       name                     id    trainId     color
    Label(  'concrete'             ,  1 ,        0 , (255, 97, 39) ),
    Label(  'bricks'               ,  2 ,        1 , (244, 35,232) ),
    Label(  'granite'              ,  3 ,        2 , (102,102,153) ),
    Label(  'asphalt'              ,  4 ,        3 , ( 85, 85, 85) ),
    Label(  'mixed'                ,  5 ,        4 , (204,153,102) ),
    Label(  'road'                 ,  6 ,        5 , (128, 64,128) ),
    Label(  'background'           ,  7 ,        6 , (0,  0,  0) ),
    Label(  'granite block-stone'  ,  8 ,        7 , (236,  0, 140) ),
    Label(  'hexagonal'            ,  9 ,        8 , (125, 125, 125) ),
    Label(  'cobblestone'          ,  10,        9 , (133, 96, 168) ),
]


name2label      = { label.name    : label for label in labels           }
# id to label object
id2label        = { label.id      : label for label in labels           }
# trainId to label object
trainId2label   = { label.trainId : label for label in reversed(labels) }
# label2trainid
label2trainid   = { label.id      : label.trainId for label in labels   }
# trainId to label object
trainId2name   = { label.trainId : label.name for label in labels   }
trainId2color  = { label.trainId : label.color for label in labels      }



class Loader(BaseLoader):
    num_classes = 10
    ignore_label = -1
    trainid_to_name = {}
    color_mapping = []

    def __init__(self, mode, quality='semantic', joint_transform_list=None,
                 img_transform=None, label_transform=None, eval_folder=None):

        super(Loader, self).__init__(quality=quality,
                                     mode=mode,
                                     joint_transform_list=joint_transform_list,
                                     img_transform=img_transform,
                                     label_transform=label_transform)

        root = cfg.DATASET.CITYSURFACES_DIR
        self.id_to_trainid = label2trainid
        self.trainid_to_name = trainId2name
        self.fill_colormap()

        ######################################################################
        # Assemble image lists
        ######################################################################
        if mode == 'folder':

            img_ext = 'png'
            mask_ext = 'png'
            img_root = os.path.join(root, 'val', 'images')
            mask_root = os.path.join(root, 'val', 'annotations')
            self.all_imgs = self.find_images(img_root, mask_root, img_ext,
                                             mask_ext)
        elif mode =='test':
            self.all_imgs = make_dataset_folder(eval_folder, testing=True)
        else:
            splits = {'train': 'train',
                      'val': 'val',
                      'test': 'tests'}
            split_name = splits[mode]
            img_ext = 'png'
            mask_ext = 'png'
            img_root = os.path.join(root, split_name, 'images')
            mask_root = os.path.join(root, split_name, 'annotations')
            self.all_imgs = self.find_images(img_root, mask_root, img_ext,
                                             mask_ext)
        logx.msg('all imgs {}'.format(len(self.all_imgs)))
        self.fine_centroids = uniform.build_centroids(self.all_imgs,
                                                      self.num_classes,
                                                      self.train,
                                                      cv=cfg.DATASET.CV,
                                                      id2trainid=self.id_to_trainid)
        self.centroids = self.fine_centroids

        self.build_epoch()

    def fill_colormap(self):
        palette = [255, 97, 39,
                   244, 35, 232,
                   102, 102, 153,
                   85, 85, 85,
                   204, 153, 102,
                   128, 64, 128,
                   0, 0, 0,
                   236, 0, 140,
                   125, 125, 125,
                   133, 96, 168]

        zero_pad = 256 * 3 - len(palette)
        for i in range(zero_pad):
            palette.append(0)
        self.color_mapping = palette



