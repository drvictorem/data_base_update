import socket
from pandas import DataFrame
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import mariadb
import sys
import json

print("Start")

def checkData (current_data_from_DB, new_data_from_axxon):
    parsed  = current_data_from_DB[0]
    BoolData = {'ip': parsed[0] == new_data_from_axxon[0] ,'status': parsed[1] == new_data_from_axxon[1], 'name':parsed[2] == new_data_from_axxon[2], 'vendor':parsed[3] == new_data_from_axxon[3]}
    # BoolData = ({parsed[0] == new_data_from_axxon[0], parsed[1] == new_data_from_axxon[1] , parsed[2] == new_data_from_axxon[2], parsed[3] == new_data_from_axxon[3])
    DB_data =  {'ip': parsed[0], 'status': parsed[1], 'name':parsed[2], 'vendor':parsed[3]}
    axxon_data = {'ip': new_data_from_axxon[0],'status': new_data_from_axxon[1], 'name':new_data_from_axxon[2], 'vendor':new_data_from_axxon[3]}
    checked = ({'DB':DB_data, 'AXXON':axxon_data, 'BOOL':BoolData})
    return checked

try:
    conn = mariadb.connect(
        user="admin",
        password="1qazxsw2",
        host="localhost",
        port=3306,
        database="cam_test"
    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

cur = conn.cursor()
print("conn OK!")


url = 'http://10.0.0.49/camera/list' #сервер axxon
response = requests.get(url, auth=HTTPBasicAuth('nikita', '139602215n'))
data = response.json()

print("axxon")
data_cam = []
for counter in range(0,len(data['cameras'])):
    new_name = data['cameras'][counter]['displayName']
    new_ip = data['cameras'][counter]['ipAddress']


    try:
        url_ip = "http://"+new_ip+"/doc/page/login.asp?_1584422935045"
        r = requests.get(url_ip,timeout=2)
        new_status='online'
        s = BeautifulSoup(r.content, 'html.parser')
        first_div = s.find('div',{"class" : "footer"})
        if first_div != None:
          new_vendor='Hikvision'
        else:
          new_vendor='dahua'
    except requests.exceptions.ConnectTimeout:
      new_status='offline'
    except requests.exceptions.ConnectionError:
      new_status='offline'

    cur.execute("SELECT ip,status,name,vendor FROM cam_list WHERE ip = '%s'"%(str(new_ip)))

    current_data_from_DB = cur.fetchall() #текущие данные
    new_data_from_axxon=(new_ip, new_status, new_name, new_vendor)#новые данные
    #print(current_data_from_DB)
    #print(new_data_from_axxon)
    checkedData = checkData(current_data_from_DB, new_data_from_axxon)


    if False in checkedData['BOOL'].values():
         keys = checkedData['BOOL'].keys()

         for index in keys:
             if checkedData['BOOL'][index] == False:
                checkedData['AXXON'][index]
                sql="UPDATE cam_list SET " + index + " = " + "'" + checkedData['AXXON'][index] + "'" + " WHERE ip" + "=" + "'"+ new_ip +"'"
                print(sql)
                cur.execute(sql)

conn.commit()
conn.close()

id = ['208428842','1266497665','134787881','401975771']
for i in id:
    url = requests.post('https://api.telegram.org/bot1153858227:AAHPj_O2ziHpATV9Uwz8hlGRWppDpesqmjg/sendMessage?chat_id='+i+'&text=Данные камер обновлены!')
