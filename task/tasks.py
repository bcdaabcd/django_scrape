import logging,fake_useragent,re
from urllib import request
from bs4 import BeautifulSoup
from django.core.mail import send_mail
from items.models import Item,Record
from dj_scrape.celery import app
log = logging.getLogger("django")

def get_price_and_save_by_exists_url(**kwargs):
    ua = fake_useragent.UserAgent()
    headers = {'User-Agent': ua.random}
    reques = request.Request(url=kwargs['url'],headers=headers)
    response = request.urlopen(reques)
    html = response.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser')
    try:
        ori_price = soup.find('span', class_="a-offscreen").text
    except AttributeError: # 也许是游戏商品
        ori_price = soup.select_one('span#actualPriceValue>strong.priceLarge').text
    price = int("".join(re.findall(r"\d",ori_price)))
    item = Item.objects.get(url=kwargs['url'])
    Record.objects.create(item=item,price=price)
    return price


@app.task
def periodic_task(*arg,**kwargs):
    print(f"开始查询<{kwargs['name']}>的价格")
    price = get_price_and_save_by_exists_url(**kwargs)
    if kwargs['email']:
        print(f"发送到此邮箱: {kwargs['email']}")
        result = send_mail(
            subject="django定时邮件",
            message=f"{kwargs['name']}\n当前价格为:{price}¥",
            from_email='60659wd@gmail.com',
            recipient_list=[kwargs['email'],],
            html_message=f"""
                <h2>{kwargs['name']}</h2>
                <p>当前价格为: {price} ¥</p>
                <p>点击前往: {kwargs['url']}</p>
            """
        )
        return f"查询完成，邮件发送完成: {result}"
    else:
        return "查询完成"


# celery -A dj_scrape beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
# celery -A dj_scrape worker -l info -P eventlet

