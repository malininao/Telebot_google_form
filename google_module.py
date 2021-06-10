from pprint import pprint
import httplib2
import googleapiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict
import os
from datetime import datetime

# for install requirement package use the command
# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib


def create_keyfile_dict():
    variables_keys = {
        "type": os.environ.get("SHEET_TYPE"),
        "project_id": os.environ.get("SHEET_PROJECT_ID"),
        "private_key_id": os.environ.get("SHEET_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("SHEET_PRIVATE_KEY"),
        "client_email": os.environ.get("SHEET_CLIENT_EMAIL"),
        "client_id": os.environ.get("SHEET_CLIENT_ID"),
        "auth_uri": os.environ.get("SHEET_AUTH_URI"),
        "token_uri": os.environ.get("SHEET_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.environ.get("SHEET_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.environ.get("SHEET_CLIENT_X509_CERT_URL")
    }
    return variables_keys


HEROKU = os.environ.get('HEROKU')
if HEROKU == "True":
    CREDENTIALS_FILE = create_keyfile_dict()
else:
    CREDENTIALS_FILE = './/bimbot-316407-d1dbeda69dde.json'

scope = ['https://www.googleapis.com/auth/drive',
         'https://www.googleapis.com/auth/spreadsheets']
credentional = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    scope
)
httpAuth = credentional.authorize(httplib2.Http())
services_sheet = googleapiclient.discovery.build('sheets', 'v4', http=httpAuth)


class DateTime:

    @staticmethod
    def date():
        date = f'{datetime.now().date().day}.{datetime.now().date().month}.{datetime.now().date().year}'
        return date

    @staticmethod
    def time():
        time = f'{datetime.now().time().hour}:{datetime.now().time().minute}:{datetime.now().time().second}'
        return time


class GoogleSheets:

    def __init__(self, link_url):
        self.link_url = link_url

    def get_sheets_from_url(self):
        sheet_id = self.link_url.split('/')[5]
        return sheet_id

    def get_sheets_values(self):
        sheet = services_sheet.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.get_sheets_from_url(), range='База ответов!A2:ZZ').execute()
        values = result.get('values', [])
        result_structure = sheet.values().get(spreadsheetId=self.get_sheets_from_url(), range='Структура!A2:ZZ2').execute()
        structure = result_structure.get('values', [])
        result_question = sheet.values().get(spreadsheetId=self.get_sheets_from_url(), range='Вопросы!A2:ZZ').execute()
        question = result_question.get('values', [])
        users_data = []
        for row in values:
            users_parameters = {
                'user_name': "Empty value",
                'name': "Empty value",
                'email': "Empty value",
                'date': "Empty value",
            }
            if row:
                users_parameters['user_name'] = row[0]
                users_parameters['name'] = row[1]
                users_parameters['email'] = row[2]
                users_parameters['date'] = row[3]
            users_data.append(users_parameters)

        return users_data, structure, question

    def get_user_data(self, username):
        sheets_values = self.get_sheets_values()
        users_parameters = sheets_values[0]
        user_name_list = []
        for item in users_parameters:
            user_name_list.append(item['user_name'])
        try:
            index = user_name_list.index(username)
            return users_parameters[index], int(index), user_name_list
        except:
            print(user_name_list)
            return "Пользователя нет в базе", user_name_list

    def add_answer(self, user_name, answers):
        sheet = services_sheet.spreadsheets()
        user_data = self.get_user_data(user_name)
        user_name_list = [user_name]
        answer = user_name_list + answers
        if user_data[0] == "Пользователя нет в базе":
            if 'Empty value' in user_data[1]:
                index = user_data[1].index('Empty value') + 2
                print(f'Пользователь записан в строку: {index}')
            else:
                index = len(self.get_sheets_values()[0]) + 2
                print(f'Пользователь записан в строку: {index}')
            request = sheet.values().update(spreadsheetId=self.get_sheets_from_url(), range=f'База ответов!A{index}',
                                            valueInputOption='USER_ENTERED',
                                            body={'values': [answer]})
            request.execute()
        else:
            print(f"Такой пользователь уже создан. Строка {self.get_user_data(user_name)[1] + 2}")
            index = self.get_user_data(user_name)[1] + 2
            request = sheet.values().update(spreadsheetId=self.get_sheets_from_url(), range=f'База ответов!A{index}',
                                            valueInputOption='USER_ENTERED',
                                            body={'values': [answer]})
            request.execute()


if __name__ == "__main__":
    linkURLSheets = 'https://docs.google.com/spreadsheets/d/1TGeDND5G9c53K1xTKZ97gFwYoO1vyBsfiX0aljO-8Ss/edit#gid=0'
    data = GoogleSheets(linkURLSheets)
    values = GoogleSheets(linkURLSheets).get_sheets_values()
    user = data.get_user_data("человек 7")
    print(user)
    #answer =  ['Виктор', "Почта", f'{DateTime.time()} {DateTime.date()}', '18', "Кашку", "Бражку"]
    #data.add_answer('человек 31', answer)

    print(values[0])
    print(user)
