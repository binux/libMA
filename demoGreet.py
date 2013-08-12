from _libMA import *
if __name__ == "__main__":
    from config import deviceToken, loginId, password
    device = Device(token=deviceToken)
    user = device.newUser(loginId=loginId, password=password)
    loginData = user.login()
    #random user id
    import random
    for j in range(10):
        userIds = [ random.randint(10000,999999) for i in range(10)]
        greetData = user.menu.likeUser(userIds)
        print "now friend ship point is",greetData.response.header.your_data.friendship_point

