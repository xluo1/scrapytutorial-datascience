### imports
import scrapy
from scrapy.crawler import CrawlerProcess
import re
from scrapy import settings
import json
import os


### Stream object

class Stream(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    streamer = scrapy.Field()
    views = scrapy.Field()
    likes = scrapy.Field()
    dislikes = scrapy.Field()
    desc = scrapy.Field()
    
### Item Pipeline

class StreamPipeline(object):
    
    def open_spider(self, spider):
        self.file = open('streams.jl', 'a')
   

    def close_spider(self, spider):
        self.file.close()
        

    def process_item(self, item, spider):
        item['views'] = item['views'][:-6]
            
        try:
            item['views'] = int(re.sub(",","",item['views']))
            
        except: 
            item['views'] = "N/A" # if html doesn't have this info
        
        
        try:
            item['dislikes'] = int(re.sub(",","",item['dislikes']))
        except:
            item['dislikes'] = "N/A"
        
        try:
            item['likes'] = int(re.sub(",","",item['likes']))
        except:
            item['likes'] = "N/A"
   
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item
        
        

### Spider object

class ytSpider(scrapy.Spider):
    name = "yt" # uniquely IDs each spider in a project, more relevant when you run startproject and get all the files but we ... aren't doin that here
        
    custom_settings = {'ITEM_PIPELINES':{'youtubespider.StreamPipeline':0}}

    def start_requests(self):
        # initiates spider
        ytURL = 'https://www.youtube.com/gaming/live'
        yield scrapy.Request(url=ytURL, callback=self.parseLivePage)
       

        
    def parseLivePage(self, response):
        # Currently on the page with all livestreams 
        # Get URLs of all streams on this page
        vidURLS = []
        titles = response.xpath('//*[contains(@class,"yt-lockup-title")]') 
        for vid in titles:
            link = vid.xpath('.//a/@href').get() # must have . at beginning to search WITHIN this selector!
            link = "https://www.youtube.com" + link  #MUST have https
            vidURLS.append(link)
        for link in vidURLS:
            streamItem = scrapy.Request(url=link, callback=self.parseVid)
            yield streamItem
            
        
    def parseVid(self, response):
        
        # get url
        url = response.url

        # get title
        title = response.xpath('//*/span[contains(@class, "watch-title")]/@title').get()
        
        # get streamer
        streamer = response.xpath('///*[contains(@class, "video-thumb  yt-thumb yt-thumb-48")]/span/span/img/@alt').get()
        
        # get number views
        views = response.xpath('string(//*[contains(@class, "watch-view-count")])').get()
        
        
        # get number likes
        likes = response.xpath('string(//*[contains(@class,"yt-uix-button yt-uix-button-size-default yt-uix-button-opacity yt-uix-button-has-icon no-icon-markup like-button-renderer-like-button like-button-renderer-like-button-clicked yt-uix-button-toggled  hid yt-uix-tooltip")]/span)').get()
      
        
        # get number dislikes
        dislikes = response.xpath('string(//*[contains(@class,"yt-uix-button yt-uix-button-size-default yt-uix-button-opacity yt-uix-button-has-icon no-icon-markup like-button-renderer-dislike-button like-button-renderer-dislike-button-clicked yt-uix-button-toggled  hid yt-uix-tooltip")]/span)').get()
        
        # get desc
        desc = response.xpath('string(//*[contains(@id, "eow-description")])').get()
        
        # add to df
        streamItem = Stream(url = url, title = title, streamer = streamer, views = views, likes = likes, dislikes = dislikes, desc = desc)
        return streamItem
        
       
        
   
        
            

### start process

open('streams.jl', 'w')
process = CrawlerProcess()
process.crawl(ytSpider)
process.start(stop_after_crawl=True)

 
### Analysis
import pandas as pd
import math
streams = []


for line in open('streams.jl','r'):
    streams.append(json.loads(line))

df = pd.DataFrame(streams)    

minecraftDF = df[df['desc'].str.contains("minecraft", case=False)]
noMinecraft = df[~df['desc'].str.contains("minecraft", case=False)]

percent = len(minecraftDF)/len(noMinecraft)
print(percent)

import matplotlib.pyplot as plt
import numpy as np

scalar = 1000000
fixedDF = (df[~df['views'].str.contains("N/A", case=False, na=False)]['views'])/scalar
fixedDF = fixedDF.tolist()


plt.hist(fixedDF, bins = 5 )

plt.show()

