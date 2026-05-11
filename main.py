import requests, time
from ppllocr import OCR
ocr, sess = OCR(), requests.Session()
while True:
    try:
        data = sess.get('https://vjudge.net/util/luogu/captcha/next')
        if len(data.text)==0:
            time.sleep(1)
            continue
        print(data.text)
        tid = data.text
        img = sess.get(f'https://vjudge.net/util/luogu/captcha/image?id={tid}').content
        code = ocr.classification(img)
        if len(code)!=4:
            code='1145'
        print('验证码：'+code)
        sess.post('https://vjudge.net/util/luogu/captcha/provide',
                    data={'id': tid, 'code': code, 'contributor': 'captcha_bot'})
    except:
        time.sleep(1)
