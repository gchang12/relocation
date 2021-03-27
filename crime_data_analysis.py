#   https://crime-data-explorer.app.cloud.gov/

import pandas as pd
from os import sep, mkdir, walk
from os.path import exists

def names_in(column):
    filename='estimated_crimes_1979_2019.csv'
    crime_data=pd.read_csv(filename)
    names=crime_data.loc[:,column]
    names.dropna(inplace=True)
    names.drop_duplicates(inplace=True)
    if column == 'state_name':
        names=names.to_list()+['TOTAL']
    else:
        names=names.to_list()
    return names

def parsed_data(state_or_year):
    filename='estimated_crimes_1979_2019.csv'
    crime_data=pd.read_csv(filename)
    crime_data.loc[:,'state_name'].fillna(value='TOTAL',inplace=True)
    if type(state_or_year) == int:
        filter_by='year'
        new_index='state_name'
    elif type(state_or_year) == str:
        filter_by='state_name'
        new_index='year'
    if state_or_year not in crime_data[filter_by].values:
        return
    new_data=crime_data[crime_data[filter_by] == state_or_year]
    new_index=list(new_data[new_index])
    new_data.index=new_index
    new_data=new_data.drop(axis=1,labels=['caveats','state_abbr','year','state_name'])
    new_data.dropna(inplace=True,axis=1,how='all')
    return new_data

def percent_data(state_or_year):
    est_data=parsed_data(state_or_year)
    for column in est_data.columns:
        if column == 'population':
            continue
        est_data[column]=est_data[column]/est_data['population']
    est_data=est_data.drop(axis=1,labels='population')
    return est_data

def make_data_folders():
    root='crime_data'
    folders='','by_year','by_state','national'
    for folder in folders:
        folder=sep.join((root,folder))
        if not exists(folder):
            mkdir(folder)

def save_crime_data(state_or_year,national=False,crime_data=None):
    if crime_data is None:
        crime_data=percent_data(state_or_year)
    folder='crime_data'
    if type(state_or_year) == int:
        subfolder='by_year'
        if national:
            subfolder='national'
        filename=str(state_or_year)
    elif type(state_or_year) == str:
        subfolder='by_state'
        filename=state_or_year
    filename+='.csv'
    folder=sep.join((folder,subfolder))
    filename=sep.join((folder,filename))
    crime_data.to_csv(filename)

def save_all_data():
    columns='state_name','year'
    for column in columns:
        for name in names_in(column):
            save_crime_data(name)

def excel_data(folder):
    dirnames=['.','crime_data',folder]
    search_dir=sep.join(dirnames)
    dirnames[-1]=folder+'.xlsx'
    save_dir=sep.join(dirnames)
    for dirpath,dirname,filenames in walk(search_dir):
        with pd.ExcelWriter(save_dir,mode='w') as writer:
            for filename in filenames:
                sheet_name=filename[:-4]
                filename=sep.join((search_dir,filename))
                data=pd.read_csv(filename,index_col=0)
                data.to_excel(writer,sheet_name=sheet_name)

def national_data(year):
    assert type(year) == int
    crime_data=parsed_data(year)
    last_row=crime_data.loc['TOTAL',:]
    for row_name in crime_data.index:
        if row_name == 'TOTAL':
            continue
        crime_data.loc[row_name,:]/=last_row
    return crime_data

def save_nat_data():
    for year in names_in('year'):
        save_crime_data(year,national=True,crime_data=national_data(year))

if __name__ == '__main__':
    excel_data('national')
