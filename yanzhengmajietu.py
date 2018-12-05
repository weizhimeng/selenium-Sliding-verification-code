# -*- coding: utf-8 -*-
from selenium import webdriver
from PIL import Image


def get_captchal():
    """
    通过截图获取图像验证码
    """
    url = 'http://wsbs.zjhz.hrss.gov.cn/index.html'
    driver = webdriver.Chrome()
    driver.get(url)
    driver.find_element_by_link_text(u"个人用户登录").click()
    driver.get_screenshot_as_file('./screenshot.png')
    img = driver.find_element_by_id('f_svl1')
    location = img.location
    size = img.size
    top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size['width']
    print(u'验证码位置', top, bottom, left, right)
    imgFrame = Image.open('./screenshot.png')
    imgFrame = imgFrame.crop((left, top, right, bottom))  # 裁剪
    imgFrame.save('./iframe.png')
    driver.close()

if __name__ == '__main__':
    get_captchal()

