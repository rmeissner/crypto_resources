from lxml import html
from eth_utils import to_checksum_address
import requests
import os
import sys
import json

class TokenInfoProvider(object):

    def __init__(self, token_info_path, token_img_base):
        self.tokens = []
        self.token_info_path = token_info_path
        self.token_img_base = token_img_base

    def download_file(self, url, taget_folder, local_filename):
        if not os.path.exists(taget_folder):
            os.makedirs(taget_folder)
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            print ("Image not found")
            return
        with open(os.path.join(taget_folder, local_filename), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)
        return local_filename

    def token_website_fallback(self, token_address):
        page = requests.get('https://etherscan.io/token/' + token_address)
        tree = html.fromstring(page.content)
        return tree.xpath('//tr[@id="ContentPlaceHolder1_tr_officialsite_1"]/td/a/text()')[0].strip()

    def token_info_fallback(self, token_address):
        page = requests.get('https://etherscan.io/readContract?v=0xb9469430eabcbfa77005cd3ad4276ce96bd221e3&a=' + token_address)
        tree = html.fromstring(page.content)
        return { 
            "address": token_address,
            "name": tree.xpath('//a[contains(text(), "name")]/../../following-sibling::div//div[@class="form-group"]/text()')[0].strip(),
            "symbol": tree.xpath('//a[contains(text(), "symbol")]/../../following-sibling::div//div[@class="form-group"]/text()')[0].strip(),
            "decimals": int(tree.xpath('//a[contains(text(), "decimals")]/../../following-sibling::div//div[@class="form-group"]/text()')[0].strip())
        }

    def pull_token_info(self, page_num=1):
        page = requests.get('https://etherscan.io/tokens?p=' + str(page_num))
        tree = html.fromstring(page.content)

        token_data = tree.xpath('//div[@id="ContentPlaceHolder1_divresult"]/table/tbody/tr')
        for element in token_data:
            link = element.xpath('td[@align="center"]/a/@href')[0]
            token_address = to_checksum_address(link[7:])
            print(token_address)
            desc = element.xpath('td/small/font/text()')
            self.download_file("https://raw.githubusercontent.com/TrustWallet/tokens/master/images/" + token_address.lower() + ".png", os.path.join(self.token_info_path, "icons"), token_address + ".png")
            token_request = requests.get("https://raw.githubusercontent.com/ethereum-lists/tokens/master/tokens/eth/" + token_address + ".json")
            data = None
            if token_request.status_code == 200:
                data = token_request.json()
            
            if not data: 
                data = self.token_info_fallback(token_address)

            if not data:
                print ("Token info not found")
                continue
            
            if not data.get('website'):
                data['website'] = self.token_website_fallback(token_address)

            data['description'] = desc[0] if desc else None
            self.tokens.append(data)

    def write_tokens(self, pages=1):
        self.tokens = []
        for page in range(1, pages + 1):
            self.pull_token_info(page)
        data = {
            "count":len(self.tokens),
            "next":None,
            "previous":None,
            "results": [
                {
                    "token": {
                        "address": to_checksum_address(token.get('address')),
                        "name": token.get('name'),
                        "symbol": token.get('symbol'),
                        "description": token.get('description'),
                        "decimals": token.get('decimals'),
                        "logoUrl": self.token_img_base + to_checksum_address(token.get('address')) + ".png",
                        "websiteUrl": token.get('website')
                    },
                    "default": False
                } for token in self.tokens
            ]
        }

        with open(os.path.join(self.token_info_path, 'tokens.json'), 'w') as outfile:
            json.dump(data, outfile, sort_keys=True, indent=4, separators=(',', ': '))      

if __name__ == "__main__":
    TokenInfoProvider(os.path.join("..", "tokens", "mainnet"), "https://raw.githubusercontent.com/rmeissner/crypto_resources/master/tokens/mainnet/icons/").write_tokens(2)