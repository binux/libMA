import sys
from ma import MA

login_id = sys.argv[1]
password = sys.argv[2]
regist = sys.argv[3]

ma = MA()
ma.login(login_id, password)
#ma.check_inspection()
#ma.notification_post_devicetoken(login_id, password)
#try:
    #ma.regist(login_id, password, regist)
#except:
    #pass
ma.save_character(login_id)

ma.tutorial_next(7030)
ma.tutorial_next(8000)
