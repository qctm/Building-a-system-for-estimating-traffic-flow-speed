import os
import sys
import cv2
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtGui import *
from PyQt5.QtCore import QTimer, QDir
from uid import UID

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import imutils
import time
from DeepSort.track_deepsort import *
from Sort.track_sort import *
from speed_calculator import *
from suport import *

global app
global start

class MainWindow(QWidget):
    # class constructor
    def __init__(self):
        self.videopath = "E:/LuanVan/HTULTDLGT/Videos/thucnghiem_3.mp4"
        self.area_speedcal = None 
        super().__init__()
        self.baseUI = UID()

        self.baseUI.setupUi(self)
        self.timer = QTimer()
        self.timer_2 = QTimer()

        self.timer.timeout.connect(self.run)
        self.timer_2.timeout.connect(self.preview)
        self.baseUI.START.clicked.connect(self.start_bt)
        self.baseUI.PAUSE.clicked.connect(self.pause)
        self.baseUI.RESUME.clicked.connect(self.resume)
        self.baseUI.STOP.clicked.connect(self.stop)
        self.baseUI.GETFILE.clicked.connect(self.getvideofile)
        self.baseUI.preview_video.clicked.connect(self.preview_button)
        self.baseUI.SO_add_lines_btn.clicked.connect(self.add2lines)
        self.baseUI.SO_add_roi_btn.clicked.connect(self.addroi)
        self.baseUI.GF_le.setText(self.videopath)
        self.baseUI.speedCal_dis_le.setText("10")
        # self.baseUI.ovb_b1.toggled.connect(self)
        self.family_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.FPS = None
        self.isSaveVideo = False
        pixmap = QPixmap('E:/LuanVan/HTULTDLGT/IMG/no-video.jpg')
        self.baseUI.imgLabel_1.setPixmap(pixmap)
        self.setWindowIcon(QIcon('logo.png'))
    
    def pause(self):
        self.timer.stop()

    def resume(self):
        if self.logic:
            self.timer.start(30)
        else:
            print('>0')

    def stop(self):
        self.timer.stop()
        self.detector = None
        self.speed_calculator = None
        self.baseUI.PAUSE.setEnabled(False)
        self.baseUI.RESUME.setEnabled(False)
        self.tracker = None
        self.speed_calculator = None
        if self.isSaveVideo:
            print('Da luu video ket qua')
            self.video_writer.release()
            self.video_writer = None
        
    def start_bt(self):
        self.video_writer = cv2.VideoWriter(self.family_directory +'\\Videos\\result_video\\' + Path(self.videopath).stem + '_result.avi', cv2.VideoWriter_fourcc(*'MJPG'), 30, (854,480))
        print('Khoi tao video writer')
        # if timer is stopped
        if not self.timer.isActive():
            self.cap = loadVideo(self.videopath)
            self.FPS = round(self.cap.get(cv2.CAP_PROP_FPS))
            self.total_frame = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.f_no = 1
            self.timer.start(self.FPS)
            self.logic = True
        else:
            self.timer.stop()
            self.cap.release()

        csv_fp = self.family_directory +'\\Videos\\csv\\'
        self.lines = load_fromcsv(csv_fp + Path(self.videopath).stem + '_lines.csv')
        self.roi = load_fromcsv(csv_fp + Path(self.videopath).stem + '_roi.csv')
        
        self.yolomodel = torch.hub.load('ultralytics/yolov5', 'custom', self.family_directory + '/Model_Yolov5/100e.pt')
        self.yolomodel.conf = 0.1
        self.names = self.yolomodel.names
        self.tracker = DeepSORT_Tracker(self.roi)
        m = self.baseUI.speedCal_dis_le.text() # khoang cach giua 2 lines tinh theo met (gia dinh)
        # cachtinh = self.baseUI.SO_useOpt_box.currentIndex() # 0: 2:Lines    1: ROI
        self.speed_calculator = SpeedCalculator(int(m), self.lines, csv_fp + Path(self.videopath).stem + '_log.csv', self.FPS)

        self.baseUI.PAUSE.setEnabled(True)
        self.baseUI.RESUME.setEnabled(True)
        self.baseUI.STOP.setEnabled(True)
        if self.timer_2.isActive():
            self.timer_2.stop()
        

    def run(self):
        global start
        colorR = (0,0,255)
        colorB = (255,0,0)
        offset = 10

        ret, frame = self.cap.read()
        if not ret:
            self.stop()
            return False
        frame = cv2.resize(frame, (854,480))
        detect_results = self.yolomodel(frame)
        results = self.tracker.update_track(detect_results, frame)

        list_v_inroi = []
        # tinh van toc
        for result in results:
            x1, y1, x2, y2, id , class_id= result
            x1, y1, x2, y2, id = int(x1), int(y1), int(x2), int(y2), int(id)
            w, h = x2 -x1, y2-y1
            cx = (x1+x2)//2
            cy = y2
            if isInsideArea((x1+x2)/2, (y1+y2)/2, self.roi):
                list_v_inroi.append(id)
                if cy < (self.lines[0][1] + offset) and cy > (self.lines[0][1] - offset):
                    self.speed_calculator.add_SFrame(id, cx, cy, self.f_no)
                if cy < (self.lines[2][1] + offset) and cy > (self.lines[2][1] - offset):
                    self.speed_calculator.add_EFrame(id, cx, cy, self.f_no)
                if cy > (self.lines[2][1] + offset):
                    self.speed_calculator.update(id, class_id)
                if id in self.speed_calculator.speeds:
                    cvzone.putTextRect(frame, f' {int(self.speed_calculator.speeds[id])} Km/h', (max(0, x1),max(35,y1)), 
                                        scale=2, thickness=2, offset=0)
                else: cvzone.putTextRect(frame, f' {int(id)}_{str(self.names[class_id])}', (max(0, x1),max(35,y1)), 
                                        scale=1, thickness=1,offset=0)
                cv2.circle(frame, (cx, cy), 2, (255,0,0),2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), colorB, 1)

        self.speed_calculator.update_current_speed(list_v_inroi)

        # cv2.putText(frame, f'{str(self.f_no)} / {str(self.total_frame)}', (50, 90), cv2.FONT_HERSHEY_PLAIN, 3, colorR,3)
        cv2.line(frame, (self.lines[0][0], self.lines[0][1]), (self.lines[1][0], self.lines[1][1]), colorR, 2)
        cv2.line(frame, (self.lines[2][0], self.lines[2][1]), (self.lines[3][0], self.lines[3][1]), colorR, 2)
        # cv2.polylines(frame, [np.array(self.roi, np.int32)], True, colorB, 2)
        self.baseUI.speed_avg_lable1.setText(str(self.speed_calculator.avg_speed)+" Km/h")
        self.baseUI.speed_current_lable1.setText(str(self.speed_calculator.cur_avg_speed)+" Km/h")
        sf = frame.copy()
        cv2.rectangle(sf, (0, 0), (200, 100), (150,0,0), -1)
        cv2.putText(sf, f'Frame: {str(self.f_no)} / {str(self.total_frame)}', (10, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255),2)
        cv2.putText(sf, f'VTTB: {str(self.speed_calculator.avg_speed)} Km/h', (10, 45), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255),2)
        cv2.putText(sf, f'VTTBTT: {str(self.speed_calculator.cur_avg_speed)} Km/h', (10, 70), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255),2)
        cv2.putText(sf, self.speed_calculator.last, (10, 95), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255),2)
        
        self.video_writer.write(sf)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        step = channel * width
        qImg = QImage(frame.data, width, height, step, QImage.Format_RGB888)
        self.baseUI.imgLabel_1.setPixmap(QPixmap.fromImage(qImg))
        self.baseUI.framerun.setText(f'{str(self.f_no)}/{str(self.total_frame)}')
        self.f_no+=1
       
    def getvideofile(self):
        filter_name = 'mp4 (*.mp4*)'
        dirpath = QDir.currentPath() + "/HTULTDLGT/Videos"
        filepath = QFileDialog.getOpenFileName(self, caption='Choose Video File',
                                                    directory=dirpath,
                                                    filter=filter_name)
        print(filepath[0])
        self.baseUI.GF_le.setText(str(filepath[0]))
        self.videopath = str(filepath[0])
        self.video = 0 if self.videopath == None else self.videopath
        # self.preview()

    def preview_button(self):
        if not self.timer_2.isActive():
            print('Xem truoc video')
            self.cap = loadVideo(self.videopath)
            self.timer_2.start(30)
            self.logic = True
        else:
            self.timer_2.stop()
            self.cap.release()

    def preview(self):
        ret, frame = self.cap.read()
        if not ret:
            self.timer_2.stop()
            return False
        frame = cv2.resize(frame, (854,480))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        step = channel * width
        qImg = QImage(frame.data, width, height, step, QImage.Format_RGB888)
        self.baseUI.imgLabel_1.setPixmap(QPixmap.fromImage(qImg))
    
    def add2lines(self):
        print("Ve 2 doan thang len frame")
        save_path = './HTULTDLGT/Videos/csv/'
        add_new_2lines(self.videopath, save_path)
    
    def addroi(self):
        print("Them roi")
        csv_fpath = self.family_directory +'\\Videos\\csv\\'
        add_new_roi(self.videopath, csv_fpath)


def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
        
if __name__ == "__main__":
    main()    