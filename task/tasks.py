import logging,fake_useragent,re
from urllib import request
from bs4 import BeautifulSoup
from django_celery_beat.models import PeriodicTask
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from items.models import Item,Record
from dj_scrape.celery import app
log = logging.getLogger("django")

def get_price(url):
    ua = fake_useragent.UserAgent()
    headers = {'User-Agent': ua.random}
    reques = request.Request(url=url,headers=headers)
    response = request.urlopen(reques)
    html = response.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser')
    try:
        ori_price = soup.find('span', class_="a-offscreen").text
    except AttributeError: # 也许是游戏商品
        ori_price = soup.select_one('span#actualPriceValue>strong.priceLarge').text
    price = int("".join(re.findall(r"\d",ori_price)))
    return price


@app.task
def periodic_task(*args,**kwargs):
    try:
        item =  get_object_or_404(Item,url=kwargs['url'])
    except Http404:
        err_msg = "查询错误，该商品已被删除"
    else:
        print(f"开始查询<{kwargs['name']}>的价格")
        url = kwargs['url']
        price = get_price(url)
        if kwargs['email']:
            if kwargs['email when'] == "every check":
                print(f"发送到此邮箱: {kwargs['email']}")
                msg=f"{kwargs['name']}\n当前价格为:{price}¥"
                html_msg=f"""<h2>{kwargs['name']}</h2>
                            <p>当前价格为: {price} ¥</p>
                            <p>点击前往: {url}</p>"""
            elif kwargs['email when'] == "when price drop":
                last_record_price = item.record_set.values_list('price',flat=True).order_by('-scrape_time').first()
                Record.objects.create(item=item,price=price)
                if price < last_record_price:
                    msg = f"您收藏的商品已降价\n{last_record_price}---->{price}\n点击前往{url}"
                    html_msg = f"""<h2>商品{kwargs['name']}已降价</h2>
                                    <h3><s>{last_record_price}</s> -> {price}</h3>
                                    <h3>点击前往{url}</h3>"""
                else:
                    return "商品未降价，仅保存记录"
            elif kwargs['email when'] == "when price lower than":
                price_lt = int(kwargs['price lt'])
                Record.objects.create(item=item,price=price)
                if price < price_lt:
                    msg = f"您收藏的商品价格已降至{price}\n(您设定的价格: {price_lt})\n点击前往{url}"
                    html_msg = f"""<h2>商品{kwargs['name']}价格已降至{price}</h2>
                                    <p>(您设定的价格: {price_lt})</p>
                                    <h3>点击前往{url}</h3>"""
                else:
                    return "商品未降至预期价格，仅保存记录"
            result = send_mail(
                    subject="django定时邮件",
                    message=msg,
                    from_email='60659wd@gmail.com',
                    recipient_list=[kwargs['email'],],
                    html_message=html_msg
                )
            return f"查询完成, 邮件已发送: {result}"
        else:
            return "查询完成"


# @app.task
# def periodic_task(*args,**kwargs):
#     print('Jjjjjjj')
#     return 'test'


# celery -A dj_scrape worker -l info -P eventlet -c 8

