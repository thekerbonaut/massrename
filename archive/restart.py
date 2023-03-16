#Imports
from fabric import Connection
from invoke import Responder
from csv import DictReader

#get username and password
username = input('Username: ')
password = input('Password: ')

#open file and add the names and serials to a dictionary
filename = input('Path to CSV: ')
with open(filename,'r', encoding='utf-8-sig') as data:
    dict_reader = DictReader(data)
    rename_list = list(dict_reader)

#auto respond to sudo prompts with the password
sudopass = Responder(
    pattern=r'Password:',
    response=password+'\n',
)

#connect to each serial number and rename it to the correct hostname specified in the csv
for device in rename_list:
    cmd = "sudo shutdown -r now"
    print('Connecting to ' + device['Serial'])
    c = Connection(
        host=device['Serial'],
        user=username,
        connect_kwargs={
            "password": password,
        },
    )
    c.run("/usr/local/jamf/bin/jamf getComputerName")
    print("restarting " + c.host)
    c.run(cmd, pty=True, warn=True, watchers=[sudopass])