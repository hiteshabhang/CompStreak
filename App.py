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
st.set_page_config(page_title="Compstreak",layout='wide')
st.write('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

client =boto3.client('s3',aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'],region_name=st.secrets['AWS_DEFAULT_REGION'])

S3Bucket=st.secrets['S3Bucket']
@st.cache_resource()
def get_cred():

    print("Downlaoding cred From S3 ")
    credentialsS3=client.get_object(Bucket=S3Bucket,Key='credentials.json')
    return json.loads(credentialsS3['Body'].read())
    

credentials=get_cred()
with st.columns(3)[1]:
    authenticator = stauth.Authenticate(credentials,'adfdd','thiscookie16',cookie_expiry_days=0)
    Name,AuthStatus,UserName =authenticator.login("Login","main")


st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
</style>
""",unsafe_allow_html=True)
# Execute your app
st.markdown('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">', unsafe_allow_html=True)

# Navbar
st.markdown("""
<nav class="navbar fixed-top justify-content-center navbar-dark" style="background-color: #3498DB;">
  <a class="navbar-brand" target="_blank"> Compstreak</a>
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
def df_style(val):
    color ='green' if val>0 else 'red'
    return F'color:{color}'
def month_Picker():
    today=datetime.datetime.now().date()
    Months=pd.date_range('2023-11-01',str(today),freq="MS").strftime("%b-%Y").tolist()
    Months.reverse()
    #print(Months,today)
    return Months 

if AuthStatus ==False or st.session_state["authentication_status"] == False:
    st.toast("Username /Password is incorrect")
    st.error('Username/password is incorrect')
    

if AuthStatus==None or st.session_state["authentication_status"] ==None:
    pass
    
    
if AuthStatus==True or st.session_state["authentication_status"] ==True:
    st.toast('User {} successfully logged in.'.format(Name))
    if 'CID' not in st.session_state:
        st.session_state['CID']=Name
        
    client_id=st.session_state.CID
    UserContainer = st.container()
    with UserContainer:
        with st.sidebar:
            menu_o=['Home']
            selected =option_menu(
                menu_title ='Welcome {}'.format(client_id),
                options=menu_o,
                icons=['house','gear'],
                menu_icon='person-check',
                default_index=0,
                styles={"icon": {"color": "orange", "font-size": "10px"}}
                )
            authenticator.logout('Logout', 'main')
        if selected =='Home':
            tab1, tab2= st.tabs(["Ledger", "Trades"])
            
            with tab1:
                #Month=st.date_input("Month") 
                Mon=st.selectbox("Report For ",month_Picker(),index=0)
                MonD=datetime.datetime.strptime(Mon,"%b-%Y")
                
                #st.write(MonD)
                todaym =  d.strftime("%m") #MonD.month #datetime.datetime.now().month
                todayY =MonD.year #datetime.datetime.now().year
                
                FMonth =todaym
                FYear =todayY
                FClient=client_id
                SubFolder="Data"
                if 'MonthDf' in st.session_state and  'todaym' in st.session_state and st.session_state['todaym']==todaym:
                    print("This is From Session ")
                    #print(st.session_state['MonthDf'])
                
                else:    
                    
                    st.session_state['todaym']=todaym
                    print(todaym)
                    
                    LookupDir =SubFolder+"/"+str(FClient)+"/"+str(FYear)+"/"+str(FMonth) +"/"
                    
                    
                    TradeFiles=client.list_objects(Bucket=S3Bucket,Prefix=LookupDir)
                    
                    
                    print("========={}==========".format( LookupDir))
                    print("========={}==========".format(TradeFiles))
                    
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
                    
                    st.session_state['MonthDf']=data
             
                data =st.session_state['MonthDf']
                print("Data Read Completed")
                #Result=data
                #print(data.columns)
                Result =data.groupby('date',as_index=False).agg({'MTM G/L  ':'sum', 'Total Value ':'sum','Buy Val ':'sum','Sell Val ':'sum'})
                 
                #print(Result)
                
                Result['Profit'] =Result['MTM G/L  ']
                Result['Expenses']=  (Result['Total Value ']  * 0.00095)
                Result['Net Profit']= Result['Profit']-Result['Expenses']
                Colround =['Buy Val ','Sell Val ','Total Value ','Profit','Expenses','Net Profit']
                
                for i in Colround:
                    Result[i] =Result[i].round(2)
                
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
                st.dataframe (Result ,hide_index=True,use_container_width=True,height=(len(Result)+1)*35+3)
                #st.dataframe (Result.style.applymap(df_style,subset=['Profit']) ,hide_index=True,use_container_width=True,height=(len(Result)+1)*35+3)
                    
                                     
                    
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
                    print(LookupDirFileName)
                    s3_obj=client.get_object(Bucket=S3Bucket,Key=LookupDirFileName)
                    S3_data=s3_obj['Body'].read().decode('utf-8')
                    dataf=pd.read_csv(StringIO(S3_data))
                    st.dataframe(dataf ,hide_index=True,use_container_width=True)
                    
                    
                except Exception as e:
                    st.error("Data not Available for selected date.")
                    print(e)
                            
                    
