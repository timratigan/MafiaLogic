import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pprint

pp = pprint.PrettyPrinter()

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

sheet = client.open('God Sheet').sheet1

player = sheet.cell(10,1).value

pp.pprint(player)

sheet.update_cell(10,1, 'Eli: Pirate Extraordinaire')

player = sheet.cell(10,1).value

pp.pprint(player)
