# NFT USER ANALYSIS MODULE
# CREATED BY Z.CAO 21/MAR/2022
import requests
from web3 import Web3, HTTPProvider
import json
import time
import numpy as np

# Init Web3 API
apiKey = "fY-K6btKj7v6tigwN1A2zoF3nYqF-GFq"
baseURL = 'https://eth-mainnet.alchemyapi.io/v2/' + apiKey
web3 = Web3(Web3.HTTPProvider(baseURL))

class Oracle_Demo(object):
    def __init__(self, user_id):
        self.data = Alchemy_api(user_id)

    def get_nft_collections(self):
        print('This account owned %d NFTS' % len(self.data.nfts))

    def get_avg_hold_time(self):
        holds_nft = []
        sold_nft = []
        for key, values in self.data.nfts.items():
            if values.sold_flag:
                sold_nft.append(values.hold_time)
            holds_nft.append(values.hold_time)
        sold_times = np.array(sold_nft) / 60 / 60 / 24
        avg_sold_time = np.mean(sold_times)
        avg_hold_time = np.mean(np.array(holds_nft) / 60 / 60 / 24)
        print('Sold NFT Avg Hold Time: %.4f Days' % avg_sold_time)
        print('All NFT Avg Hold Time: %.4f Days' % avg_hold_time)

    def get_avg_profit(self):
        profits = []
        asset = ''
        for key, values in self.data.nfts.items():
            if values.sold_flag:
                try:
                    asset = str(values.price_asset_in)  # TODO: Exchange ETH/USDT etc.
                    profits.append(values.price_value_out - values.price_value_in)
                except:
                    pass
        avg_profit = np.mean(np.array(profits))
        print('Avg Profit: %.4f %s' % (avg_profit, asset))

    def get_user_patterns(self):
        if len(self.data.nfts) > 5:
            print("Rich Man")
        else:
            print("Poor Man")


class Alchemy_api(object):
    """ API Request from Alchemy
        :param User_Account: User Hash ID of Ethereum
        :return Analysis of one account
    """

    def __init__(self, user_account):
        global baseURL
        self.account = user_account
        self.baseURL = baseURL
        self.headers = {'Content-Type': 'application/json'}
        self.params = {'chain': 'eth', 'format': 'decimal'}
        self.in_data = list()
        self.out_data = list()
        self.nfts = dict()
        self.transactions_in = dict()
        self.avg_hold_time: float = 0
        self.tag: str = ''
        try:
            self._get_transcations_data()
        except ValueError:
            print('Request Error... Try Again')
            time.sleep(1)
            self._get_transcations_data()
        self._anal_transactions()
        self._post_process()

    def _get_transcations_data(self):
        request_data_in = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "alchemy_getAssetTransfers",
            "params": [
                {
                    "fromBlock": "0x0",
                    "toAddress": self.account,
                }]
        }

        response_in = requests.post(url=self.baseURL, params=self.params,
                                    headers=self.headers, data=json.dumps(request_data_in))
        time.sleep(1)
        request_data_out = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "alchemy_getAssetTransfers",
            "params": [
                {
                    "fromBlock": "0x0",
                    "fromAddress": self.account,
                }]
        }

        response_out = requests.post(url=self.baseURL, params=self.params,
                                     headers=self.headers, data=json.dumps(request_data_out))

        try:
            self.in_data = response_in.json()['result']['transfers']
            self.out_data = response_out.json()['result']['transfers']
        except:
            print(response_in.json())
            print(response_out.json())
            raise ValueError("Request Error")

    def _generate_nft_id(self, addr, tid):
        return str(addr) + '+' + str(tid)

    def _anal_transactions(self):
        """
            This is only a Demo here
        """
        for _item in self.in_data:
            if _item['erc721TokenId'] or _item['erc1155Metadata']:  # Identify A NFT transaction
                _record = NFTRecord(self._generate_nft_id(_item['rawContract']['address'], _item['tokenId']))
                _record.update_info(_item['blockNum'], _item['hash'])
                self.nfts[_item['hash']] = _record
            else:  # Coin Exchange, Mark the Hash
                self.transactions_in[_item['hash']] = _item

        for _item in self.out_data:
            if _item['hash'] in self.nfts:  # Find Same Hash, Update Price
                self.nfts[_item['hash']].update_price(_item['value'], _item['asset'])

            if _item['erc721TokenId'] or _item['erc1155Metadata']:  # sold this NFT
                for k, v in self.nfts.items():
                    if v.id == self._generate_nft_id(_item['rawContract']['address'], _item['tokenId']):
                        try:
                            sold_value = self.transactions_in[_item['hash']]['value']
                            sold_asset = self.transactions_in[_item['hash']]['asset']
                            self.nfts[k].sold(_item, sold_value, sold_asset)
                        except:  # Cannot Find Corresponding Transaction
                            sold_value = 0
                            sold_asset = 'ETH'
                            self.nfts[k].sold(_item, sold_value, sold_asset)

    def _post_process(self):
        for k, v in self.nfts.items():
            v.update_hold_time()

class NFTRecord(object):
    """
        :param NFT Collection ID
    """

    def __init__(self, id):
        self.id = id
        self.price_value_in: float = 0
        self.price_asset_in: str = ''
        self.price_value_out: float = 0
        self.price_asset_out: str = ''
        self.blockNum = ''
        self.hash = ''
        self.sold_flag = False
        self.sold_info = dict()
        self.hold_time = 0

    def update_info(self, blockNum, hash):
        self.blockNum = blockNum
        self.hash = hash

    def update_price(self, price_value_in, price_asset_in):
        self.price_value_in = price_value_in
        self.price_asset_in = price_asset_in

    def sold(self, sold_info, sold_value, sold_asset):
        self.sold_flag = True
        self.sold_info = sold_info
        self.price_value_out = sold_value
        self.price_asset_out = sold_asset

    def update_hold_time(self):  # This is a demo
        if self.sold_flag:
            time_in = web3.eth.get_block(int(self.blockNum, 16))['timestamp']
            time_out = web3.eth.get_block(int(self.sold_info['blockNum'], 16))['timestamp']
            self.hold_time = time_out - time_in
        else:
            time_in = web3.eth.get_block(int(self.blockNum, 16))['timestamp']
            time_out = web3.eth.get_block('latest')['timestamp']
            self.hold_time = time_out - time_in

if __name__ == '__main__':
    # user_id = "0x84c59727820bd96B4c1b9ce2D963936Df8B6872b"
    # user_id = "0x90857dd31AEF29d288C1F8c14222F5cBd1Bbb19a"
    pass

