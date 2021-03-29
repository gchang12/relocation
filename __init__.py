#   https://data.census.gov/cedsci/profile?q=United%20States&g=0100000US

from os.path import exists,sep
from os import mkdir, walk

import pandas as pd

renting='renting.csv'
sunset_times='sunset-times.csv'
employment='employment.csv'

def us_data(file,percent=False):
    data=pd.read_csv(file,index_col=0)
    n=(1 if percent else 0)
    x=data.iloc[:,n:102:2]
    new_labels=(m[:m.index('!!')] for m in x.columns)
    x.columns=new_labels
    return x.transpose()

def section_list(*args):
    data=us_data(*args)
    l=tuple(data.columns)
    sections=(u for u in l if u.isupper())
    d={}
    for section in sections:
        d[section]=l.index(section)
    return d


def save_table(file,df,folder):
    destination=('.',folder)
    save_path=sep.join(destination)
    if not exists(save_path):
        mkdir(save_path)
    save_path+=sep+file+'.csv'
    df.to_csv(save_path)


def save_section_data(folder,*args):
    sl=section_list(*args)
    data=us_data(*args)
    start=0
    file_num=tuple(sl.items())
    for n in range(len(file_num)):
        file1,num1=file_num[n]
        suffix=('_percent' if args[-1] else '_estimate')
        file1+=suffix
        if n is not len(file_num)-1:
            file2,num2=file_num[n+1]
            x=data.iloc[:,num1+1:num2]
        else:
            x=data.iloc[:,num1+1:]
            break
        save_args=(file1,x,folder)
        save_table(*save_args)


def save_rent_and_employment_data(show_percent):
    def save_data(file,folder):
        args=(file,show_percent)
        save_section_data(folder,*args)
    global renting, employment
    save_data(renting,'renting')
    save_data(employment,'employment')


#   Excel merge script from here onwards


def convert_to_percent(num_list):
    new_list=[]
    for num in num_list:
        if type(num) == str:
            if '%' in num:
                perc_loc=num.index('%')
                num=num[:perc_loc]
                num=float(num)
        new_list.append(num)
    return new_list


def format_percent(data):
    d={}
    for column in data.columns:
        cell0=data[column][0]
        if type(cell0) != str:
            continue
        if '%' in cell0:
            d[column]="{:.2%}"
    return d


def has_no_duplicates(ls):
    x=ls
    s=set(ls)
    return len(x) == len(s)


def get_new_index(data):
    old_index=data.columns
    new_index=[]
    for title in old_index:
        title=title.strip()
        new_index.append(title)
    newer_index=[]
    for title in new_index:
        N=tuple(new_index).count(title)
        if N > 1:
            d=(title+str(n) for n in range(N))
            for t in d:
                if t not in newer_index:
                    title=t
                    break
        newer_index.append(title)
    return newer_index


def stripped_data(file_loc,**read_kw):
    data=pd.read_csv(file_loc,**read_kw)
    data.columns=get_new_index(data)
    to_perc=format_percent(data)
    data=data.apply(convert_to_percent)
    data=data.style.format(to_perc)
    return data


def csv_data_compiler(stat_type,data_type):
    assert data_type in ('estimate','percent')
    assert stat_type in ('renting','employment')
    data_files={}
    read_kw={
        'sep':',',\
        'index_col':0,\
        'header':0,\
        'thousands':','
        }
    if data_type == 'estimate':
        start=0
    elif data_type == 'percent':
        start=1
    for root,folder,files in walk('.'):
        if root == '.':
            continue
        if stat_type not in root:
            continue
        file_list=files[start::2]
        for file in file_list:
            file_loc=sep.join([root,file])
            data=stripped_data(file_loc,**read_kw)
            key=file[:file.index('_'+data_type)]
            if '(' in key:
                if stat_type == 'renting':
                    key_start=key.index('(')
                    key_stop=key.index(')')+1
                    key=key[key_start:key_stop]
                else:
                    key=key[:key.index(' (')]
            elif key == 'YEAR HOUSEHOLDER MOVED INTO UNIT':
                key='YEAR HOUSEHOLDER MOVED IN'
            data_files[key]=data
    return data_files

def csv_data_merger(folder,*args):
    data_files=csv_data_compiler(*args)
    data_folder=sep.join(('.',folder))
    data_name='_'.join(args)+'.xlsx'
    data_name=sep.join((data_folder,data_name))
    if not exists(folder):
        mkdir(folder)
    with pd.ExcelWriter(data_name,mode='w') as writer:
        for name,file in data_files.items():
            kw={
                'sheet_name':name
                }
            file.to_excel(writer,**kw)


def merge_all_data(folder='xl_output'):
    data_types='estimate','percent'
    stat_types='employment','renting'
    for dtype in data_types:
        for stype in stat_types:
            args=stype,dtype
            csv_data_merger(folder,*args)

if __name__=='__main__':
    filename='2019_NIBRS_NATIONAL_MASTER_FILE_ENC_STATIC.txt'
    with open(filename,'r') as rFile:
        for line in rFile.readlines():
            print(line)
            break
