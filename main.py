#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from time import sleep
import time
import requests
import urlparse
import re
import qrcode
import random
import csv
reload(sys)
sys.setdefaultencoding('utf-8')


def main():
#     browser = webdriver.Chrome(
#         executable_path=sys.path[0] + "/chromedriver")
    ff_option = Options()
    ff_option.add_argument('-headless')
    keyword = raw_input("请输入产品关键词:")
    min_price = raw_input("请输入最低价")
    max_price = raw_input("请输入最高价")
    print "正在搜索关键词:%s" % keyword.strip()
    browser = webdriver.Firefox(executable_path=sys.path[0] + "/geckodriver", options=ff_option)
    search_url = "https://list.tmall.com/search_product.htm?q=%s" % (keyword)
    browser.get(search_url)
    sleep(1)
    totalPage = browser.find_element_by_name("totalPage").get_property("value")
    print "关键词产品共有%s页" % totalPage
    element = browser.find_element_by_link_text("请登录")
    
    login_url = element.get_property("href")
    browser.get(login_url)
    sleep(1)
    showQr(browser)
    while isLogin(browser) == False:
        sleep(2)
#         if needShowQr(browser):
#              showQr(browser, False)
    print "登录成功!"
    
    for page in range(1, int(totalPage) + 1):
        print "正在解析第%d页的数据(%d/%d)" % (page, page, int(totalPage))
        browser.get(search_url)
        sleep(2)
        products = browser.find_elements_by_css_selector('.product a')
        product_urls = []
        for p in products:
            product_urls.append(p.get_property('href'))
            
        productList = analysisProductList(browser, product_urls, page)
         #
        saveCsvFile(keyword, productList)
        sleep(6)
        if page != totalPage:
            search_url = browser.find_element_by_link_text("下一页>>").get_property("href")
            sleep(2)
            
    print "任务完成"


def showQr(browser, needSwitch=True):
    sleep(1)
    if needSwitch == True:
        browser.switch_to_frame(browser.find_element_by_css_selector('#J_loginIframe'))
        sleep(1)
    img_src = browser.find_element_by_xpath("/html/body/div[1]/div/div/div[2]/div[4]/div/div[3]/div[1]/div[1]/img").get_property("src")
    print "解析登录链接中"
    response = requests.post("https://cli.im/Api/Browser/deqr", data={'data':img_src})   
    result = response.json()
    url = result['data']['RawData']
    qr = qrcode.QRCode(version=1)
    qr.add_data(url.strip())
    if sys.stdout.isatty():
        qr.print_tty()
        print "请用淘宝客户端扫码登录"
        
    browser.switch_to_default_content()
    return    
    
    
def qs(url, param): 
    query = urlparse.urlparse(url).query 
    parmas = dict([(k, v[0]) for k, v in urlparse.parse_qs(query).items()])
    if param in parmas:
        return parmas[param]
    return None


def isElementExistByXpath(browser, xpath):
    flag = True
    try:
        browser.find_element_by_xpath(xpath)
        return flag
    except:
        flag = False
        return flag


def isElementExistByClass(browser, classname):
    flag = True
    try:
        browser.find_element_by_class_name(classname)
        return flag
    except:
        flag = False
        return flag


def isElementExistById(browser, id):
    flag = True
    try:
        browser.find_element_by_id(id)
        return flag
    except:
        flag = False
        return flag


def isLogin(browser):
    return isElementExistByXpath(browser, "//*[@id=\"login-info\"]/span[1]/span")


# 分析产品列表
def analysisProductList(browser, urls, page, max_price, min_price):
    products = [];
    print "解析成功第%s页的数据,共%d件产品" % (page, len(urls))
    for url, index in urls:
       products.append(analysisProduct(browser, url, index, page, max_price, min_price))
    return products
    

def analysisProduct(browser, url, No, pageNo, max_price, min_price):
    sleep(random.randint(2, 10))
    id = qs(url, 'id')
    browser.get(url)
    
    title = getContentByCssSelecter(browser, ".tb-detail-hd h1")
    print "正在分析:%s" % (title)
    price = 0
    saleprice = 0
    prices = browser.find_elements_by_css_selector(".tm-price")
    price_array = []
    for p in prices:
        price_array.append(p.get_property('innerText'))

    if price_array:
        price = max(price_array)
        saleprice = min(price_array)
        
    if saleprice >= min_price and saleprice <= max_price:
        send_place = getContentByCssSelecter(browser, "#J_deliveryAdd") 
        shopname = getContentByCssSelecter(browser, ".slogo-shopname strong") 
        fee = re.sub(r'\D', '', getContentByCssSelecter(browser, ".tb-postAge-info"))
        hot = re.sub(r'\D', '', getContentByCssSelecter(browser, "#J_CollectCount"))
        comment_count = getContentByCssSelecter(browser, ".tm-ind-reviewCount .tm-count")
        sale_count = getContentByCssSelecter(browser, ".tm-ind-sellCount .tm-count")
        brand = getContentByCssSelecter(browser, "#J_BrandAttr .J_EbrandLogo")
        return [pageNo, (pageNo - 1) * 60 + No, sale_count, comment_count, id, title, price, saleprice, send_place, shopname, fee, hot, brand]
    else: 
        return None


def needShowQr(browser):
    browser.switch_to_frame(browser.find_element_by_css_selector('#J_loginIframe'))
    element = browser.find_element_by_class_name("msg-err")
    if element.value_of_css_property("display") != "none":
        showQr(browser, False)
    else:
        print "还未监测需要更换二维码"
        
    browser.switch_to_default_content()
    sleep(1)
    return


def getContentByCssSelecter(browser, css_selecter):
    try:
        return browser.find_element_by_css_selector(css_selecter).get_property('innerText')
    except:
        return ""
    
    return 


def saveCsvFile(keyword, productList):
    if len(productList) == 0:
        print "不存在产品列表信息"
        return
    time = time.strftime("%Y%m%d", time.localtime())
    filename = "/data/%s_%s.csv" % (keyword, time);
    file_path = sys.path[0] + filename
    
    if os.path.exists(file_path):
        out = open(file_path, 'a')
        csv_write = csv.writer(out, dialect='excel')
        labels = ['所在页数', '排名', '销售量', '评论里', '产品编号', '产品标题', '产品原价', '产品销售价', '发货地', '店铺名称', '邮费', '热度', '品牌']
        csv_write.writerow(labels)
    else:
        with open(file_path, 'w') as csv_file:
            csv_write = csv.writer(csv_file) 
            
    for product in productList:
        csv_write.writerow(product)
    
    return filename


if __name__ == '__main__':
  main()
