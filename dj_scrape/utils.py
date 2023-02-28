import fake_useragent,re
from urllib import request
from bs4 import BeautifulSoup
from django.core import exceptions
from items.models import Item,Img,Record

def get_certain_item_info(url:str)->dict:
    def check_if_color_option_exist(soup):
        try:
            info_box = soup.find('div',id='variation_color_name')
            info = info_box.select_one('span.selection').text.strip()
        except AttributeError:
            info = None
        return info
    def check_if_size_option_exist(soup):
        try:
            info_box = soup.find('div',id='variation_size_name')
            info = info_box.select_one('span.selection').text.strip()
        except AttributeError:
            info = None
        return info
    ua = fake_useragent.UserAgent()
    headers = {'User-Agent': ua.random}
    reques = request.Request(url=url,headers=headers)
    response = request.urlopen(reques)
    html = response.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser')
    try:
        src = soup.select_one("div.imgTagWrapper>img")['src']
    except TypeError: # 也许是游戏商品
        src = soup.select_one("img#js-masrw-main-image")['src']
    try:
        name = soup.find('span',id='productTitle').text.strip().replace(" ","")
    except AttributeError:
        name = soup.select_one('span#btAsinTitle').text.strip().replace(" ","")
    try:
        ori_price = soup.find('span', class_="a-offscreen").text
    except AttributeError:
        ori_price = soup.select_one('span#actualPriceValue>strong.priceLarge').text
    price = int("".join(re.findall(r"\d",ori_price)))
    size_info = check_if_size_option_exist(soup)
    color_info = check_if_color_option_exist(soup)
    return {'name':name,'price':price,'size':size_info,'color':color_info,'src':src}

def save_item_or_add_record_on_exist_item(url:str,item_info:dict):
    def save_img_if_not_exist_in_certain_item(item_info,item):
        try:
            img = Img.objects.get(src=item_info['src'])
        except exceptions.ObjectDoesNotExist:
            img = Img()
            img.src = item_info['src']
            img.item = item
            img.save()
        else:
            if img.item != item:
                img = Img()
                img.src = item_info['src']
                img.item = item
                img.save()
    item,created = Item.objects.get_or_create(url=url)
    if created:
        item.name = item_info['name']
        item.size = item_info['size']
        item.color = item_info['color']
        item.save()
    record = Record()
    record.item = item
    record.price = item_info['price']
    record.save()
    save_img_if_not_exist_in_certain_item(item_info,item)
    return item