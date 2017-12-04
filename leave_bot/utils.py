import requests, json


def send_ask_leave(token, name, reason, channel):
    url = 'https://hooks.slack.com/api/chat.postMessage?token='+token\
        +'&channel='+channel\
        +'&text='+name+' wants to leave: '+reason
    resp = requests.get(url)
    return json.loads(resp.text)

def answer_dm(token, message, user):
    resp = requests.get('https://slack.com/api/im.open?token='+token+'&user='+user)
    j = json.loads(resp.text)
    if j['ok'] == True:
        resp2 = requests.get('https://slack.com/api/im.list?token='+token)
        j2 = json.loads(resp2.text)
        im_id = [line['id'] for line in j2['ims'] if line['user']==user][0]
        resp3 = requests.get('https://slack.com/api/chat.postMessage?token='+token+'&channel='+im_id+'&text='+message)

