import googleapiclient.discovery
import httplib2
from oauth2client.service_account import ServiceAccountCredentials

from settings import INVENTARIZATION_SPREADSHEET_ID, CREDENTIAL_FILE
from bot_sources import logger

class GoogleSheetOperator(object):

    def __init__(self, spreadsheet_id, credentials_file_name):
        self.spreadsheet_id = spreadsheet_id
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_file_name,
            ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive'])
        self.httpAuth = self.credentials.authorize(httplib2.Http())
        self.service = googleapiclient.discovery.build('sheets', 'v4', http=self.httpAuth)

    def read_range(self, list_name, range_in_list, major_dimension='ROWS'):
        values = None
        try:
            values = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"\'{list_name}\'!{range_in_list}",
                majorDimension=major_dimension
            ).execute()
        except Exception as e:
            print(e)
            return values
        return values.get('values')

    def write_data_to_range(self, list_name, range_in_list, data, major_dimension='ROWS'):
        try:
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={
                    "valueInputOption": "USER_ENTERED",
                    "data":
                        [
                            {"range": f"\'{list_name}\'!{range_in_list}",
                             "majorDimension": major_dimension,
                             "values": data}
                        ]
                }
            ).execute()
        except Exception as e:
            print(e)
            return


class GoogleSync(GoogleSheetOperator):

    def __init__(self, spreadsheet_id=INVENTARIZATION_SPREADSHEET_ID, credentials_file_name=CREDENTIAL_FILE):
        super().__init__(spreadsheet_id, credentials_file_name)
