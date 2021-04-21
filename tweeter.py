import twitter
import RPi.GPIO as GPIO
import time
import subprocess
import logging
import Queue
import threading
from datetime import datetime
import os

callback_q = Queue.Queue(maxsize=2)

#init logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('/home/pi/twitter/poop.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

print GPIO.VERSION

GPIO.setmode(GPIO.BCM)
#GPIO.setmode(GPIO.BOARD)
GPIO.cleanup()
GPIO.setwarnings(False)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
print "Lights Camera Action!"
GPIO.output(23, GPIO.HIGH)
GPIO.output(17, GPIO.HIGH)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')

ACCESS_TOKEN_KEY = os.environ.get('ACCESS_TOKEN_KEY')
ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET')

SNAP_NAME = "snap.jpg"

count = 0

api = None

TWITTER_HANDLE_PRIMARY = os.environ.get('TWITTER_HANDLE_PRIMARY')
TWITTER_HANDLE_SECOND = os.environ.get('TWITTER_HANDLE_SECONDARY')

def init_twitter():
    global api
    logger.info("Init Twitter api")
    try:
        time.sleep(1)
        api = twitter.Api(consumer_key=CONSUMER_KEY,
                          consumer_secret=CONSUMER_SECRET,
                          access_token_key=ACCESS_TOKEN_KEY,
                          access_token_secret=ACCESS_TOKEN_SECRET)
        logger.info(str(api.VerifyCredentials()))
        users = api.GetFriends()
        print [u.name for u in users]
    except:
        time.sleep(1)
        init_twitter()

def listen_gpio():
    blink(23)
    logger.info("Startup complete. Ready!")
    while True:
        input_state = GPIO.input(18)
        if not input_state:
            GPIO.output(23, GPIO.LOW)
            print 'Button Pressed'
            logger.info('Button pressed')
            callback_q.put(execute)
            play_sound()
            time.sleep(0.5)
        else:
            GPIO.output(23, GPIO.HIGH)


def execute():
    take_snapshot()
    global count
    count += 1
    try:
        logger.info(status)
        message = 'I push button, I go poop now? (%d)' % (count)
        status = api.PostMedia(message, "/home/pi/webcam/%s" % (SNAP_NAME))
        print status.text
        logger.info(status.text)
        status = api.PostDirectMessage(message, screen_name=TWITTER_HANDLE_PRIMARY)
        print status.text
        logger.info(status.text)
        print('Tweet sent')
    except:
        logger.info("Failed twitter upload")

def blink(pin):
    for x in range(0,5):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.5) 
    
def play_sound():
    logger.info("Playing sound")
    result = subprocess.check_call(['omxplayer', '/home/pi/twitter/bell.mp3'])
    print result
    logger.info(result)


def take_snapshot():
    logger.info("Taking snapshot")
    snap_name = datetime.now().strftime('%Y.%m.%d:%H.%M.%S')
    snap_dir = "/home/pi/webcam/%s" % (SNAP_NAME)
    logger.info('Saving out put to %s' % (snap_dir))
    result = subprocess.check_call(['fswebcam', '-r', '1280x720', '--no-banner', snap_dir])
    print result
    logger.info(result)

init_twitter()

try:
    logger.info("Starting listen_gpio thread")
    threading.Thread(target=listen_gpio).start()
    while True:
        callback = callback_q.get()
        callback()
except KeyboardInterrupt:
    print 'keyboard interrupt in main'
    GPIO.cleanup()
    
