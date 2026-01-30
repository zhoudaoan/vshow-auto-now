# import requests
#
#
# data = {"id":37146604,
#         "action_intro":1,
#         "coins":1,
#         "approval_id":"",
#         "menu_id":0}
#
# response = requests.post(
#     json=data,
#     url = 'https://test3397-admin.v.show/user/add-coin',
#     headers={"Cookie":"_ga=GA1.1.178593440.1757054696; _ga_VHE7RWKHR2=GS2.1.s1757303337$o2$g0$t1757303337$j60$l0$h0; _csrf=fd66cefc627b19b1d1105803a630f68ecfcc2fe525971cf721fca574f6b419f8a%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22vHzhSJ-oPcLLN-WUipSkTVjiCHSeBHxE%22%3B%7D; PHPSESSID=gcv7ms0g64uitdkj80pgsqsio5"})
# print(response.json())
from Vshow_TOOLS.random_str import generate_random_chinese

print(generate_random_chinese(51))








