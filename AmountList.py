# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 11:54:00 2018

@author: timandreev
"""

import requests
import json
import pandas as pd

token = 'TOKEN'

"""
Получение списка клиентов
"""

AgencyClientsURL = 'https://api.direct.yandex.com/json/v5/agencyclients'

# Создание HTTP-заголовков запроса
headers = {
           # OAuth-токен. Использование слова Bearer обязательно
           "Authorization": "Bearer " + token,
           # Язык ответных сообщений
           "Accept-Language": "ru"
           }

AgencyClientsBody = {
    "method": "get",
    "params": {
        "SelectionCriteria": {
            "Archived": "NO"   # Получить только активных клиентов
        },
        "FieldNames": ["Login"],
        "Page": {
            "Limit": 10000,  # Получить не более 10000 клиентов в ответе сервера
            "Offset": 0
        }
    }
}

# Отсутствие параметра LimitedBy в ответе означает, что
# получены все клиенты
HasAllClientLoginsReceived = False
ClientList = []

while not HasAllClientLoginsReceived:
    ClientsResult = requests.post(AgencyClientsURL, json.dumps(AgencyClientsBody), headers=headers).json()
    for Client in ClientsResult['result']['Clients']:
        ClientList.append(Client["Login"])
    if ClientsResult['result'].get("LimitedBy", False):
        AgencyClientsBody['Page']['Offset'] = ClientsResult['result']["LimitedBy"]
    else:
        HasAllClientLoginsReceived = True


"""
Создание отчета по бюджетам
"""

BudgetURL = "https://api.direct.yandex.ru/live/v4/json/"

# Создание запроса по бюджетам
# Создание двух словарей для текущего остатка и дневного бюджета
AmountDict = {}
DayBudgetDict = {}


for login in range(len(ClientList)):
    params = {
            "method" : "AccountManagement",
            "token" : token,
            "param" : {
                    "SelectionCriteria" : {
                            "Logins" : [ClientList[login]]
                                        },
            "Action":"Get"
                    }
            }

    jdata = json.dumps(params, ensure_ascii=False).encode('utf8')  
    result = requests.post(BudgetURL, data = jdata).json()


# Добавление результатов в словари
    try:
        AmountDict[result["data"]["Accounts"][0]["Login"]] = result["data"]["Accounts"][0]["Amount"]
        DayBudgetDict[result["data"]["Accounts"][0]["Login"]] = result["data"]["Accounts"][0]["AccountDayBudget"]["Amount"]
    except IndexError:
        pass
    except KeyError:
        pass
 
# Преобразование в серию и запись в файл       
AmountSeries = pd.Series(AmountDict)
DayBudgetSeries = pd.Series(DayBudgetDict)

Amounts = pd.concat([AmountSeries, DayBudgetSeries], axis = 1)
Amounts.to_csv("Amounts.csv", sep='\t', encoding='utf-8')
