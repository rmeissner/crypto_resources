import json
import os

prio_tokens = [
    '0x6810e776880C02933D47DB1b9fc05908e5386b96', # GNO
    '0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359', # DAI
]
token_path = os.path.join('..', 'tokens', 'mainnet')

def key_extractor(tokenMeta):
    token = tokenMeta['token']
    try:
        prio_index = prio_tokens.index(token['address'])
    except: 
        prio_index = 10000000
    return (prio_index, token['name'].lower())

with open(os.path.join(token_path, 'tokens.json')) as f:
    tokens = json.load(f)     

tokens['results'] = sorted(filter(lambda item: item['token']['symbol'] != '0x', tokens['results']) , key=key_extractor)
tokens['count'] = len(tokens['results'])

with open(os.path.join(token_path, 'tokens.json'), 'w') as outfile:
    json.dump(tokens, outfile, sort_keys=True, indent=4, separators=(',', ': '))