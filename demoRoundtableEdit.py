from _libMA import *
if __name__ == "__main__":
    from config import deviceToken, loginId, password
    device = Device(token=deviceToken)
    user = device.newUser(loginId=loginId, password=password)
    loginData = user.login()
    cardIds = map(lambda x:x.serial_id, loginData.response.header.your_data.owner_card_list.user_card)
    cardData = user.roundtable.edit()
    nowCardIds = filter(lambda x:x.isdigit(), cardData.response.body.roundtable_edit.deck_cards.split(","))
    print "now round table is ",",".join(nowCardIds)
    print "leader is ",cardData.response.body.roundtable_edit.leader_card
    print "random chose a card"
    import random
    card = random.choice(cardIds)
    print "chose",card
    saveData = user.roundtable.save([card,],card)
    print "roundtable saved"
