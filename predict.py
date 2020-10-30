#!/usr/bin/python3
# predict on jpg files or mp4 video
import cv2
import torch
from glob import glob
import os
import os.path as osp
from pathlib import Path
from torchvision import transforms
from modules.dataloaders.utils import decode_segmap
from modules.models.deeplab_xception import DeepLabv3_plus
from modules.models.sync_batchnorm.replicate import patch_replication_callback
import numpy as np
from PIL import Image
from tqdm import tqdm
import jetson.utils
import time
import socket
from select import *
import sys
import os
from time import ctime
import threading
import sys
import subprocess

### RUN OPTIONS ###
MODEL_PATH = "/home/vision/Desktop/segmentation-selectstar-master/run/surface/deeplab/model_iou_77.pth.tar"
ORIGINAL_HEIGHT = 300
ORIGINAL_WIDTH = 300
MODEL_HEIGHT = 300
MODEL_WIDTH = 300
NUM_CLASSES = 7  # including background
CUDA = True if torch.cuda.is_available() else False




MODE = 'jpg'  # 'mp4' or 'jpg'
DATA_PATH = '/home/vision/Desktop/segmentation-selectstar-master/input/jpgs'  # .mp4 path or folder containing jpg images
OUTPUT_PATH = '/home/vision/Desktop/segmentation-selectstar-master/output/jpgs'  # where video file or jpg frames folder should be saved.


SHOW_OUTPUT = True if 'DISPLAY' in os.environ else False  # whether to cv2.show()

OVERLAPPING = True  # whether to mix segmentation map and original image
FPS_OVERRIDE = 60  # None to use original video fps

CUSTOM_COLOR_MAP = [
    [0, 0, 0],  # background
    [255, 128, 0],  # bike_lane
    [255, 0, 0],  # caution_zone
    [255, 0, 255],  # crosswalk
    [255, 255, 0],  # guide_block
    [0, 0, 255],  # roadway
    [0, 255, 0],  # sidewalk
]  # To ignore unused classes while predicting

CUSTOM_N_CLASSES = len(CUSTOM_COLOR_MAP)
######


class FrameGeneratorMP4:
    def __init__(self, mp4_file: str, output_path=None, show=True):
        assert osp.isfile(mp4_file), "DATA_PATH should be existing mp4 file path."
        self.vidcap = cv2.VideoCapture(mp4_file)
        self.fps = int(self.vidcap.get(cv2.CAP_PROP_FPS))
        self.total = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.show = show
        self.output_path = output_path

        if self.output_path is not None:
            os.makedirs(osp.dirname(output_path), exist_ok=True)
            self.fourcc = cv2.VideoWriter_fourcc(*'DIVX')

            if FPS_OVERRIDE is not None:
                self.fps = int(FPS_OVERRIDE)
            self.out = cv2.VideoWriter(OUTPUT_PATH, self.fourcc, self.fps, (ORIGINAL_WIDTH, ORIGINAL_HEIGHT))

    def __iter__(self):
        success, image = self.vidcap.read()
        for i in range(0, self.total):
            if success:
                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                yield np.array(img)

            success, image = self.vidcap.read()

    def __len__(self):
        return self.total

    def write(self, rgb_img):
        bgr = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

        if self.show:
            cv2.imshow('output', bgr)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print('User Interrupted')
                self.close()
                exit(1)

        if self.output_path is not None:
            self.out.write(bgr)

    def close(self):
        cv2.destroyAllWindows()
        self.vidcap.release()
        if self.output_path is not None:
            self.out.release()


class FrameGeneratorJpg:
    def __init__(self, jpg_folder: str, output_folder=None, show=True):
        assert osp.isdir(jpg_folder), "DATA_PATH should be directory including jpg files."
        self.files = sorted(glob(osp.join(jpg_folder, '*.jpg'), recursive=False))
        self.show = show
        self.output_folder = output_folder
        self.last_file_name = ""

        if self.output_folder is not None:
            os.makedirs(output_folder, exist_ok=True)

    def __iter__(self):
        for file in self.files:
            img = cv2.imread(file, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.last_file_name = str(Path(file).name)
            yield np.array(img)

    def __len__(self):
        return len(self.files)

    def write(self, rgb_img):
        bgr = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

        if self.show:
            cv2.imshow('output', bgr)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print('User Interrupted')
                self.close()
                exit(1)

        if self.output_folder is not None:
            path = osp.join(self.output_folder, f'{self.last_file_name}')
            cv2.imwrite(path, bgr)

    def close(self):
        cv2.destroyAllWindows()


class ModelWrapper:
    def __init__(self):
        self.composed_transform = transforms.Compose([
            transforms.Resize((MODEL_HEIGHT, MODEL_WIDTH), interpolation=Image.BILINEAR),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))])

        self.model = self.load_model(MODEL_PATH)

    @staticmethod
    def load_model(model_path):
        model = DeepLabv3_plus(nInputChannels=3, n_classes=NUM_CLASSES, os=16)
        if CUDA:
            model = torch.nn.DataParallel(model, device_ids=[0])
            patch_replication_callback(model)
            model = model.cuda()
        if not osp.isfile(MODEL_PATH):
            raise RuntimeError("=> no checkpoint found at '{}'".format(model_path))
        checkpoint = torch.load(model_path)
        if CUDA:
            model.module.load_state_dict(checkpoint['state_dict'])
        else:
            model.load_state_dict(checkpoint['state_dict'])
        print("=> loaded checkpoint '{}' (epoch: {}, best_pred: {})"
              .format(model_path, checkpoint['epoch'], checkpoint['best_pred']))
        model.eval()
        return model

    def predict(self, rgb_img: np.array):
        x = self.composed_transform(Image.fromarray(rgb_img))
        x = x.unsqueeze(0)

        if CUDA:
            x = x.cuda()
        with torch.no_grad():
            output = self.model(x)
        pred = output.data.detach().cpu().numpy()
        pred = np.argmax(pred, axis=1).squeeze(0)
        segmap = decode_segmap(pred, dataset='custom', label_colors=CUSTOM_COLOR_MAP, n_classes=CUSTOM_N_CLASSES)
        segmap = np.array(segmap * 255).astype(np.uint8)

        resized = cv2.resize(segmap, (ORIGINAL_WIDTH, ORIGINAL_HEIGHT),
                             interpolation=cv2.INTER_NEAREST)
        return resized

def main():
    try:
        server_sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        host ='192.168.1.83'
        port=10035
        server_sock.bind((host, port))
        server_sock.listen(100)
        print("wait....")
        client_socket, addr = server_sock.accept()
        print('Connected by',addr)
        print('Loading model...')

        data=client_socket.recv(1024)
        print(data.decode("utf-8"), len(data))
        data=client_socket.recv(1024)
        model_wrapper = ModelWrapper()
        camera=jetson.utils.gstCamera(640,480,"csi://0")
        chk=0
        sok=0
        while True:
            img, width, height = camera.CaptureRGBA(zeroCopy=1)
            jetson.utils.cudaDeviceSynchronize()
            jetson.utils.saveImageRGBA('/home/vision/Desktop/segmentation-selectstar-master/input/jpgs/image.jpg',img,width,height)

            if MODE == 'mp4':
                generator = FrameGeneratorMP4(DATA_PATH, OUTPUT_PATH, show=SHOW_OUTPUT)
            elif MODE == 'jpg':
                generator = FrameGeneratorJpg(DATA_PATH, OUTPUT_PATH, show=SHOW_OUTPUT)
            else:
                raise NotImplementedError('MODE should be "mp4" or "jpg".')

            for index, img in enumerate(tqdm(generator)):
                segmap = model_wrapper.predict(img)
                if OVERLAPPING:
                    h, w, _ = np.array(segmap).shape
                    img_resized = cv2.resize(img, (w, h))
                    result = (segmap).astype(np.uint8)
                else:
                    result = segmap
                generator.write(result)

            generator.close()
            image=Image.open('/home/vision/Desktop/segmentation-selectstar-master/output/jpgs/image.jpg')#'./input/jpgs/input.jpg')
            pixel=np.array(image)
            sum=0
            for i in range(int(pixel.shape[1]/3),int(pixel.shape[1]*2/3)):# width
                for j in range(int(pixel.shape[0]/3),int(pixel.shape[0]*2/3)):#height
                    sum=sum+pixel[j,i]
            avg=sum/(pixel.shape[1]*2/3-pixel.shape[1]/3)*(pixel.shape[0]*2/3-pixel.shape[0]/3)
            print(avg[0],avg[1],avg[2])
            if (avg[0]>100 and avg[1]<150 and avg[2]<150) or (pixel[150,150,0]>250 and pixel[150,150,1]<5 and pixel[150,150,2]<5):
                print('caution zone')
                sok=1
            elif (avg[0]<150 and avg[1]<150 and avg[2]>100) or (pixel[150,150,0]<5 and pixel[150,150,1]<5 and pixel[150,150,2]>250):
                print('roadway')
                sok=4
            elif (avg[0]>100 and avg[1]<150 and avg[2]>100) or (pixel[150,150,0]>250 and pixel[150,150,1]<5 and pixel[150,150,2]>250) :
                print('crosswalk')
                sok=2
            elif (avg[0]>100 and avg[1]>100 and avg[2]<150) or (pixel[150,150,0]>250 and pixel[150,150,1]>250 and pixel[150,150,2]<5):
                print('guide_block')
                sok=3
            else:
                print('nothing')
                sok=0
            if sok!=chk and sok!=0:
                client_socket.send(data)
                client_socket.send(sok.to_bytes(4, byteorder='little'))
                chk=sok
            print('Done.')
        

    except KeyboardInterrupt:
        print('finish')
        client_socket.close()
        server_sock.close()
#        subprocess.call(["shutdown", "-h", "now"]) #shudown jetson nano
if __name__ == '__main__':

    main()
'''
try:
    
    host ='192.168.1.83'
    port=10032
    server_sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    server_sock.bind((host, port))
    server_sock.listen(100)
    print("wait....")
    client_socket, addr = server_sock.accept()
    print('Connected by',addr)
    data=client_socket.recv(1024)
    print(data.decode("utf-8"), len(data))

    data=client_socket.recv(1024)
    print(data.decode("utf-8"), len(data))

    t1=threading.Thread(target=th1, args=())
#    t2=threading.Thread(target=th2, args=())
    t1.start()
#    t2.start()

except KeyboardInterrupt:
    client_socket.close()
    server_sock.close()
    print('finish program')
    sys.exit()
    os.system('systemctl poweroff')
#    print('finish')
#    finish()
'''





