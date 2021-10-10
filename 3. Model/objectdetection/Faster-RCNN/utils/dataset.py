import os
from random import sample

import torch
from torchvision.datasets import CocoDetection

from pycocotools.coco import COCO

from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

class myCocoDetection(CocoDetection):
    def __init__(
        self, root, annFile, transform, remove_invalid_data=True, show=False
    ):
        super(myCocoDetection, self).__init__(root, annFile)
        
        # self.coco = COCO(annFile)
        # self.ids = list(sorted(self.coco.imgs.keys()))
        if remove_invalid_data:
            ids = []
            for img_id in self.ids:
                ann_ids = self.coco.getAnnIds(imgIds=img_id)
                anno = self.coco.loadAnns(ann_ids)
                # print(len(anno))
                if self.is_valid_data(anno):
                    ids.append(img_id)
            self.ids = ids
            
        self.transform = transform
        self.show = show
        
    # 물체가 없거나 bbox가 1보다 작은 경우 제외
    def is_valid_data(self, anno):
        if len(anno) == 0:
            return False
        for obj in anno:
            for o in obj['bbox'][2:]:
                if o <= 1:
                    return False
        return True
            
    
    def __getitem__(self, index: int):
        idx = self.ids[index]
        image = self._load_image(idx)
        target = self._load_target(idx)
        
        bboxes, labels = [], []
        for obj in target:
            bbox = [obj['bbox'][0],
                    obj['bbox'][1],
                    obj['bbox'][0] + obj['bbox'][2],
                    obj['bbox'][1] + obj['bbox'][3]]
            bboxes.append(bbox)
            labels.append(obj['category_id'])
            
        if self.show:
            return image, bboxes, labels
        
        if self.transform:
            image = self.transform(image)
            bboxes = self.transform(np.array(bboxes)).reshape(-1, 4)
            
            targets ={}
            labels = torch.tensor(labels).type(torch.int64)
            bboxes = bboxes.type(torch.FloatTensor)
            targets['boxes'] = bboxes
            targets['labels'] = labels
            
            return idx, image, targets        
            
        return image, bboxes, labels
    
    def _load_image(self, id):
        path = self.coco.loadImgs(id)[0]["file_name"]
        return Image.open(os.path.join(self.root, path)).convert("RGB")

    def _load_target(self, id):
        return self.coco.loadAnns(self.coco.getAnnIds(id))


# Specific Classes
class myCocolimit(CocoDetection):
    def __init__(
        self, root, annFile, transform, class_list, remove_invalid_data=True, show=False
    ):
        super(myCocolimit, self).__init__(root, annFile)
        
        self.class_list = class_list        
        self.catIds = self.coco.getCatIds(catNms=self.class_list)
        self.ids = []
        for id in self.catIds:
            self.ids.extend(self.coco.getImgIds(catIds=id))

        if remove_invalid_data:
            ids = []
            for img_id in self.ids:
                ann_ids = self.coco.getAnnIds(imgIds=img_id)
                anno = self.coco.loadAnns(ann_ids)
                # print(len(anno))
                if self.is_valid_data(anno):
                    ids.append(img_id)
            self.ids = ids
            
        self.transform = transform
        self.show = show
        
    # 물체가 없거나 bbox가 1보다 작은 경우 제외
    def is_valid_data(self, anno):
        if len(anno) == 0:
            return False
        for obj in anno:
            for o in obj['bbox'][2:]:
                if o <= 1:
                    return False
        return True
            
    
    def __getitem__(self, index: int):
        idx = self.ids[index]
        image = self._load_image(idx)
        target = self._load_target(idx)
        
        bboxes, labels = [], []
        for obj in target:
            bbox = [obj['bbox'][0],
                    obj['bbox'][1],
                    obj['bbox'][0] + obj['bbox'][2],
                    obj['bbox'][1] + obj['bbox'][3]]
            bboxes.append(bbox)
            labels.append(obj['category_id'])
            
        if self.show:
            return image, bboxes, labels
        
        if self.transform:
            image = self.transform(image)
            bboxes = self.transform(np.array(bboxes)).reshape(-1, 4)
            
            targets ={}
            labels = torch.tensor(labels).type(torch.int64)
            bboxes = bboxes.type(torch.FloatTensor)
            targets['boxes'] = bboxes
            targets['labels'] = labels
            
            return idx, image, targets        
            
        return image, bboxes, labels
    
    def _load_image(self, id):
        path = self.coco.loadImgs(id)[0]["file_name"]
        return Image.open(os.path.join(self.root, path)).convert("RGB")

    def _load_target(self, id):
        original = self.coco.loadAnns(self.coco.getAnnIds(id))
        new = [ann for ann in original if ann['category_id'] in self.catIds]
        return new
    


def coco_show(dataset, shape=(2,2), figsize=(10,10)):
    CLASSES = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
    'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'N/A', 'dining table',
    'N/A', 'N/A', 'toilet', 'N/A', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book',
    'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]
    
    size = shape[0] * shape[1]
    nums = sample(range(0, len(dataset)), size)
    
    fig, axes = plt.subplots(*shape, figsize=figsize)
    axes = axes.ravel() if isinstance(axes, np.ndarray) else [axes]
    
    for i, num in enumerate(nums):
        image_id, image, target = dataset.__getitem__(num)
        image = image.permute(1,2,0)
        boxes = target['boxes']
        labels = target['labels']
        
        for box, label in zip(boxes, labels):
            rect = patches.Rectangle((box[0], box[1]), 
                                     box[2]-box[0], box[3]-box[1], 
                                     linewidth=1, edgecolor='r', facecolor='none')
            axes[i].add_patch(rect)
            axes[i].text(box[0], box[1], CLASSES[label], fontsize=15)
            
        axes[i].imshow(image)
        axes[i].axis('off')
        axes[i].set_title(f'Image ID :{image_id}')
        
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    
    import torchvision.transforms as transforms
    from torch.utils.data import DataLoader

    import pprint
    pp = pprint.PrettyPrinter()

    def collate_fn(batch):
        return tuple(zip(*batch))

    train_path = r'C:\Users\gjust\Documents\Github\data\COCO\val2017'
    train_ann = r'C:\Users\gjust\Documents\Github\data\COCO\annotations\instances_val2017.json'
    dataset = myCocolimit(root=train_path, annFile=train_ann, 
                          transform=transforms.ToTensor(), class_list=['person', 'dog'])
    
    print(dataset)
    
    # print(dataset.__annotations__)
    # dataloader = DataLoader(dataset, batch_size=1, shuffle=False, collate_fn=collate_fn)

    # img_ids, images, targets = iter(dataloader).next()
    # print(img_ids)
    coco_show(dataset, shape=(2,2))