# NFT USER ANALYSIS MODULE
# CREATED BY Z.CAO 21/MAR/2022

from utils import Alchemy_api, NFTRecord, Oracle_Demo
import numpy as np

def main():
    user_id = "0x17Be2881d37f878520E46082fF3d0AF739aE392B"
    oracle = Oracle_Demo(user_id)
    oracle.get_nft_collections()
    oracle.get_avg_hold_time()
    oracle.get_avg_profit()
    oracle.get_user_patterns()

if __name__ == '__main__':
    main()
