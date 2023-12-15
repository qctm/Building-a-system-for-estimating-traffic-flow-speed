import argparse
import os
import platform
import shutil
import time
from pathlib import Path
import cv2
import cvzone
import torch
import torch.backends.cudnn as cudnn
import numpy as np
from yolov5.models.experimental import attempt_load
from yolov5.utils.downloads import attempt_download
from yolov5.models.common import DetectMultiBackend
from yolov5.utils.dataloaders import LoadImages, LoadStreams
from yolov5.utils.general import (LOGGER, check_img_size, non_max_suppression, scale_coords, 
                                  check_imshow, xyxy2xywh, increment_path)
from yolov5.utils.torch_utils import select_device, time_sync
from yolov5.utils.plots import Annotator, colors
from DeepSort.deep_sort.utils.parser import get_config
from DeepSort.deep_sort.deep_sort import DeepSort

import sys
sys.path.insert(0, './UI_TEST')

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # yolov5 deepsort root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative


def yolov5_deepsort_tracking():
    opt = parse_opt()
    # - SET UP: DeepSORT
    cfg = get_config()
    cfg.merge_from_file(opt.config_deepsort)
    deepsort = DeepSort(opt.deep_sort_model,
                        max_dist=cfg.DEEPSORT.MAX_DIST,
                        max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                        max_age=cfg.DEEPSORT.MAX_AGE, n_init=cfg.DEEPSORT.N_INIT, nn_budget=cfg.DEEPSORT.NN_BUDGET,
                        )

    # - SET UP: YOLO    use_cuda=True
    # Load model
    device = select_device(opt.device)
    model = DetectMultiBackend(opt.yolo_model)
    stride, names, pt, jit, _ = model.stride, model.names, model.pt, model.jit, model.onnx

    imgsz = check_img_size(opt.imgsz, s=stride)
    
    # Dataloader
    bs = 1  # batch_size
    dataset = LoadImages(opt.source, img_size=imgsz, stride=stride, auto=pt and not jit)
    
    model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
    # time_run = [0.0, 0.0]
    for frame_idx, (path, img, im0s, vid_cap, s) in enumerate(dataset):
        img = torch.from_numpy(img).to(device)
        img = img.half() if opt.half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)
        # Inference
        t1 = time_sync()
        pred = model(img)
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, opt.classes, opt.agnostic_nms, max_det=opt.max_det)
        # time_run[0] = time_sync() - t1

        for i, det in enumerate(pred):  # detections per image
            p, im0 = path, im0s.copy()#, getattr(dataset, 'frame', 0)
            p = Path(p)  # to Path
            s += '%gx%g ' % img.shape[2:]  # print string
            w, h = im0.shape[1],im0.shape[0]
            if det is not None and len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string
                xywhs = xyxy2xywh(det[:, 0:4])
                confs = det[:, 4]
                clss = det[:, 5]

                t2 = time_sync()
                outputs = deepsort.update(xywhs.cpu(), confs.cpu(), clss.cpu(), im0)
                # time_run[1] = time_sync() - t2

                # print("YOLO: {:.3f}s --- DeepSORT: {:.3f}s".format(time_run[0], time_run[1]))
        
                for output in outputs:
                    x1, y1, x2, y2, track_id, class_id = output
                    cv2.rectangle(im0, (x1, y1), (x2, y2), (255,0,0),2)
                    cvzone.putTextRect(im0, f' {int(track_id)}', (max(0, x1),max(35,y1)), 
                                scale=1, thickness=1, offset=0)

        cv2.imshow(str(p), im0)
        if cv2.waitKey(1) == ord('q'):  # q to quit
            raise StopIteration

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deep_sort_model', type=str, default='osnet_x0_25') #osnet_x0_25
    parser.add_argument('--output', type=str, default='inference/output', help='output folder')  # output folder
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[480, 852], help='inference size h,w')
    parser.add_argument('--conf-thres', type=float, default=0.5, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.5, help='IOU threshold for NMS')
    parser.add_argument('--fourcc', type=str, default='mp4v', help='output video codec (verify ffmpeg support)')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--evaluate', action='store_true', help='augmented inference')
    parser.add_argument("--config_deepsort", type=str, default="E:\LuanVan\HTULTDLGT\DeepSort\deep_sort\configs\deep_sort.yaml")
    parser.add_argument("--half", action="store_true", help="use FP16 half-precision inference")
    parser.add_argument('--visualize', action='store_true', help='visualize features')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detection per image')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
    parser.add_argument('--project', default=ROOT / 'runs/track', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    return opt

class DeepSORT_Tracker():
    def __init__(self, roi):
        opt = parse_opt()
        cfg = get_config()
        cfg.merge_from_file(opt.config_deepsort)
        self.deepsort = DeepSort(opt.deep_sort_model,
                            max_dist=cfg.DEEPSORT.MAX_DIST,
                            max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                            max_age=cfg.DEEPSORT.MAX_AGE, n_init=cfg.DEEPSORT.N_INIT, nn_budget=cfg.DEEPSORT.NN_BUDGET,
                            )
        self.roi = roi
     
    def update_track(self, detect_results, frame):       
        r = detect_results.xyxy[0]
        xywhs = xyxy2xywh(r[:, 0:4])
        confs = r[:, 4]
        clss = r[:, 5]
        outputs = self.deepsort.update(xywhs.cpu(), confs.cpu(), clss.cpu(), frame)
        return outputs 
    
    