import os
import time
import datetime
import argparse

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision
import torchvision.transforms as transforms
from torchvision.datasets import CIFAR10, MNIST

import matplotlib.pyplot as plt

# from model import ResNet, Bottleneck, BasicBlock
from models import get_model
from utils import save_result, make_folder

import warnings
warnings.filterwarnings('ignore')

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', help='A or B dataset', default='cifar10', type=str)
    parser.add_argument('--model', help='Model Name', default='resnet18', type=str)
    parser.add_argument('--in_channels', help='Channels of input Image', default=3, type=int)
    parser.add_argument('--num_classes', help='Number of Classes', default=10, type=int)
    parser.add_argument('--batch_norm', help='Using Batch Normalization', default=False, type=bool)
    parser.add_argument('--train_batch_size', help='Batch size of Training dataset', default=256, type=int)
    parser.add_argument('--test_batch_size', help='Batch size of Testing dataset', default=128, type=int)
    parser.add_argument('--epoch', help='Size of Epoch', default=20, type=int)
    parser.add_argument('--lr', help='Learning Rate', default=0.01, type=float)
    parser.add_argument('--momentum', help='Momentum', default=0.9, type=float)
    parser.add_argument('--cuda', help='Using GPU', default=True, type=bool)
    parser.add_argument('--resume', help='Start from checkpoint', default='', type=str)
    parser.add_argument('--save_result', help='Save Result of Train&Test', default=True, type=bool)
    parser.add_argument('--save_folder', help='Directory of Saving weight', default='train0', type=str)
    parser.add_argument('--modify', help='Use If code need to be modify', action='store_true')
    opt = parser.parse_args()
    
    return opt


def train(model, dataloader, optimizer, loss_func, device, start_epoch, scheduler, e):
    print(f'EPOCH[{e+1}/{start_epoch+opt.epoch}] Training....')
    model.train()
    iter_loss = []
    corrects = 0
    data_size = 0
      
    for i, (images, labels) in enumerate(dataloader):
        images, labels = images.to(device), labels.to(device)
        data_size += images.shape[0]
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = loss_func(outputs, labels)
        loss.backward()
        optimizer.step()

        iter_loss.append(loss.item())
        corrects += sum(outputs.argmax(axis=1) == labels).item()

        if ((i+1) % 40 == 0) or ((i+1) == len(dataloader)) :
            print(f'Iter[{i+1}/{len(dataloader)}]'\
                  f'--- Loss: {sum(iter_loss)/data_size:0.4f}'\
                  f' --- Accuracy: {corrects/data_size:0.2f}'\
                  f'--- LR: {scheduler.get_lr()[0]:0.4f}')
            
    return [sum(iter_loss)/data_size, corrects/data_size]


def test(model, dataloader, loss_func, device, start_epoch, e):
    print(f'EPOCH[{e+1}/{start_epoch+opt.epoch}] Teseting....')
    model.eval()
    iter_loss = []
    corrects = 0
    
    with torch.no_grad():
        data_size = 0
        for i, (images, labels) in enumerate(dataloader):
            images, labels = images.to(device), labels.to(device)
            data_size += images.shape[0]
            
            outputs = model(images)
            loss = loss_func(outputs, labels)
            
            iter_loss.append(loss.item())
            corrects += sum(outputs.argmax(axis=1) == labels).item()
    
    print(f'Iter[{i+1}/{len(dataloader)}]' \
          f'--- Loss: {sum(iter_loss)/data_size:0.4}'\
          f'--- Accuracy: {corrects/data_size:0.2}')
    
    return [sum(iter_loss)/data_size, corrects/data_size]
            
        
def main(opt):
    
    # make folder
    base_path = 'result'
    os.makedirs(base_path, exist_ok=True)
    result_path = make_folder(base_path, opt.save_folder)      
    
    # Dataset
    from datasets import get_dataset_path
    print('Preparing Dataset....')
    # datasets = {
    #     'mnist': r'C:\Users\gjust\Documents\Github\data',
    #     'cifar10': r'C:\Users\gjust\Documents\Github\data',
    #     'cifar100': r'C:\Users\gjust\Documents\Github\data'
    # }
    data_path = get_dataset_path[opt.dataset]
    
    # Load Dataset
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],std=[0.229, 0.224, 0.225])
    ])
        
    if opt.dataset == 'mnist':
        train_set = MNIST(root=data_path, transform=transform, train=True, download=True)
        test_set = MNIST(root=data_path, transform=transform, train=False, download=True)
    elif opt.dataset == 'cifar10':
        train_set = CIFAR10(root=data_path, transform=transform, train=True, download=True)
        test_set = CIFAR10(root=data_path, transform=transform, train=False, download=True)
    elif opt.dataset == 'cifar100':
        train_set = CIFAR100(root=data_path, transform=transform, train=True, download=True)
        test_set = CIFAR100(root=data_path, transform=transform, train=False, download=True)
               
    train_loader = DataLoader(train_set, batch_size=opt.train_batch_size, shuffle=True)
    test_loader = DataLoader(test_set, batch_size=opt.test_batch_size, shuffle=False)
     
    # GPU
    device = 'cuda' if (torch.cuda.is_available() and opt.cuda) else 'cpu'
    print(f'Using {device}')
    
    # model
    print('Preparing Model....')
    model = get_model(opt.model, opt.num_classes)
    model.to(device)
    
    # resuming
    if opt.resume:
        print('Resuming from checkpoint')
        assert os.path.isdir(f'{opt.resume}')
        checkpoint = torch.load(f'{opt.resume}/{opt.model}_ckpt.pth')
        model.load_state_dict(checkpoint['model'])
        best_acc = checkpoint['acc']
        start_epoch = checkpoint['epoch']
        train_result = checkpoint['train_result']
        test_result = checkpoint['test_result']
    else:
        start_epoch = 0
        best_acc = 0
        train_result, test_result = [], [] 
        
        
    # optmizer
    loss_func = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=opt.lr, weight_decay=0.0001)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=200)
    
    # Training
    start = time.time()
    for e in range(start_epoch, start_epoch+opt.epoch):
        train_result += train(model, train_loader, optimizer, loss_func, device, start_epoch, scheduler, e)
        test_result += test(model, test_loader, loss_func, device, start_epoch, e)
        scheduler.step()
        
        # Save checkpoint
        if test_result[1::2][-1] > best_acc:
            print(f'Saving Model....({result_path})')
            state = {
                'model': model.state_dict(),
                'epoch': e+1,
                'acc': test_result[1::2][-1],
                'train_result': train_result,
                'test_result': test_result
            }
            torch.save(state, f'{result_path}/{opt.model}_ckpt.pth')
            best = test_result[1::2][-1]
            
        # Save Result
        if opt.save_result:
            print(f'Saving Result....({result_path})')
            save_result(train_result, test_result, result_path)
            
    end = time.time()
    with open(f'{result_path}/time_log.txt', 'w') as f:
        f.write(str(datetime.timedelta(seconds=end-start)))
        f.close()
    
          

if __name__ == '__main__':
    opt = parse_opt()
    
    main(opt)
    
