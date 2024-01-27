import json
import requests
import scrapy
import os


class MauiJimSpider(scrapy.Spider):
    name = "maui_jim"
    allowed_domains = ["trade.mauijim.com"]
    data_list = []

    def get_cookie(self):
        login_url = "https://trade.mauijim.com/mauijimb2bstorefront/en_US/j_spring_security_check"
        username = "joel@nadlanrealty.com"
        password = "f$sSCvu7BV7!qEW"
        j_username = "mj_trade_joel@nadlanrealty.com"

        # Create a session to persist cookies across requests
        session = requests.Session()

        # Send a GET request to the login page to obtain initial cookies and CSRF token
        login_page_response = session.get(login_url)

        # Extract CSRF token from the response
        csrf_token = login_page_response.cookies.get("CSRFToken")

        headers = {
                    'content-type': 'application/x-www-form-urlencoded',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }

        payload = f'j_formusername={username}&j_username={j_username}&j_password={password}&b2bUnit=&_spring_security_remember_me=false&CSRFToken={csrf_token}'

        # Send a POST request to perform the login
        login_response = session.post(login_url, data=payload, headers=headers)

        cookies_dict = session.cookies.get_dict()
        print(cookies_dict)
        return cookies_dict

    def start_requests(self):
        new_cookies = self.get_cookie()
        print(new_cookies)
        cookies_str = ';'.join([f"{key}={value}" for key, value in new_cookies.items()])

        url = 'https://trade.mauijim.com/mauijimb2bstorefront/en_US/c/b2bsun_mauijim/'

        headers = {
            'cookie': f'{cookies_str}',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        cookies = new_cookies
        yield scrapy.Request(url, headers=headers, method="GET", callback=self.parse,cookies=cookies,  meta={'headers': headers, 'cookies': cookies})

    def parse(self, response):
        headers = response.meta['headers']
        cookies = response.meta['cookies']
        print(headers)
        print(cookies)

        product = ["https://trade.mauijim.com" + i.strip() for i in response.xpath("//a[@class='product-url']/parent::div/a/@href").getall() if i.strip()]
        for url in product:
            print(url)
            yield scrapy.Request(url, headers=headers, method="GET", callback=self.get_product,cookies=cookies,  meta={'headers': headers, 'cookies': cookies})
            

    def get_product(self, response):
        headers = response.meta['headers']
        cookies = response.meta['cookies']
        f= open("a.html","w",encoding="utf-8")
        f.write(response.text)
        data_dict = {}
        data_dict['product_name'] = response.xpath("//div[@class='product-title']//h2/text()").get().strip()
        data_dict['lens_material'] = response.xpath("//strong[contains(text(), 'Lens Material:')]/following-sibling::span/text()").get().strip()
        data_dict['maui_evolution'] = response.xpath("//strong[contains(text(), 'Maui Evolution:')]/following-sibling::text()").get().strip()
        data_dict['polycarbonate'] = response.xpath("//strong[contains(text(), 'Polycarbonate:')]/following-sibling::text()").get().strip()
        data_dict['maui_brilliant'] = response.xpath("//strong[contains(text(), 'MauiBrilliant:')]/following-sibling::text()").get().strip()
        dive_elements = response.xpath("//fieldset/div[starts-with(@class, 'row body variantitem')]")

        data_dict['style_code'] = [dive.xpath(".//span[@class='style-number']/text()").get().strip() for dive in dive_elements]
        data_dict['frame'] = [dive.xpath(".//span[@class='framecolor-label']/following-sibling::text()").get().strip() for dive in dive_elements]
        data_dict['lens'] = [dive.xpath(".//span[@class='lenscolor-label']/following-sibling::text()").get().strip() for dive in dive_elements]
        data_dict['price'] = [dive.xpath(".//span[@class='price-label']/following-sibling::text()").get().strip() for dive in dive_elements]
        self.data_list.append(data_dict)
        data_dict['image_url'] = []
        for image_code in data_dict['style_code']:
            code = image_code.split("-")[0]
            cleaned_code = ''.join(char for char in code if not char.isalpha())
            # data_dict['image_url'].append(f"https://images.mauijim.com/sunglasses/{cleaned_code}/{image_code}_side.jpg")
            # data_dict['image_url'].append(f"https://images.mauijim.com/sunglasses/{cleaned_code}/{image_code}_front.jpg")
            # data_dict['image_url'].append(f"https://images.mauijim.com/sunglasses/{cleaned_code}/{image_code}_quarter.jpg")
            image_url = f"https://images.mauijim.com/sunglasses/{cleaned_code}/{image_code}_side.jpg"
            image_name = image_url.split('sunglasses')[1]
            yield scrapy.Request(image_url, method="GET", headers=headers, cookies=cookies, callback=self.image_response, meta={"image_name": image_name})

            image_url = f"https://images.mauijim.com/sunglasses/{cleaned_code}/{image_code}_front.jpg"
            image_name = image_url.split('sunglasses')[1]
            yield scrapy.Request(image_url, method="GET", headers=headers, cookies=cookies, callback=self.image_response, meta={"image_name": image_name})

            image_url = f"https://images.mauijim.com/sunglasses/{cleaned_code}/{image_code}_quarter.jpg"
            image_name = image_url.split('sunglasses')[1]
            yield scrapy.Request(image_url, method="GET", headers=headers, cookies=cookies, callback=self.image_response, meta={"image_name": image_name})

    def image_response(self, response):
        image_name = response.meta['image_name']
        image_data = response.body
        image_filename = f"image_output{image_name}"
        os.makedirs(os.path.dirname(image_filename), exist_ok=True)
        with open(image_filename, 'wb') as image_file:
            image_file.write(image_data)

    def closed(self, reason):
        with open("output.json", "w") as output_file:
            json.dump(self.data_list, output_file)