import msvcrt
import time
from datetime import datetime
import json
import argparse
from RepeatedTimer import RepeatedTimer
try:
	import requests
except ImportError as error:
	print(error.__class__.__name__+" : "+error.message)
except Exception as exception:
	print(exception, False)
	print(exception.__class__.__name__+" : "+exception.message)

app_version = "1.0"
app_name = "BLANK_OLED"
app_event = "OLED_OFF"
app_timer_interval = 50 #send keepalive every X sec max 60 sec
app_display_name = ""
device_type = "screened" #"screened" for all or invidually "screened-120x36", "screened-128x52"
corePropsPath = "c:/ProgramData/SteelSeries/SteelSeries Engine 3/coreProps.json" #path to file
sseAddress = json.load(open(corePropsPath))["address"]
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="verbose output timer.", action="store_true")
args = parser.parse_args()

def output_dt():
	dt = datetime.now()
	return dt.strftime("%Y/%m/%d %H:%M:%S")

def output2screen(print_output):
	print(output_dt()+" "+print_output)

def kbfunc():
	#this is boolean for whether the keyboard has bene hit
	x = msvcrt.kbhit()
	if x:
		#getch acquires the character encoded in binary ASCII
		ret = msvcrt.getch()
	else:
		ret = False
	return ret

def check_request_status(status_code):
	if status_code == 200:
		return "OK"
	else:
		return "ERROR"

def register_game():
	game_metadata = {
		"game": app_name,
		"game_display_name": app_display_name,
		"deinitialize_timer_length_ms": 60000
	}
	try:
		r = requests.post("http://"+sseAddress+"/game_metadata", json=game_metadata)
	except requests.exceptions.HTTPError as e:
		output2screen(e.response.text)
	finally:
		output2screen("Registering APP "+app_name+" v"+app_version+" : "+check_request_status(r.status_code))

def create_oled_blank_img(ncount):
	return ([0] * ncount)

def bind_event():
	screen_handler = {
		"game": app_name,
		"event": app_event,
		"value_optional": True,
		"handlers": [{
			"device-type": device_type,
			"mode": "screen",
			"zone": "one",
			"datas": [{
				"has-text": False,
				"image-data-128x36": create_oled_blank_img(576),
				"image-data-128x40": create_oled_blank_img(640),
				"image-data-128x48": create_oled_blank_img(768),
				"image-data-128x52": create_oled_blank_img(832)
				}
			]}
		]
	}
	try:
		r = requests.post("http://"+sseAddress+"/bind_game_event", json=screen_handler)
	except requests.exceptions.HTTPError as e:
		output2screen(e.response.text)
	finally:
		output2screen("Bind event "+app_event+" : "+check_request_status(r.status_code))

def send_event():
	event_data = {
		"game": app_name,
		"event": app_event,
		"data": {"has-text": False}
	}
	try:
		r = requests.post("http://"+sseAddress+"/game_event", json=event_data)
	except requests.exceptions.HTTPError as e:
		output2screen(e.response.text)
	finally:
		if args.verbose == True:
			output2screen("Sending keepalive event "+app_event+" : "+check_request_status(r.status_code))

def send_heartbeat():
	hb_data = {
		"game": app_name
	}
	try:
		r = requests.post("http://"+sseAddress+"/game_heartbeat", json=hb_data)
	except requests.exceptions.HTTPError as e:
		output2screen(e.response.text)
	finally:
		output2screen("Sending heartbeat: "+check_request_status(r.status_code))

def unbind_event():
	hb_data = {
		"game": app_name,
		"event": app_event
	}
	try:
		r = requests.post("http://"+sseAddress+"/remove_game_event", json=hb_data)
	except requests.exceptions.HTTPError as e:
		output2screen(e.response.text)
	finally:
		output2screen("Unbind event "+app_event+" : "+check_request_status(r.status_code))

def unregister_game():
	hb_data = {
		"game": app_name
	}
	try:
		r = requests.post("http://"+sseAddress+"/remove_game", json=hb_data)
	except requests.exceptions.HTTPError as e:
		output2screen(e.response.text)
	finally:
		output2screen("Unregister "+app_name+" : "+check_request_status(r.status_code))

def main():
	register_game()
	bind_event()
	output2screen("Starting "+app_name+" keepalive.")
	send_event()
	rt = RepeatedTimer(app_timer_interval, send_event)
	#app keyboard input infinite loop
	while True:
		#acquire the keyboard hit if exists
		x = kbfunc() 
		#if we got a keyboard hit
		if (x != False) and (x.decode(errors="ignore") == 'x' or x.decode(errors="ignore") == 'q'):
			output2screen("Stopping "+app_name+" keepalive.")
			rt.stop()
			unbind_event()
			unregister_game()
			break
		else:
			#wait a half second
			time.sleep(0.5)

if __name__ == "__main__":
	main()

