#!/usr/bin/python3
import jetson.inference
import jetson.utils
import argparse
import sys

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import RPi.GPIO as gpio
import time
import warnings

import socket
warnings.filterwarnings('ignore')


COLLISION = 18
TRIGER = 24
ECHO = 23
classlabel = 0
temlabel = 0
repeat_count = 0    #thread 
distance = 0
count = 0
move_list = list(range(14))
fixed_list = list(range(14,28))
email_arv = 'NULL'
gpio.setmode(gpio.BCM)
#global email_send='lord4255@naver.com'
# GPIO
gpio.setup(TRIGER, gpio.OUT)
gpio.setup(ECHO, gpio.IN)

def Ultra_detect():
    try:
        gpio.output(TRIGER, gpio.LOW)
        time.sleep(0.5)
        gpio.output(TRIGER, gpio.HIGH)
        time.sleep(0.00001)
        gpio.output(TRIGER, gpio.LOW)

 
        while gpio.input(ECHO) == 0 :
            pulse_start = time.time()
            if gpio.input(ECHO) != 1:
                gpio.setup(ECHO, gpio.OUT)
                gpio.output(ECHO, gpio.LOW)
                gpio.setup(ECHO, gpio.IN)
                pulse_start = time.time()
                break

        while gpio.input(ECHO) == 1 :
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17000
        distance = round(distance, 2)
        print ("Distance : ", distance, "cm")
        time.sleep(0.01)
        return distance

    except UnboundLocalError as error:
        print(error)


def Collision(email_arv):
    global count
    gpio.setup(COLLISION, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    col_count = gpio.input(COLLISION)
    result = col_count
    if  result == 1:
        print("진동이 감지 되었습니다")
        print(count)
        count += result
        time.sleep(0.05)
        if count == 8:
            print("Alert")
            jetson.utils.saveImageRGBA('/home/vision/jetson-inference/python/training/detection/ssd/emergency.jpg',img,width,height)
            Emergency_email(email_arv)
            count = 0

    else:
        if count <= 0:
            count = 0
        else:
            count -= 1
        #time.sleep(0.05)
    return count



def Emergency_email(email_arv):

    if email_arv is 'NULL':
        return 0
    print(email_arv)
    email_user = 'lord4255@gmail.com'      #<ID> 본인 계정 아이디 입력
    email_password = 'tkfkd45^^'      #<PASSWORD> 본인 계정 암호 입력
    email_send = email_arv         # <받는곳주소> 수신자 이메일

    # 제목 입력
    subject = 'Emergency Message ' 
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_send
    msg['Subject'] = subject

    # 본문 내용 입력
    body = 'An emergency has occurred for the user'
    msg.attach(MIMEText(body,'plain'))

    # 첨부파일 경로/이름 지정하기
    filename='/home/vision/jetson-inference/python/training/detection/ssd/emergency.jpg'
    attachment  =open(filename,'rb')

    part = MIMEBase('application','octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',"attachment", filename= filename)
    msg.attach(part)

    text = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(email_user,email_password)
    server.sendmail(email_user,email_send,text)



# parse the command line
parser = argparse.ArgumentParser(description="Locate objects in a live camera stream using an object detection DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.detectNet.Usage() +
                                 jetson.utils.videoSource.Usage() + jetson.utils.videoOutput.Usage() + jetson.utils.logUsage())

parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="ssd-mobilenet-v2", help="pre-trained model to load (see below for options)")
parser.add_argument("--overlay", type=str, default="box,labels,conf", help="detection overlay flags (e.g. --overlay=box,labels,conf)\nvalid combinations are:  'box', 'labels', 'conf', 'none'")
parser.add_argument("--threshold", type=float, default=0.7, help="minimum detection threshold to use") 

is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

try:
	opt = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)

# load the object detection network
net = jetson.inference.detectNet(opt.network, sys.argv, opt.threshold)
camera = jetson.utils.gstCamera(640,480,"csi://0") # 1280/720
display = jetson.utils.glDisplay()

# create video sources & outputs
#input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)
#output = jetson.utils.videoOutput(opt.output_URI, argv=sys.argv+is_headless)

# socket
host = '192.168.1.24'
port = 10019
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_sock.bind((host, port))
server_sock.listen(1)

print("wait....")
client_socket, addr = server_sock.accept()

print('Connected by',addr)
data = client_socket.recv(1024)
print(data.decode("utf-8"), len(data))


def thr2(sock):
    recv_data = sock.recv(1024)
    if not recv_data :
         return 0
    if len(recv_data)==8:
        client_socket.close()
        gpio.cleanup()
        server.quit() # gamil server quit
        server_sock.close()
        sys.exit()
    elif len(recv_data)>10:
        print(recv_data.decode("utf-8"))
        recv_utf = recv_data.decode("utf-8").split()
        recv_utf = str(recv_utf).split('4')
        recv_utf = recv_utf[1].split("'")
        print("email=",recv_utf[0])
        return recv_utf[0]

email_arv = thr2(client_socket)
try:
	p=0
	label=0
	while True:
		# capture the next image
		#img = input.Capture()
		img, width, height = camera.CaptureRGBA(zeroCopy=1)
		jetson.utils.cudaDeviceSynchronize()
	# detect objects in the image (with overlay)
		detections = net.Detect(img, width, height, overlay=opt.overlay)
		#detections = net.Detect(img, width, height)

	# print the detections
#		print("detected {:d} objects in image".format(len(detections)))
#		for detection in detections:
#			print(detections[0].ClassID)
#			classlabel = detections[0].ClassID
		if p!=len(detections):#and distance<400
			for i in range(len(detections)):
				if detections[i].ClassID==9:#person
					label=detections[i].ClassID
					break;
				elif detections[i].ClassID==3 and label!=9:#car
					label=detections[i].ClassID
				elif detections[i].ClassID==2 and label!=9 and label!=3:#bus
					label=detections[i].ClassID
				elif detections[i].ClassID==5 and label!=9 and label!=3 and label!=2:#cat
					label=detections[i].ClassID
				elif detections[i].ClassID==6 and label!=9 and label!=3 and label!=2 and label!=5:#dog
					label=detections[i].ClassID
				elif detections[i].ClassID==1 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6:#bicycle
					label=detections[i].ClassID
				elif detections[i].ClassID==10 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1:#scooter
					label=detections[i].ClassID
				elif detections[i].ClassID==11 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10:#truck
					label=detections[i].ClassID
				elif detections[i].ClassID==12 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11:#wheelchair
					label=detections[i].ClassID
				elif detections[i].ClassID==4 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12:#carrier
					label=detections[i].ClassID
				elif detections[i].ClassID==7 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12 and label!=4:#motorcycle
					label=detections[i].ClassID
				elif detections[i].ClassID==8 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7:#movable_signage
					label=detections[i].ClassID
				elif detections[i].ClassID==26 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8:#tree_trunk
					label=detections[i].ClassID
				elif detections[i].ClassID==15 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26:#bollard
					label=detections[i].ClassID
				elif detections[i].ClassID==13 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15:#barricade
					label=detections[i].ClassID
				elif detections[i].ClassID==14 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15 and label!=13:#bench
					label=detections[i].ClassID
				elif detections[i].ClassID==16 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15 and label!=13 and label!=14:#chair
					label=detections[i].ClassID
				elif detections[i].ClassID==17 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15 and label!=13 and label!=14 and label!=16:#fire_hy
					label=detections[i].ClassID
				elif detections[i].ClassID==20 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15 and label!=13 and label!=14 and label!=16 and label!=17:#pole
					label=detections[i].ClassID
				elif detections[i].ClassID==21 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15 and label!=13 and label!=14 and label!=16 and label!=17 and label!=20:#potted_plant
					label=detections[i].ClassID
				elif detections[i].ClassID==22 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15 and label!=13 and label!=14 and label!=16 and label!=17 and label!=20 and label!=21:#stop
					label=detections[i].ClassID
				elif detections[i].ClassID==15 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15 and label!=13 and label!=14 and label!=16 and label!=17 and label!=20 and label!=21 and label!=22:#table
					label=detections[i].ClassID
				elif detections[i].ClassID==24 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15 and label!=13 and label!=14 and label!=16 and label!=17 and label!=20 and label!=21 and label!=22 and label!=23:
					label=detections[i].ClassID
				elif detections[i].ClassID==25 and label!=9 and label!=3 and label!=2 and label!=5 and label!=6 and label!=1 and label!=10 and label!=11 and label!=12  and label!=4 and label!=7 and label!=8 and label!=26 and label!=15 and label!=13 and label!=14 and label!=16 and label!=17 and label!=20 and label!=21 and label!=22 and label!=23 and label!=24:
					label=detections[i].ClassID

			
			Collision(email_arv)
			distance = Ultra_detect()

			if distance is None:
				distance=400
			if p!=len(detections) and distance < 250:
				print(label)
				client_socket.send(data)
				client_socket.send(label.to_bytes(4, byteorder='little'))
				p=len(detections)
			if distance<50:
				warn=99
				client_socket.send(data)
				client_socket.send(warn.to_bytes(4, byteorder='little'))
			#Collision(email.arv)
			
#		if repeat_count < 30:
#			Collision(email_arv)		# collision detect 
#		else :
#			if repeat_count % 15 == 0 :
#				distance = Ultra_detect()
#				if not distance :
#					distance = 0	# ultra detect
#			if temlabel != classlabel and 0 < distance and distance < 100 :
#				data2 = classlabel
#				client_socket.send(data)
#				print('send', data2)
#				client_socket.send(data2.to_bytes(4, byteorder='little'))
#				temlabel = classlabel
#				repeat_count = 0

	# render the image
		#output.Render(img)
		display.RenderOnce(img, width, height)

	# update the title bar
		#output.SetStatus("{:s} | Network {:.0f} FPS".format(opt.network, net.GetNetworkFPS()))
		display.SetTitle("{:s} | Network {:.0f} FPS".format(opt.network, net.GetNetworkFPS()))
		repeat_count += 1

except KeyboardInterrupt:
        client_socket.close()
        gpio.cleanup()
        server.quit() # gamil server quit
        server_sock.close()
        sys.exit()

	 	#print out performance info
		#net.PrintProfilerTimes()

	# exit on input/output EOS
		#if not input.IsStreaming() or not output.IsStreaming():
		#	break



