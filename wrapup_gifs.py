import os
from dotenv import load_dotenv
import json
from urllib import parse, request
import random

search_winner = ["winner", "touchdown dance", "win", "nfl touchdown"]
search_loser = ["loser", "rock bottom", "fail", "you suck", "nfl blooper"]
gif_limit = 10

load_dotenv()
api_key = os.getenv("GIPHY_API_KEY")

url = "http://api.giphy.com/v1/gifs/search"

sw_index = 0 
sl_index = 0 
sm_index = 0
# params = parse.urlencode({
#   "q": "ryan gosling",
#   "api_key": api_key,
#   "limit": "2"
# })
# 
# with request.urlopen("".join((url, "?", params))) as response:
#   data = json.loads(response.read())

# # print(json.dumps(data, sort_keys=True, indent=4))
# print(data['data'][0]['url'])
# print(data['data'][1]['url'])

def get_winner_gif():
    sw_index = random.randint(0,len(search_winner)-1)
    index = random.randint(0,gif_limit-1)
    params = parse.urlencode({
      "q": search_winner[sw_index],
      "api_key": api_key,
      "limit": gif_limit
    })
    with request.urlopen("".join((url, "?", params))) as response:
      data = json.loads(response.read())

    # return data['data'][0]['url']
    return data['data'][index]['images']['original']['url']

def get_loser_gif():
    sl_index = random.randint(0,len(search_loser)-1)
    index = random.randint(0,gif_limit-1)
    params = parse.urlencode({
      "q": search_loser[sl_index],
      "api_key": api_key,
      "limit": gif_limit
    })
    with request.urlopen("".join((url, "?", params))) as response:
      data = json.loads(response.read())

    # return data['data'][0]['url']
    return data['data'][index]['images']['original']['url']
