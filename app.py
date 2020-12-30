#导入库
import requests 
import json
import random
from flask import Flask,render_template, request


#基本函数______________________________________________________
def add_dict(d1,d2):
    result = d1.copy()
    result.update(d2)
    return result

#生成随机数部分
def random_number(limit, number):
    lim = range(0,limit)
    random_list = random.sample(lim, number)
    return random_list
#基本函数finish_________________________________________________




#mid号查用户名
def mid2username(mid):
    url = f"https://api.bilibili.com/x/space/acc/info?mid={mid}&jsonp=jsonp"
    req = requests.get(url)
    name = json.loads(req.text)["data"]["name"]
    return name

#反查AV号
def BV2AV(bv_number):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_number}"
    req = requests.get(url)
    return json.loads(req.text)["data"]["aid"]
    

#全部评论
def video_floor(bv_number):
    av_number = BV2AV(bv_number)
    page = 1
    url = f"https://api.bilibili.com/x/v2/reply?&type=1&pn={page}&oid={av_number}"
    req = requests.get(url)
    json_file = json.loads(req.text)
    all_comment = []
    # 总评论条数
    comment_number = json_file["data"]["page"]["count"]
    # 计算评论页数

    comment_page = comment_number // 20 + 1
    for page in range(1, comment_page + 1):
        url = f"https://api.bilibili.com/x/v2/reply?&type=1&pn={page}&oid={av_number}"
        req = requests.get(url)
        json_file = json.loads(req.text)
        comments = json_file["data"]["replies"]
        all_comment = all_comment + comments
    return all_comment

#检查MID防止重复
def check_mid(all_comment):
    MID_list = []
    for each_comment in all_comment:
        mid_tmp = each_comment["member"]["mid"]
        if(MID_list.count(mid_tmp) == 0):
            MID_list.append(mid_tmp)
    return MID_list


#检查某人是否关注了UP
def check_subscibe(mid, up_mid):
    print(f"正在检查{mid}是否关注了{up_mid}")
    subscribe_list = []
    flag = False
    page = 1
    url = f"https://api.bilibili.com/x/relation/followings?vmid={mid}&pn={page}&ps=20"
    req = requests.get(url)
    subscribe_number = json.loads(req.text)["data"]["total"]
    page_number = subscribe_number // 50 + 1
    for page in range(1, min(page_number + 1, 5)):
        url = f"https://api.bilibili.com/x/relation/followings?vmid={mid}&pn={page}&ps=50"
        req = requests.get(url)
        json_tmp = json.loads(req.text)
        if(json_tmp["data"]["list"] != None):
            subscribe_list_tmp = json_tmp["data"]["list"]
            subscribe_list += subscribe_list_tmp
    for each_subscribe in subscribe_list:
        if(each_subscribe["mid"] == up_mid):
            flag = True
            return flag
    return flag


#抽奖
def calculate(bv, number, up_mid, check):
    #获得评论数量
    all_comment = video_floor(bv)
    #检查MID
    MID_list = check_mid(all_comment)
    false_list = []
    if (check == "on"):
        #检查是否关注
        for each,count in zip(MID_list, range(len(MID_list))):
            result = check_subscibe(each, up_mid)
            if(result == False):
                false_list.append(count)
        
        #从列表中删掉没有关注的人
        for each in false_list:
            del MID_list[each]

    lucky = []
    #如果number过大就直接返回出错
    if(int(number) >= len(MID_list)):
        return ['抽奖人数过多哦']
    #随机抽取幸运观众
    
    for each in random_number(len(MID_list), int(number)):
        lucky.append(mid2username(MID_list[each]))
    return lucky


app = Flask(__name__)

@app.route("/", methods=["GET"])
def root():
    #获得参数
    bv = request.args.get("bv")
    number = request.args.get("number")
    check = request.args.get("check")
    check = "off"
    up_mid = request.args.get("mid")
    if(bv == None or number == None or check == None):
        return render_template("index.html")
    else:
        print(bv, number, up_mid, check)
        try:
            lucky = calculate(bv, number, up_mid, check)
            print(lucky)
        except KeyError as e:
            print(e)
            return render_template("index.html", lucky=["输入信息有误哦"])
        return render_template("index.html", lucky=lucky)
if __name__ == "__main__":
    app.run(debug=True)