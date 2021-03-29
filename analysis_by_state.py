#   https://data.census.gov/cedsci/profile?q=United%20States&g=0100000US

from os import mkdir
from os.path import exists, sep

import pandas as pd

if not exists('state'):
    mkdir('state')

def state_data(state_name,category,show_estimate):
    assert category in ('employment','housing')
    state_folder=sep.join(('state',state_name.lower()))
    if not exists(state_folder):
        mkdir(state_folder)
    filename=sep.join((state_folder,category+'.csv'))
    if not exists(filename):
        class FileError(Exception):
            def __init__(self,message):
                self.message=message
        message=(\
            '',\
            'The file below was not found:',\
            filename,\
            ''
            )
        message='\n\n'.join(message)
        state_folder=filename[:filename.index(category)-1]
        table_name=('DP03' if category == 'employment' else 'DP04')
        if not exists(state_folder):
            mkdir(state_folder)
        link='https://data.census.gov/cedsci/table?q=ACSDP1Y2019.%s%20United%20States&tid=ACSDP1Y2019.%s&moe=false&hidePreview=true'%(table_name,table_name)
        instructions=(\
            '1. Follow this link:\n\n%s\n'%link,\
            '2. Filter to state of choice',\
            '3. Filter to counties within %s'%state_name.capitalize(),\
            '4. Click ``Excel\'\' and download as .csv',\
            '5. Relabel as ``%s.csv\'\''%category,\
            '6. Insert ``%s.csv\'\' into ``%s\'\''%(category,state_folder),\
            '7. Rerun script.'
            )
        instructions='\n'.join(instructions)
        message+=instructions
        raise FileError(message)
    data=pd.read_csv(filename,index_col=0)
    if show_estimate:
        start=0
    else:
        start=1
    data=data.iloc[:,start::2]
    new_columns=()
    for column in data.columns:
        if state_name.capitalize() not in column:
            class CountyError(Exception):
                def __init__(self,message):
                    self.message=message
            stop=column.index('!!')
            if state_name not in ('louisiana','alaska'):
                start=column.index(' County, ')
                locations=(\
                    column[:start],\
                    column[start+len(' County, '):stop],\
                    state_name.capitalize()
                    )
                message='\n\nThe County of %s is in %s, not %s.'%locations
            else:
                start=column.index(', ')
                locations=(
                    column[:start],\
                    column[start+len(', '):stop],\
                    state_name.capitalize()
                    )
                message='\n\n%s is in %s, not %s'%locations
            raise CountyError(message)
        if ' County' in column:
            column_name=column[:column.index(' County')]
        else:
            column_name=column[:column.index('!!')]
        new_columns+=(column_name,)
    data.columns=new_columns
    return data

def data_by_county(state_name,category,show_estimate):
    data=state_data(state_name,category,show_estimate)
    indices=list(data.index)
    sheet_indices=()
    for n,name in enumerate(indices):
        if name.strip() == name:
            sheet_indices+=(n,)
            if len(name)>31:
                name=name[:31]
        indices[n]=name.strip()
    data.index=indices
    sheet_dict={}
    for n,index in enumerate(sheet_indices):
        if index is sheet_indices[-1]:
            break
        sheet_name=indices[index]
        start=index+1
        stop=sheet_indices[n+1]
        sheet=data.iloc[start:stop,:]
        sheet_dict[sheet_name]=sheet
    return sheet_dict

def numeric_converter(state_name,category,show_estimate):
    data_sheets=data_by_county(state_name,category,show_estimate)
    for data in data_sheets.values():
        for column in data.columns:
            numerical_values=[]
            for value in data.loc[:,column].values:
                rtext=''
                divisor=1
                delimiters=',','%','.'
                if '%' in value:
                    divisor=1000
                for d in delimiters:
                    value=value.replace(d,'')
                if value.isnumeric():
                    value=float(value)
                    value/=divisor
                numerical_values.append(value)
            data.loc[:,column]=numerical_values
    return data_sheets

def xl_data_writer(state_name,category,show_estimate=True):
    data_sheets=numeric_converter(state_name,category,show_estimate)
    if show_estimate:
        suffix='_estimate'
    else:
        suffix='_percent'
    category+=suffix+'.xlsx'
    filename=sep.join(('state',state_name.lower(),category))
    with pd.ExcelWriter(filename,mode='w') as writer:
        for sheet_name,sheet in data_sheets.items():
            sheet.transpose().to_excel(writer,sheet_name=sheet_name)

def compile_data_into_excel(state_name):
    for category in ('housing','employment'):
        for boolean in (True,False):
            xl_data_writer(state_name,category,show_estimate=boolean)

if __name__ == '__main__':
    compile_data_into_excel('ohio')
