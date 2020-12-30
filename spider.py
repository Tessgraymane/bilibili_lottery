import multiprocessing
import requests
import os
import zipfile
from bs4 import BeautifulSoup
import re
import shutil
import time


def spider():
    all_links = []
    year_dict = [2004, 2006, 2008, 2009, 2011,  2013, 2014, 2015, 2017, 2018]
    for year in year_dict:
        del_list = []
        url = f"http://www.piano-e-competition.com/midi_{year}.asp"

        req = requests.get(url)
        res = req.text

        bs4 = BeautifulSoup(res, "html.parser")
        all_a_tag = bs4.find_all("a")

        # 2011年前和2011年后采用不同处理方案
        if year > 2011:
            for each in all_a_tag:

                # 查看其string属性即可
                if (each.string != "STANDARD MIDI"):
                    del_list.append(each)

            for each in del_list:
                all_a_tag.remove(each)

            for each in all_a_tag:
                all_links.append(
                    "http://www.piano-e-competition.com"+each.attrs["href"])

        else:
            for each in all_a_tag:
                # 使用try防止该标签没有href属性
                try:
                    if (re.match(".*EnhancedMIDI.*", each.attrs["href"]) == None):
                        del_list.append(each)
                except KeyError:
                    del_list.append(each)

            for each in del_list:
                all_a_tag.remove(each)

            for each in all_a_tag:
                all_links.append(
                    "http://www.piano-e-competition.com"+each.attrs["href"])
        print(f"Find {len(all_a_tag)} files in year {year}")

    with open("File_URL.txt", "w+") as fp:
        for each_url in all_links:
            fp.writelines(each_url+"\n")

# CPU核心数测试


def CPU_test():
    return multiprocessing.cpu_count()

# 找到文件名


def get_name(string):
    cnt = 0
    location = 0
    for each in list(string):
        if(each == '/'):
            location = cnt
        cnt += 1
    return string[location+1:]

# 读取文件列表


def read_file(Path, mode):
    with open(Path, mode) as fp:
        all_links = fp.readlines()
    return all_links

# 解压


def unzip(file):
    if os.path.isdir("./data_unzip"):
        pass
    else:
        os.mkdir("./data_unzip")
    zip_file = zipfile.ZipFile(file)
    for name in zip_file.namelist():
        zip_file.extract(name, "./data_unzip/")
    zip_file.close()

# 下载处理


def print_process(progress, mission):
    cnt = 0
    while cnt < 100:
        print("",end="")
        print(f"\r {'=' * cnt}>{cnt}%",end="")
        cnt += 1
    print("")

# 下载文件


def download_zip(all_links, task_begin, task_finish):
    cnt = 0
    url = all_links[task_begin:task_finish]
    for each_url in url:
        req = requests.get(each_url[:-1])
        with open("./data/" + get_name(each_url[:-1]), "wb") as fp:
            # 写入文件
            fp.write(req.content)
            # 解压文件
            unzip("./data/" + get_name(each_url[:-1]))
        cnt += 1
        print(f"Process {os.getpid()}:file {get_name(each_url[:-1])} download finish")

# 错误文件夹处理


def wrong_file_process():
    file_list = os.listdir("./data_unzip")
    for each in file_list:
        # 如果存在解压出的文件夹
        if(os.path.isdir("./data_unzip/"+each)):
            wrong_files = os.listdir("./data_unzip/"+each)
            for filename in wrong_files:
                shutil.copyfile("./data_unzip/" + each + "/" +
                                filename, "./data_unzip/" + filename)
            os.system("rm -rf ./data_unzip/" + each)


# 主进程任务
if __name__ == "__main__":
    # 爬取目录
    spider()
    print("\n\n--------------------------Spider end,Downloader begin------------------------------\n\n")
    CPU_core_number = CPU_test()
    if os.path.isdir("./data"):
        pass
    else:
        os.mkdir("./data")
    all_links = read_file("./File_URL.txt", "r")
    # 创建进程池
    Pool = multiprocessing.Pool(processes=CPU_core_number)
    # 任务分配
    task_number = len(all_links) // CPU_core_number + 1
    begin = 0
    for cnt in range(CPU_core_number):
        Pool.apply_async(download_zip, args=(
            all_links, begin, begin + task_number))
        begin += task_number
    Pool.close()
    Pool.join()
    print("\n\n--------------------------Downloader end,Wrong files fixing------------------------------\n\n")
    # 错误处理
    wrong_file_process()
