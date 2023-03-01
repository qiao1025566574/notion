import os
import requests
import pickle
from notion_client import Client
from pprint import pprint
from tabulate import tabulate
from calendar import isleap
from notion_client.helpers import iterate_paginated_api
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

def str2time(time_str):
    # 1h20m -> 80
    time = 0
    cur = ''
    for t in time_str:
        if t == 'h':
            cur = int(cur)
            time += cur * 60
            cur = ''
        elif t == 'm':
            cur = int(cur)
            time += cur
            cur = ''
        else:
            cur += t
    return time

def time2str(time):
    # 343 -> 5h43m
    h = int(time/60)
    m = time % 60
    if h == 0:
        return f'{m}m'
    elif m==0:
        return f'{h}h'
    elif h==0 and m==0:
        return '0m'
    else:
        return f'{h}h{m}m'

def get_page():
    # 利用notion api查询数据库数据
    notion = Client(auth=os.environ["NOTION_TOKEN"])

    block_list = []
    for block in iterate_paginated_api(
        notion.databases.query, database_id=database_id
    ):
        block_list.append(block)
    return block_list    

def get_table(ori_data_list):
    day_num = get_day_num()
    # 得到表格统计数据
    content_dict = {}
    count_dict = {}
    for ori_data in ori_data_list:
        date, number, time, content = ori_data
        if content in content_dict:
            content_dict[content] += time
            count_dict[content] += 1
        else:
            content_dict[content] = time
            count_dict[content] = 1
    total_print_list = [['内容', '总时间', '天数', '时间/天(有效)', '时间/天(总)']]
    for content in content_dict:
        time = content_dict[content]
        time_str = time2str(time)
        count = count_dict[content]
        avg_time = int(time/count)
        avg_time_str = time2str(avg_time)
        avg_day_time = int(time/day_num)
        avg_day_time_str = time2str(avg_day_time)
        total_print_list.append([content, time_str, count, avg_time_str, avg_day_time_str])
    print(tabulate(total_print_list, headers='firstrow', tablefmt='grid'))

def get_ori_data_from_list(block_list):
    # 得到原始数据
    ori_data_list = []
    for my_page in block_list:
        for page in my_page:
            this_dict = page['properties']
            date_number = this_dict['Number']['title'][0]['text']['content']
            date, number = date_number.split('-')
            if date == f'{year}{month:02}{day:02}':
                content = this_dict['Content']['select']['name']
                time_str = this_dict['Cost']['rich_text'][0]['text']['content']
                time = str2time(time_str)
                ori_data_list.append([date, number, time, content])
    return ori_data_list


def get_ori_data(my_page):
    # 得到原始数据
    ori_data_list = []
    for page in my_page['results']:
        this_dict = page['properties']
        date_number = this_dict['Number']['title'][0]['text']['content']
        date, number = date_number.split('-')
        content = this_dict['Content']['select']['name']
        time_str = this_dict['Cost']['rich_text'][0]['text']['content']
        time = str2time(time_str)
        ori_data_list.append([date, number, time, content])
    return ori_data_list

def get_day_num():
    if month in [1,3,5,7,8,10,12]:
        return 31
    elif month==2:
        if isleap(year):
            return 29
        else:
            return 28
    else:
        return 30

def plt_pie(ori_data_list, output_path='3.png'):
    # 画饼图
    content_dict = {}
    for ori_data in ori_data_list:
        date, number, time, content = ori_data
        if '-' in content:
            continue
        if content in content_dict:
            content_dict[content] += time
        else:
            content_dict[content] = time

    content_list, time_list = [], []
    for content in content_dict:
        time = content_dict[content]
        content_list.append(content)
        time_list.append(time)
    my_dpi = 96
    plt.figure(figsize=(720/my_dpi, 720/my_dpi), dpi=my_dpi)
    patches, texts = plt.pie(time_list, labels=content_list, pctdistance=1.2)
    for t in texts:
        t.set_size(12)
    total_time = sum(time_list)
    time_percent_list = [f'{time/total_time:.2%}' for time in time_list]
    labels = [f'{i} {j} ({v}分钟)' for i,j,v in zip(content_list, time_percent_list, time_list)]
    patches, labels, dummy = zip(*sorted(zip(patches, labels, time_list), key=lambda x:x[2], reverse=True))
    #plt.legend(patches, labels, loc='center', bbox_to_anchor=(-1, 0.5), fontsize=8)
    plt.legend(patches, labels, loc='best', fontsize=8)
    plt.title(f'{year}年{month:2}月{day:02}日时间分类占比图', fontsize=20)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.clf()
    print(f'Pie picture has been saved to path:{output_path}.')

def main():
    pickle_filepath = f'./time/{year}_{month}_{day}_block.pickle'
    force_download = False
    if os.path.exists(pickle_filepath) and not force_download:
        pickle_file = open(pickle_filepath, 'rb')
        block_list = pickle.load(pickle_file)
        pickle_file.close()
        print(f'load block_list from {pickle_filepath}')
    else:
        block_list = get_page()
        pic = open(pickle_filepath, 'wb')
        pickle.dump(block_list, pic)
        pic.close()
        print(f'load from url')
        print(f'save block_list to {pickle_filepath}')
    ori_data_list = get_ori_data_from_list(block_list)
    with open(f'./time/{year}_{month}_{day}_content.txt', 'w') as fw:
        for ori_data in ori_data_list:
            for data in ori_data:
                fw.write(str(data))
                fw.write(' ')
            fw.write('\n')
    plt_pie(ori_data_list, f'./time/{year}{month:02}{day:02}_pie.png')

if __name__=='__main__':
    year, month, day = 2023, 2, 27
    database_id = '8d19ff252abf43969d12ab1b9d99b137'
    main()
    print('Done.')
