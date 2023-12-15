from pathlib import Path
import cv2
import csv

def loadVideo(video_path):
    if Path(video_path).is_file():
        # print(Path(video_path).stem)
        video = cv2.VideoCapture(video_path)
    else: 
        print("input khong ton tai")
        exit()
    return video

def handle_left_click(event, x, y, flags, points):
    if event == cv2.EVENT_LBUTTONDOWN and len(points)<=3:
        points.append([x, y])
    if event == cv2.EVENT_MOUSEMOVE :  
        XY = [x, y]
        print(XY)

def moumove(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE :  
        XY = [x, y]
        print(XY)

def get_1_frame(video_path):
    f = loadVideo(video_path)
    r, f = f.read()
    return f

def is_file(path):
    if Path(path).is_file():
        return True
    return False

def draw_lines_2_frame(frame, points):
    for point in points:
        frame = cv2.circle(frame, (point[0], point[1]), 5, (0,0,255), -1)
    if len(points) == 4:
        pointA, pointB, pointC, pointD = points
        #line 1
        cv2.putText(frame, "Line 1", (pointA[0], pointA[1]-5), cv2.FONT_HERSHEY_PLAIN, 1.2, (0,0,255),2)
        cv2.line(frame, (pointA[0], pointA[1]), (pointB[0], pointB[1]), (100, 100, 255), 2)
        #line 1
        cv2.putText(frame, "Line 2", (pointC[0], pointC[1]-5), cv2.FONT_HERSHEY_PLAIN, 1.2, (0,0,255),2)
        cv2.line(frame, (pointC[0], pointC[1]), (pointD[0], pointD[1]), (14, 200, 255), 2)
    return frame

def add_pointlist2csvfile(points, video_path, savepath):
    import csv
    csv_filename = Path(video_path).stem
    with open('D:/LuanVan/Videos/csv/' + csv_filename + '.csv', 'w', newline='') as file:
        writerObj = csv.writer(file)
        writerObj.writerows(points)

def load_fromcsv(csv_path):
    if Path(csv_path).exists():
        list_point = []
        with open(csv_path, 'r') as file:
            readerObj = csv.reader(file)
            for row in readerObj:
                list_point.append(row)
        for i in range(0, len(list_point)):
            for j in range(0, 2):
                list_point[i][j] = int(list_point[i][j])
        return list_point
    return False

def add_new_2lines(video_path, save_path):
    points = []
    video = loadVideo(video_path)
    _, frame = video.read()
    outframe = frame
    while True:
        ret, frame = video.read()
        frame = cv2.resize(frame, (854,480))
        # frame = cv2.resize(frame, (854, 480), interpolation = cv2.INTER_LINEAR)
        frame = draw_lines_2_frame(frame, points)
        print(points)
        if ret:
            cv2.rectangle(frame, (0, 0), (285, 40), (150,0,0), -1)
            cv2.putText(frame, "Add 2 lines", (1,15), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255),2)
            cv2.putText(frame, "[s] Save [r] Redraw [q] Quit", (1, 35), cv2.FONT_HERSHEY_PLAIN, 1.2, (0,0,255),2)
            cv2.imshow("FRAME", frame)
        else:
            print('no video')
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        # cv2.setMouseCallback('FRAME', moumove)
        cv2.setMouseCallback('FRAME', handle_left_click, points)
        key = cv2.waitKey(0)
        if key == ord('r'): #chon lai
            points = []
        if key == ord('s'): #chon
            csv_filename = Path(video_path).stem
            save_path = save_path + csv_filename + '_lines.csv'
            print(save_path)
            save_point = []
            with open(save_path, 'w', newline='') as file:
                writerObj = csv.writer(file)
                writerObj.writerows(points)
                print(save_path)
            break
        if key == ord('q'): # thoat
            break
    video.release()
    cv2.destroyAllWindows()

import pandas
import numpy
def result_tolistboxes(result,pretrain):
    boxes = []
    for _, row in result.pandas().xyxy[0].iterrows():
        x1 = int(row['xmin'])
        y1 = int(row['ymin'])
        x2 = int(row['xmax'])
        y2 = int(row['ymax'])
        conf = round(float(row["confidence"]), 2)
        cls = row['class']
        name = row['name']
        if pretrain:
            if row['class'] == 2 or row['class'] == 3 or row['class'] == 5 or row['class'] == 7:
                boxes.append([x1, y1, x2, y2, conf, cls, name])
        else: boxes.append([x1, y1, x2, y2, conf, cls, name])
    return boxes

def roi_click(event, x, y, flags, points):
    if event == cv2.EVENT_LBUTTONDOWN and len(points)<=10:
        points.append([x, y])

def add_new_roi(video_path, csv_fpath):
    points = []
    video = loadVideo(video_path)

    while True:
        ret, frame = video.read()
        frame = cv2.resize(frame, (854,480))
        # frame = cv2.resize(frame, (854, 480), interpolation = cv2.INTER_LINEAR)
        # print(points)
        for point in points:
            frame = cv2.circle(frame, (point[0], point[1]), 5, (0,0,255), -1)
        if ret:
            cv2.rectangle(frame, (0, 0), (285, 40), (150,0,0), -1)
            cv2.putText(frame, "Add roi", (1,15), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255),2)
            cv2.putText(frame, "[s] Save [r] Redraw [q] Quit", (1, 35), cv2.FONT_HERSHEY_PLAIN, 1.2, (0,0,255),2)
            cv2.imshow("FRAME", frame)
        else:
            print('no video')
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        cv2.setMouseCallback('FRAME', roi_click, points)
        key = cv2.waitKey(0)
        if key == ord('r'): #chon lai
            points = []
        if key == ord('s'): #chon
            # luu 4 toa
            print(points)
            with open(csv_fpath + Path(video_path).stem + '_roi.csv', 'w', newline='') as file:
                writerObj = csv.writer(file)
                writerObj.writerows(points)
            break
        if key == ord('q'): 
            break
    video.release()
    cv2.destroyAllWindows()

import numpy as np
def isInsideArea(cx, cy, area):
    if cv2.pointPolygonTest(np.array(area, np.int32), (cx, cy), False) >= 0:
        return True
    return False

import datetime
def frame_num_to_time(frame_num, fps_real):
    s = frame_num / fps_real
    # s = s % (24 * 3600)
    # h = s // 3600
    # m = s // 60
    # s %= 60
    # return "%d:%02d:%02d" % (h, m, s)
    return str(datetime.timedelta(seconds=s))

def get_trackID_inframe(output_tracks):
        trackid_inframe = []
        for sublist in output_tracks:
            trackid_inframe.append(int(sublist[4]))
        return trackid_inframe

def get_trackID_inroi(output_tracks, roi):
    trackid_inroi = []
    for t in output_tracks:
        x1, y1, x2, y2, id = t
        x1, y1, x2, y2, id = int(x1), int(y1), int(x2), int(y2), int(id)
        if isInsideArea((x1+x2)/2, (y1+y2)/2, roi):
            trackid_inroi.append(int(t[4]))
    return trackid_inroi

def birdeye_viewtransform(img):
    print('da xoa')

def line_count(img, roi):
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY)
    e = cv2.Canny(thresh, 200, 255)
    contour, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    i = 0
    for cnt in contour:
        approx = cv2.approxPolyDP(cnt, 0.05*cv2.arcLength(cnt, True), True)
        if len(approx)==4:
            x = approx.ravel()[0]
            y = approx.ravel()[1]
            # cv2.drawContours(img, [approx], -1, (255,0,0), 1)
            # cv2.putText(img, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255))
            
            if cv2.pointPolygonTest(np.array(roi, np.int32), (float(x), float(y)), False) >= 0:
                cv2.drawContours(img, [approx], -1, (255,0,0), 1)
                cv2.putText(img, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255))
                i+=1
    return img, i

def new_csv(filepath, header):
    with open(filepath,'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

def write_new_line_csv(filepath, linetext):
    with open(filepath,'a',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(linetext)

def outROIisblack(img, roi):
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            if cv2.pointPolygonTest(np.array(roi, np.int32), (j, i), False) <= 0:
                img[i, j] = [0,0,0]
    return img