# -*-coding:utf-8 -*-

import time

from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from urllib import urlretrieve
from selenium import webdriver
from bs4 import BeautifulSoup
import PIL.Image as image
import re
import numpy as np



#缓动函数
def ease_out_expo(x):
    if x == 1:
        return 1
    else:
        return 1 - pow(2,-10 * x)


class Crack():
    def __init__(self, username, passwd):
        self.url = 'https://passport.bilibili.com/login'
        self.browser = webdriver.Chrome('chromedriver')
        self.wait = WebDriverWait(self.browser, 100)
        #初始边界值
        self.BORDER = 6
        self.passwd = passwd
        self.username = username

    def open(self):
        """
        打开浏览器,并输入查询内容
        """
        self.browser.get(self.url)
        keyword = self.wait.until(EC.presence_of_element_located((By.ID, 'login-username')))
        keyword.send_keys(self.username)
        keyword = self.wait.until(EC.presence_of_element_located((By.ID, 'login-passwd')))
        keyword.send_keys(self.passwd)
        # bowton.click()

    def get_images(self, bg_filename='bg.jpg', fullbg_filename='fullbg.jpg'):
        """
        获取验证码图片
        return: 图片的location信息
        """
        bg = []
        fullgb = []
        while bg == [] and fullgb == []:
            bf = BeautifulSoup(self.browser.page_source, 'lxml')
            bg = bf.find_all('div', class_='gt_cut_bg_slice')
            fullgb = bf.find_all('div', class_='gt_cut_fullbg_slice')
        bg_url = re.findall('url\(\"(.*)\"\);', bg[0].get('style'))[0].replace('webp', 'jpg')
        fullgb_url = re.findall('url\(\"(.*)\"\);', fullgb[0].get('style'))[0].replace('webp', 'jpg')
        bg_location_list = []
        fullbg_location_list = []
        for each_bg in bg:
            location = {}
            location['x'] = int(re.findall('background-position: (.*)px (.*)px;', each_bg.get('style'))[0][0])
            location['y'] = int(re.findall('background-position: (.*)px (.*)px;', each_bg.get('style'))[0][1])
            bg_location_list.append(location)
        for each_fullgb in fullgb:
            location = {}
            location['x'] = int(re.findall('background-position: (.*)px (.*)px;', each_fullgb.get('style'))[0][0])
            location['y'] = int(re.findall('background-position: (.*)px (.*)px;', each_fullgb.get('style'))[0][1])
            fullbg_location_list.append(location)

        urlretrieve(url=bg_url, filename=bg_filename)
        # print('缺口图片下载完成')
        urlretrieve(url=fullgb_url, filename=fullbg_filename)
        # print('背景图片下载完成')
        return bg_location_list, fullbg_location_list

    def get_merge_image(self, filename, location_list):
        """
        根据位置对图片进行合并还原
        :filename:图片
        :location_list:图片位置
        """
        im = image.open(filename)
        im_list_upper = []
        im_list_down = []

        for location in location_list:
            if location['y'] == -58:
                #crop:从图像中提取出某个矩形大小的图像。它接收一个四元素的元组作为参数，各元素为（left, upper, right, lower），坐标系统的原点（0, 0）是左上角。
                im_list_upper.append(im.crop((abs(location['x']), 58, abs(location['x']) + 10, 116)))
            if location['y'] == 0:
                im_list_down.append(im.crop((abs(location['x']), 0, abs(location['x']) + 10, 58)))

        new_im = image.new('RGB', (260, 116))

        x_offset = 0
        for im in im_list_upper:
            new_im.paste(im, (x_offset, 0))
            x_offset += im.size[0]

        x_offset = 0
        for im in im_list_down:
            new_im.paste(im, (x_offset, 58))
            x_offset += im.size[0]

        new_im.save(filename)

        return new_im


    def is_pixel_equal(self, img1, img2, x, y):
        """
        判断两个像素是否相同
        image1: 图片1
        image2: 图片2
        x: 位置x
        y: 位置y
        return: 像素是否相同
        """
        # 取两个图片的像素点
        pix1 = img1.load()[x, y]
        pix2 = img2.load()[x, y]
        threshold = 50
        if (abs(pix1[0] - pix2[0] < threshold) and abs(pix1[1] - pix2[1] < threshold) and abs(
                pix1[2] - pix2[2] < threshold)):
            return True
        else:
            return False

    def get_gap(self, img1, img2):
        """
        获取缺口偏移量
        img1: 不带缺口图片
        img2: 带缺口图片
        return:
        """
        for i in range(img1.size[0]):
            for j in range(img1.size[1]):
                if not self.is_pixel_equal(img1, img2, i, j):
                    left = i
                    return left
        # return left

    def get_track(self, distance,seconds,ease_func):
        tracks = [0]
        offsets = [0]
        for t in np.arange(0.0,seconds,0.1):
            ease = globals()[ease_func]
            offset = round(ease(t / seconds) * distance)
            tracks.append(offset - offsets[-1])
            offsets.append(offset)
        return offsets,tracks


    def get_slider(self):
        """
        获取滑块
        return: 滑块对象
        """
        while True:
            try:
                slider = self.browser.find_element_by_xpath("//div[@class='gt_slider_knob gt_show']")
                break
            except:
                time.sleep(0.5)
        return slider

    def move_to_gap(self, slider, tracks):
        """
        拖动滑块到缺口处
        slider: 滑块
        track: 轨迹
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in tracks:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        ActionChains(self.browser).pause(0.5).release().perform()
        #松开鼠标左键


    def crack(self):
        # 打开浏览器
        self.open()
        time.sleep(0.3)
        while 1:
            # 保存的图片名字
                bg_filename = 'bg.jpg'
                fullbg_filename = 'fullbg.jpg'

                # 获取图片
                bg_location_list, fullbg_location_list = self.get_images(bg_filename, fullbg_filename)

                # 根据位置对图片进行合并还原
                bg_img = self.get_merge_image(bg_filename, bg_location_list)
                fullbg_img = self.get_merge_image(fullbg_filename, fullbg_location_list)

                # 获取缺口位置
                gap = self.get_gap(fullbg_img, bg_img)
                # print('获取缺口位置')
                offsets,tracks = self.get_track(gap - self.BORDER,12,'ease_out_expo')
                # print('滑动滑块')

                # 点按呼出缺口
                slider = self.get_slider()

                # 拖动滑块到缺口处
                self.move_to_gap(slider, tracks)

                # 点击登陆
                self.browser.find_element_by_xpath('//a[@class="btn btn-login"]').click()
                #验证失败等待5s
                time.sleep(2)
                if self.browser.current_url == self.url:
                    print('验证失败')
                    time.sleep(3)
                else:
                    print('登陆成功')
                    break





    def send_comment(self):
        self.browser.find_element_by_xpath('//div[@class="groom-module home-card"][1]').click()
        time.sleep(2)
        self.browser.switch_to_window(self.browser.window_handles[-1])
        #下拉
        targetElem = self.browser.find_element_by_xpath('//div[@class="bilibili-player-video"]')
        self.browser.execute_script("arguments[0].scrollIntoView();", targetElem)
        time.sleep(1)
        #发送弹幕
        self.browser.find_element_by_xpath('//input[@class="bilibili-player-video-danmaku-input"]').send_keys('666')
        self.browser.find_element_by_xpath('//div[@class="bilibili-player-video-btn-send bpui-component bpui-button button"]').click()

        #下拉
        targetElem = self.browser.find_element_by_xpath('//div[@id="arc_toolbar_report"]')
        self.browser.execute_script("arguments[0].scrollIntoView();", targetElem)
        targetElem = self.browser.find_element_by_xpath('//div[@id = "recommend_report"]')
        self.browser.execute_script("arguments[0].scrollIntoView();", targetElem)
        time.sleep(1)
        #发送评论
        self.browser.find_element_by_xpath('//textarea[@class="ipt-txt"]').send_keys('666')
        self.browser.find_element_by_xpath('//button[@class="comment-submit"]').click()







if __name__ == '__main__':
    crack = Crack('username', 'passwd')
    crack.crack()
    crack.send_comment()

