import os

from dotenv import load_dotenv

load_dotenv()

BOT_PROXY = {'https': os.environ.get('BOT_PROXY')}
BOT_TOKEN = os.environ.get('BOT_TOKEN')

INVENTARIZATION_SPREADSHEET_ID = os.environ.get('INVENTARIZATION_SPREADSHEET_ID')
PHONE_SPREADSHEET_ID = os.environ.get('PHONE_SPREADSHEET_ID')
CREDENTIAL_FILE = os.environ.get('CREDENTIAL_FILE')

DB_FILE_PATH = os.environ.get('DB_FILE_PATH')

USER_SECRET = os.environ.get('USER_SECRET')

LOG_FILE = os.environ.get('LOG_FILE')

CHANNEL_URL = os.environ.get('CHANNEL_URL')

IT_SUPPORT_TABLE = os.environ.get('IT_SUPPORT_TABLE')
IT_SUPPORT_FORM = os.environ.get('IT_SUPPORT_FORM')