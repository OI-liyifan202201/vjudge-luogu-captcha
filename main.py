import requests, time
from ppllocr import OCR
ocr, sess = OCR(), requests.Session()
while True:
    try:
        tid = sess.get('https://vjudge.net/util/luogu/captcha/next').text
        if not tid: time.sleep(0.5); continue
        img = sess.get(f'https://vjudge.net/util/luogu/captcha/image?id={tid}').content
        code, l, r = '', 0.1, 0.9
        for _ in range(5):
            m = (l + r) / 2
            code = ocr.classification(img, conf=m)
            if len(code) == 4: break
            if len(code) < 4: r = m  # 阈值太高，降低以识别更多
            else: l = m              # 阈值太低，提高以过滤噪声
        if len(code) != 4: code = '1145'
        print('验证码：'+code)
        sess.post('https://vjudge.net/util/luogu/captcha/provide',
                  data={'id': tid, 'code': code, 'contributor': 'captcha_bot'})
    except: time.sleep(1)
