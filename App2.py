import streamlit as st
import streamlit_authenticator as stauth
from  streamlit_option_menu import option_menu
import pickle
from pathlib import Path
import json
import pandas as pd
import os
import datetime
from streamlit.components.v1 import html
import boto3
from io import StringIO

#from st_aggrid import AgGrid
#from stqdm import stqdm

client =boto3.client('s3',aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'],region_name=st.secrets['AWS_DEFAULT_REGION'])

S3Bucket=st.secrets['S3Bucket']


def get_cred():
    return client.get_object(Bucket=S3Bucket,Key='credentials.json')
    
credentialsS3 =get_cred()

credentials=json.loads(credentialsS3['Body'].read())
print("FROM s3 ",credentials)

st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
</style>
""",unsafe_allow_html=True)
# Execute your app
st.markdown('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">', unsafe_allow_html=True)

st.markdown("""
<nav class="navbar fixed-top justify-content-center navbar-dark" style="background-color: #3498DB;">

  <a class="navbar-brand" target="_blank"> CompSteak</a>
</nav>
""", unsafe_allow_html=True)
st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        height: 80% ;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        height: 80%
    }
    </style>
    """,
    unsafe_allow_html=True,
)


authenticator = stauth.Authenticate(credentials,'adfdd','nhhh',cookie_expiry_days=0)

Name,AuthStatus,UserName =authenticator.login("Login","main")



if AuthStatus ==False:
    st.toast("Username /Password is incorrect")
    st.error('Username/password is incorrect')
    

if AuthStatus ==None:
    pass
    
    
if AuthStatus ==True:
    
    st.toast('User {} successfully logged in.'.format(Name))
    if 'CID' not in st.session_state:
        st.session_state['CID']=Name
        
    client_id=st.session_state.CID
    UserContainer = st.container()
    with UserContainer:
        with st.sidebar:
            menu_o=['Home','Setting']
            selected =option_menu(
                menu_title ='Welcome {}'.format(client_id),
                options=menu_o,
                icons=['house','gear'],
                menu_icon='person-check',
                default_index=0,
                styles={"icon": {"color": "orange", "font-size": "10px"}}
                )
        if selected =='Home':
            tab1, tab2= st.tabs(["Ledger", "Trades"])
            
            with tab1:
                #Month=st.date_input("Month") 
                todaym =datetime.datetime.now().month
                todayY =datetime.datetime.now().year
                
                FMonth =todaym
                FYear =todayY
                FClient=client_id
                SubFolder="Data"
                
                
                print(todaym)
                
                LookupDir =SubFolder+"/"+str(FClient)+"/"+str(FYear)+"/"+str(FMonth) +"/"
                
                
                TradeFiles=client.list_objects(Bucket=S3Bucket,Prefix=LookupDir)
                
                
                print("========={}==========".format( LookupDir))
                #print("========={}==========".format(TradeFiles['Contents']))
                
                #Getting Files for monrh
                data=pd.DataFrame()
                    
                for Fkey in TradeFiles['Contents']:
                    ObjectName =Fkey['Key']
                    FileCSV =ObjectName.split(".")[-1]
                    if FileCSV=="csv":
                        
                        print(Fkey['Key'])
                        
                    
                        s3_obj=client.get_object(Bucket=S3Bucket,Key=Fkey['Key'])
                        S3_data=s3_obj['Body'].read().decode('utf-8')
                        t=pd.read_csv(StringIO(S3_data))
                        date_string=Fkey['Key'].split(".")[0]
                        date_string =date_string.split("/")[-1]
                        _=print("S3 {}".format(date_string))
                        format="%d%m%Y"
                        t['date']=datetime.datetime.strptime(date_string, format).strftime("%d-%m-%Y")
                        
                        data=pd.concat([data,t])
                
                               
             
                print("Data Read Completed")
                #Result=data
                #print(data.columns)
                Result =data.groupby('date',as_index=False).agg({'MTM G/L  ':'sum', 'Total Value ':'sum','Buy Val ':'sum','Sell Val ':'sum'})
                 
                #print(Result)
                Result['Profit'] =Result['MTM G/L  ']
                Result['Expenses']=  (Result['Total Value ']  * 0.00095)
                Result['Net Profit']= Result['Profit']-Result['Expenses']
                Result.loc['Total','date']="Total"
                Result.loc['Total','Profit'] =Result['Profit'].sum()
                Result.loc['Total','Expenses'] =Result['Expenses'].sum()
                Result.loc['Total','Net Profit'] =Result['Net Profit'].sum()
                Result.loc['Total','Total Value '] =Result['Total Value '].sum()
                Result.loc['Total','Buy Val '] =Result['Buy Val '].sum()
                Result.loc['Total','Sell Val '] =Result['Sell Val '].sum()
            
                ColSeq =['date','Buy Val ','Sell Val ','Total Value ','Profit','Expenses','Net Profit']
                Result =Result[ColSeq]
                
                #st.dataframe(Result)
                st.dataframe (Result ,hide_index=True)
                    
                                     
                    
            with tab2:
                try:
                    
                    d = st.date_input("Report For ")
                    print(d,type(d))
                    filename=""
                
                    Month= d.strftime("%m")
                    filename= d.strftime("%d%m%Y")
                    filename +=".csv"
                    FMonth =d.strftime("%m")
                    FYear =d.strftime("%Y")
                    FClient=client_id
                    SubFolder="Data"
                    
                    
                    
                    LookupDirFileName =SubFolder+"/"+str(FClient)+"/"+str(FYear)+"/"+str(FMonth) +"/"+filename
                    s3_obj=client.get_object(Bucket=S3Bucket,Key=LookupDirFileName)
                    S3_data=s3_obj['Body'].read().decode('utf-8')
                    dataf=pd.read_csv(StringIO(S3_data))
                    st.dataframe(dataf ,hide_index=True)
                    
                    
                except Exception as e:
                    print(e)
                            
                    