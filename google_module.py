from pprint import pprint
import httplib2
import googleapiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict
import os
from datetime import datetime


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
    CREDENTIALS_FILE = 'osipia-eac8c331dd32.json'

scope = ['https://www.googleapis.com/auth/drive',
         'https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/spreadsheets']
credentional = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    scope
)
httpAuth = credentional.authorize(httplib2.Http())
services = googleapiclient.discovery.build('docs', 'v1', http=httpAuth)
services_sheet = googleapiclient.discovery.build('sheets', 'v4', http=httpAuth)


class GoogleDocs:

    # Класс который получает необходимые блоки гугл документа для дальнейшей работы в другом классе
    def __init__(self, link_url):
        self.link_url = link_url

    def get_document_from_url(self):
        docs_id = self.link_url.split('/')[5]
        document = services.documents().get(documentId=docs_id).execute()
        return document

    def get_document_body(self):
        doc_body = self.get_document_from_url().get('body')
        return doc_body

    def get_inline_object(self):
        inline_object = self.get_document_from_url().get('inlineObjects')
        return inline_object


class GoogleDocsRead:

    def __init__(self, doc_body=None, inline_objects=None, document_style=None, named_styles=None,
                 revision_id=None, suggestions_view_mode=None, document_id=None):

        self.doc_body = doc_body
        self.document_style = document_style
        self.inline_objects = inline_objects
        self.named_styles = named_styles
        self.revision_id = revision_id
        self.suggestions_view_mode = suggestions_view_mode
        self.document_id = document_id

    @staticmethod
    def build_in_html(text, styles):
        #print(styles)
        if 'italic' in styles:
            text = f'<i>{text}</i>'
        if 'bold' in styles:
            text = f'<b>{text}</b>'
        if 'underline' in styles:
            text = f'<u>{text}</u>'
        return text

    def read_text(self):
        # print(str(docBody['content'][2]['paragraph']['elements'][1]))

        paragraph_count = int(str(self.doc_body).count('paragraph') / 2)
        total_text_list = []

        for i in range(1, paragraph_count + 1, 1):
            string = ''
            elements_count = len(list(self.doc_body['content'][i]['paragraph']['elements']))

            for j in range(0, elements_count, 1):
                if str(self.doc_body['content'][i]['paragraph']['elements'][j]).count("inlineObjectElement") == 0:
                    text = self.doc_body['content'][i]['paragraph']['elements'][j]['textRun']['content']
                    styles = self.doc_body['content'][i]['paragraph']['elements'][j]['textRun']['textStyle']
                    string = string + self.build_in_html(text=text, styles=styles)
            total_text_list.append(string.replace('\n', ''))

            # if '' in total_text_list:
            # total_text_list.remove('')

        # print(total_text_list)

        return total_text_list

    def get_img(self):

        paragraph_count = int(str(self.doc_body).count('paragraph') / 2)
        total_img_list = []

        for i in range(1, paragraph_count + 1, 1):
            img_url = ''
            elements_count = len(list(self.doc_body['content'][i]['paragraph']['elements']))

            for j in range(0, elements_count, 1):
                if str(self.doc_body['content'][i]['paragraph']['elements'][j]).count("inlineObjectElement") != 0:
                    img_id = self.doc_body['content'][i]['paragraph']['elements'][j]['inlineObjectElement'] \
                        ['inlineObjectId']
                    img_url = (self.inline_objects[f'{img_id}']['inlineObjectProperties']['embeddedObject']
                    ['imageProperties']['contentUri'])

            total_img_list.append(img_url.replace('\n', ''))

            # if '' in total_img_list:
            # total_img_list.remove('')

        # print(total_img_list)

        return total_img_list

    def join_total_list(self):
        text_list = self.read_text()
        img_list = self.get_img()

        index_empty_text = defaultdict(list)
        index_empty_url = defaultdict(list)

        for index, e in enumerate(text_list):
            index_empty_text[e].append(index)

        for index, e in enumerate(img_list):
            index_empty_url[e].append(index)

        total_list = []
        for i in range(len(text_list)):
            total_list.append(text_list[i])
            total_list.append(img_list[i])
            if '' in total_list:
                total_list.remove('')
        if '' in total_list:
            total_list.remove('')

        for i in range(len(total_list)):
            if '' in total_list:
                total_list.remove('')

        '''
        print(index_empty_text)
        print(index_empty_url)
    
        print(index_empty_text[''])
        print(index_empty_url[''])
        '''
        #print(total_list)

        return total_list


class GoogleSheets:

    def __init__(self, link_url):
        self.link_url = link_url

    def get_sheets_from_url(self):
        sheet_id = self.link_url.split('/')[5]
        return sheet_id

    def get_sheets_values(self):
        sheet = services_sheet.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.get_sheets_from_url(), range='База!A2:F').execute()
        values = result.get('values', [])
        users_data = []
        for row in values:
            users_parameters = {
                'user_name': "Empty value",
                'date_start': "Empty value",
                'number_requests': 0,
                'effective_requests': 0,
                'time_of_latest_requests': "Empty value",
                'date_of_latest_requests': "Empty value"
            }
            if row:
                users_parameters['user_name'] = row[0]
                users_parameters['date_start'] = row[1]
                users_parameters['number_requests'] = row[2]
                users_parameters['effective_requests'] = row[3]
                users_parameters['time_of_latest_requests'] = row[4]
                users_parameters['date_of_latest_requests'] = row[5]

            users_data.append(users_parameters)

        return users_data

    def get_user_data(self, username):
        sheets_values = self.get_sheets_values()
        users_parameters = sheets_values
        user_name_list = []
        for item in users_parameters:
            user_name_list.append(item['user_name'])
        try:
            index = user_name_list.index(username)
            return users_parameters[index], int(index), user_name_list
        except:
            return "Пользователя нет в базе", user_name_list

    def add_user(self, user_name):
        sheet = services_sheet.spreadsheets()
        user_data = self.get_user_data(user_name)
        date = f'{datetime.now().date().day}.{datetime.now().date().month}.{datetime.now().date().year}'
        if user_data[0] == "Пользователя нет в базе":
            if 'Empty value' in user_data[1]:
                index = user_data[1].index('Empty value') + 2
                print(f'Пользователь записан в строку: {index}')
            else:
                index = len(self.get_sheets_values()) + 2
                print(f'Пользователь записан в строку: {index}')
            request = sheet.values().update(spreadsheetId=self.get_sheets_from_url(), range=f'База!A{index}',
                                            valueInputOption='USER_ENTERED',
                                            body={'values': [[user_name, f"{date}", 0, 0, 'Empty', 'Empty']]})
            request.execute()
        else:
            print(f"Такой пользователь уже создан. Строка {self.get_user_data(user_name)[1] + 2}")

    def add_interaction_point(self, user_name, effective):
        self.add_user(user_name)
        sheet = services_sheet.spreadsheets()
        user_data = self.get_user_data(user_name)
        last_count_request = user_data[0]['number_requests']
        last_count_effective_request = user_data[0]['effective_requests']
        new_count_request = int(last_count_request) + 1
        if effective is True:
            new_count_effective_request = int(last_count_effective_request) + 1
        else:
            new_count_effective_request = int(last_count_effective_request)
        date = f'{datetime.now().date().day}.{datetime.now().date().month}.{datetime.now().date().year}'
        time = f'{datetime.now().time().hour}:{datetime.now().time().minute}:{datetime.now().time().second}'
        values = [[new_count_request, new_count_effective_request, time, date]]
        index = user_data[1] + 2
        request = sheet.values().update(spreadsheetId=self.get_sheets_from_url(), range=f'База!C{index}',
                                        valueInputOption='USER_ENTERED',
                                        body={'values': values})
        request.execute()


if __name__ == "__main__":
    # linkURL = 'https://docs.google.com/document/d/1yb7TAgQQqjhBWoiCEmlRx0iZWbOp7BmHVxbRA_Ubl_k/edit'
    linkURLSheets = 'https://docs.google.com/spreadsheets/d/13mPMefBJ4gjLF2R6ONaOmJB6dsoM1ylWzg7cKQwh9tk/edit#gid=0'
    # doc = GoogleDocs(linkURL)
    # instruction = GoogleDocsRead(doc_body=doc.get_document_body(),
                                 # inline_objects=doc.get_inline_object()).join_total_list()
    data = GoogleSheets(linkURLSheets)
    values = GoogleSheets(linkURLSheets).get_sheets_values()
    user = GoogleSheets(linkURLSheets).get_user_data(username='Пользователь 2')
    data.add_user(user_name='Пользователь 129')
    data.add_interaction_point(user_name='Пользователь 129', effective=False)
    print(user[0])
    print(values)
