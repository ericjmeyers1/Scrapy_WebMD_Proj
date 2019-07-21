from scrapy import Spider
from scrapy import Request
from webmd.items import WebmdItem
import re

class WebMDSpider(Spider):
    name = 'webmd_spider'
    allowed_urls = ['https://www.webmd.com/']
    start_urls = ['https://www.webmd.com/drugs/2/condition-594/type+2+diabetes+mellitus']
    def parse(self, response):
        result_urls = response.xpath('//tbody//tr/td[4]/a/@href').extract()
        result_urls = ['https://www.webmd.com' + i for i in result_urls]

        #NOTE TO SELF: 'scrapy shell "relevant URL"' to initiate xpath validation

        #FIRST CHECKPOINT
        #print('='*50)
        #print(len(result_urls))
        #print('='*50)

        for url in result_urls:
            yield Request(url=url, callback=self.parse_result_page)


    def parse_result_page(self, response):
        # Now identify how many review pages to be scraped per drug
        # pages is first page, following three lines determine how many "next pages"
        pages = response.xpath('//div[@class="postPaging"]/text()').extract_first()
        reviewsperpage = int(re.findall('\d+', pages)[1])
        totalreviewpages = int(re.findall('\d+', pages)[2])
        numreviewpages = totalreviewpages // reviewsperpage

        # To get next review pages
        # create list of all urls for review number_pages
        # use num review pages to create list of drug_urls
        next_pages = response.xpath('//div[@class="postPaging"]/a/@href').extract()[2]
        drug_review_format = re.sub("pageIndex=1", "pageIndex=ZEBRA", next_pages)
        per_drug_url_list = [re.sub("ZEBRA",str(i),drug_review_format) for i in range(numreviewpages+1)]

        #create parsed list for all drug reviews
        final_drug_review_urls = []
        for url in per_drug_url_list:
            url = 'https://www.webmd.com' + url
            final_drug_review_urls.append(url)

        for url in final_drug_review_urls:
            yield Request(url=url, callback=self.parse_review)


    def parse_review(self, response):
        first_review_page = response.xpath('//div[@class="userPost"]').extract_first()
        reviews = response.xpath('//div[@class="userPost"]')


        #SECOND CHECKPOINT
        #print('='*50)
        #print(len(reviews))
        #print('='*50)


        # pull review data
        for review in reviews:
            drug = response.xpath('//div[@class="tb_main"]/h1/text()').extract_first()[25:]
            condition = review.xpath('//div[@class="conditionInfo"]/text()').extract_first().strip()[11:]
            Rdate = review.xpath('.//div[@class="date"]/text()').extract_first()
            reviewer = review.xpath('.//p[@class="reviewerInfo"]/text()').extract_first()[9:].strip()
            effectiveness = int(review.xpath('.//span[@class="current-rating"]/text()').extract()[0].strip()[16:])
            easeofuse = int(review.xpath('.//span[@class="current-rating"]/text()').extract()[1].strip()[16:])
            satisfaction = int(review.xpath('.//span[@class="current-rating"]/text()').extract()[2].strip()[16:])
            comment = review.xpath('//p[@class="comment"]/text()').extract_first()
            helpful = int(review.xpath('//p[@class="helpful"]/text()').extract_first()[:3].strip())

        # create review item
            item = WebmdItem()
            item['drug'] = drug
            item['condition'] = condition
            item['Rdate'] = Rdate
            item['reviewer'] = reviewer
            item['effectiveness'] = effectiveness
            item['easeofuse'] = easeofuse
            item['satisfaction'] = satisfaction
            item['comment'] = comment
            item['helpful'] = helpful
            yield item
