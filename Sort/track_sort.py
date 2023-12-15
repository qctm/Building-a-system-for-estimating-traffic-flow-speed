import torch
import cv2
# from ultralytics import YOLO
import cvzone
from Sort.sort import *
import numpy as np
from suport import *
from speed_calculator import *
import time

class SORT_Tracker():
    def __init__(self):
        self.yolomodel = torch.hub.load('ultralytics/yolov5', 'custom', 'E:/LuanVan/HTULTDLGT/best.pt')
        self.yolomodel.eval()
        self.tracker = Sort(max_age=20, min_hits=2, iou_threshold=0.3)

    def update_track(self, frame):
        results = self.yolomodel(frame)
        boxes = result_tolistboxes(results, 0)
        detections = np.empty((0, 5))

        for box in boxes:
            x1, y1, x2, y2, conf, cls, name = box
            if conf > 0.3:
                currentArray = np.array([x1, y1, x2, y2, conf])
                detections = np.vstack((detections, currentArray))
        
        resultsTracker = self.tracker.update(detections)

        return resultsTracker
    
        '''for result in resultsTracker:
            x1, y1, x2, y2, id = result
            x1, y1, x2, y2, id = int(x1), int(y1), int(x2), int(y2), int(id)
            w, h = x2 -x1, y2-y1
            cx = (x1+x2)//2
            cy = (y1+y2)//2
            cv2.circle(frame, (cx, cy), 2, (255,0,0),2)
            cvzone.cornerRect(frame, (x1, y1, w, h), l=0, rt=2, colorR=(255,0,0))
            cvzone.putTextRect(frame, f' {int(id)}', (max(0, x1),max(35,y1)), 
                                    scale=1, thickness=1, offset=0)

        # cv2.putText(frame, 'FPS: ' + str(round(vfps)), (50, 90), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255),3)
        # cv2.putText(frame, 'AVG SPEED: ' + str(round(speed.avg_speed, 2)) + "Km/h", (50, 150), cv2.FONT_HERSHEY_PLAIN, 3, colorR,3)
        # cv2.imshow('FRAME', frame)
        
        return frame'''