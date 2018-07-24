# -*- coding: utf-8 -*-
'''by sudo rm -rf  http://imchenkun.com'''

import os
import requests
from bs4 import BeautifulSoup
import datetime
from faker import Factory
import Queue
import threading

fake = Factory.create()
luoo_site = 'http://www.luoo.net/music/'
luoo_site_mp3 = 'http://mp3-cdn2.luoo.net/low/luoo/radio%s/%s.mp3'

headers = {
    'Connection': 'keep-alive',
    'User-Agent': fake.user_agent()
}


def get_FileSize(filepath):
    fsize = os.path.getsize(filepath)
    fsize = fsize / float(1024 * 1024)
    return round(fsize, 2)


def fix_characters(s):
    for c in ['<', '>', ':', '"', '/', '\\\\', '|', '?', '*']:
        s = s.replace(c, '')
    return s


class LuooSpider(threading.Thread):
    def __init__(self, url, vols, queue=None):
        threading.Thread.__init__(self)
        self.url = url
        self.queue = queue
        self.vol = '1'
        self.vols = vols

    def run(self):
        start = datetime.datetime.now()
        print '[luoo spider start]'
        print '=' * 20
        for vol in self.vols:
            self.spider(vol)
        end = datetime.datetime.now()
        print '[luoo spider end]',
        print (end - start).seconds,
        print 's'
        print '=' * 20

    def spider(self, vol):
        url = luoo_site + vol
        print 'crawling: ' + url + '\\n'
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.find('span', attrs={'class': 'vol-title'}).text
        cover = soup.find('img', attrs={'class': 'vol-cover'})['src']
        desc = soup.find('div', attrs={'class': 'vol-desc'})
        track_names = soup.find_all('a', attrs={'class': 'trackname'})
        track_count = len(track_names)
        tracks = []
        for track in track_names:
            _id = str(int(track.text[:2])) if (int(vol) < 12) else track.text[
                                                                   :2]  # 12期前的音乐编号1~9是1位（如：1~9），之后的都是2位 1~9会在左边垫0（如：01~09）
            _name = fix_characters(track.text[4:])
            tracks.append({'id': _id, 'name': _name})
        phases = {
            'phase': vol,  # 期刊编号
            'title': title,  # 期刊标题
            'cover': cover,  # 期刊封面
            'desc': desc,  # 期刊描述
            'track_count': track_count,  # 节目数
            'tracks': tracks  # 节目清单(节目编号，节目名称)
        }
        self.queue.put(phases)


class LuooDownloader(threading.Thread):
    def __init__(self, url, dist, queue=None):
        threading.Thread.__init__(self)
        self.url = url
        self.queue = queue
        self.dist = dist
        self.__counter = 0

    def run(self):
        print 'thread start'
        start = datetime.datetime.now()
        while True:
            if self.queue.qsize() <= 0:
                break
            else:
                phases = self.queue.get()
                self.download(phases)
        end = datetime.datetime.now()
        print 'thread end',
        print (end - start).seconds

    def download(self, phases):
        for track in phases['tracks']:
            file_url = self.url % (phases['phase'], track['id'])

            local_file_dict = '%s/%s' % (self.dist, phases['phase'])
            if not os.path.exists(local_file_dict):
                os.makedirs(local_file_dict)

            local_file = '%s/%s.%s.mp3' % (local_file_dict, track['id'], track['name'])
            if not os.path.isfile(local_file):
                res = requests.get(file_url, headers=headers)
                with open(local_file, 'wb') as f:
                    f.write(res.content)
                    f.close()
                print 'downloaded: ' + track['name'] + str(get_FileSize(local_file)) + 'MB'
            else:
                print 'break: ' + track['name']


if __name__ == '__main__':
    spider_queue = Queue.Queue()

    luoo = LuooSpider(luoo_site, vols=['680', '721', '725', '720'], queue=spider_queue)
    luoo.setDaemon(False)
    luoo.start()
    luoo.join()

    downloader_count = 5
    luoo_download_thread = []
    for i in range(downloader_count):
        luoo_download = LuooDownloader(luoo_site_mp3, 'D:/luoo', queue=spider_queue)
        luoo_download_thread.append(luoo_download)
        luoo_download.setDaemon(False)
        luoo_download.start()

    for thread in luoo_download_thread:
        thread.join()
