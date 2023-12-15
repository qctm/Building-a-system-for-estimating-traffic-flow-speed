import math
import statistics
from suport import new_csv, write_new_line_csv

class SpeedCalculator:
    def __init__(self, m, lines, log_file_path, fps):
        print(f'Khoi tao SC, m={str(m)}, fps = {str(fps)}')
        self.vehicles = {}
        self.speeds = {}
        self.metre = m
        self.yline1, self.yline2 = lines[0][1], lines[2][1]   # tọa độ y của 2 đoạn thẳng
        self.fps_soucre = fps    #defaut
        self.avg_speed = '--'

        # Cho van toc tuc thoi
        # self.trackID_inroi_list = [] # danh sach track_Id trong frame - cập nhật qua mỗi frame
        self.cur_speed = {}
        self.cur_avg_speed = '--'
        self.lfp = log_file_path
        new_csv(self.lfp, ['ID', 'Class', 'SFrame', 'EFrame','ySF', 'yEF', 'SP'])
        self.last = 'VID -: -- km/h '

    def add_SFrame(self, id, cx, cy, frame_no):
        coord = [cx, cy, frame_no, None, None, None]
        if id in self.vehicles:
            if cy == self.vehicles[id][1]:
                self.vehicles[id] = coord
                return 0
            # so sanh
            f1 = self.yline1 - self.vehicles[id][1]
            f2 = self.yline1 - cy
            if abs(f2) < abs(f1):
                self.vehicles[id] = coord
                # print(f'[110]Cap nhat FFrame: ID Phuong tien: {str(id)} --- CY1: {str(cy)} --- FFRAME: {str(frame_no)}')
                return 0
        else:
            self.vehicles[id] = coord
            # print(f'[100]Them FFrame: ID Phuong tien: {str(id)} --- CY1: {str(cy)} --- FFRAME: {str(frame_no)}')

    def add_EFrame(self, id, cx, cy, frame_no):
        if id in self.vehicles:
            coord = [self.vehicles[id][0], self.vehicles[id][1], self.vehicles[id][2], cx, cy, frame_no]
            if None not in self.vehicles[id]:
                # so sanh
                f1 = self.yline2 - self.vehicles[id][4]
                f2 = self.yline2 - cy
                if abs(f2) < abs(f1):
                    self.vehicles[id] = coord
                    # print(f'[210]Cap nhat EFrame: ID Phuong tien: {str(id)} --- CY2: {str(cy)} --- EFRAME: {str(frame_no)}')
            else:
                self.vehicles[id] = coord
                # print(f'[200]Them EFrame: ID Phuong tien: {str(id)} --- CY2: {str(cy)} --- EFRAME: {str(frame_no)}')

    def update(self, id, class_id):
        if self.isReady(id):      
            cx1, cy1, sframe, cx2, cy2, eframe = self.vehicles[id]
            # print(str(id) +"--"+ str(self.vehicles[id]))
            # === Tính vận tốc
            delta_frame = eframe - sframe 
            time_s = delta_frame / self.fps_soucre           

            v = self.metre / time_s # => metre per second

            # === Quy doi sang km / h
            v = round(v*3.6, 2)
            # print(f'delta_frame: {str(delta_frame)} -- dis: {str(dis)} -- fpss: {str(self.fps_soucre)} -- cachtinh: {str(self.cachtinh)}')
            
            # VT toan thoi gian
            self.speeds[id] = v
            self.cur_speed[id] = v
            self.cur_avg_speed = round(statistics.mean(self.cur_speed.values()), 1)
            self.avg_speed = round(statistics.mean(self.speeds.values()), 1)
            self.vehicles.pop(id)
            print("Vehicle ID: %3d --- speed: %2.1f km/h" %(id, self.speeds[id]))
            self.last = 'VID '+str(id) + ': ' +str(self.speeds[id])+' Km/h'
            write_new_line_csv(self.lfp, [str(id), str(class_id), str(sframe), str(eframe), str(cy1), str(cy2), str(v)])
            return True
        return False
    
    def update_current_speed(self, list_v_inroi):

        '''# Kiem tra speed khong rong:
        if not self.speeds: 
            return False
        # Kiem tra trackid da tinh van toc con trong frame?
        set1 = set(list(self.cur_speed.keys()))     # DS trackID đang trong DS cur_speed
        set2 = set(self.trackID_inframe_list)       # danh sách trackID hiện có trong frame
        trackID_notinframe = set1.difference(set2)
               
        for trackID in trackID_notinframe:
            self.cur_speed.pop(trackID)
 
        self.cur_avg_speed = round(statistics.mean(self.cur_speed.values())) if self.cur_speed else '--'
        print(self.cur_speed)'''

        if len(list_v_inroi) == 0:
            self.cur_avg_speed = '--'
            self.cur_speed = dict()

    
    def check_frame_is_no_track(self):
        if not self.trackID_inframe_list:
            self.cur_avg_speed = '--'

    def isReady(self, id):
        if id not in self.speeds.keys() and id in self.vehicles.keys():
            if None not in self.vehicles[id]:
                return True
        return False
        