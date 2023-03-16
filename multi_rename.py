#Imports
from fabric import Connection
from invoke import Responder
from csv import DictReader
import click
import multiprocessing

def get_creds():
    username = click.prompt('Username', type=str)
    password = click.prompt('Password', type=str)
    return username, password

def open_rename_list():
    filename = click.prompt('Path to renaming CSV', type=str)
    with open(filename,'r', encoding='utf-8-sig') as data:
        dict_reader = DictReader(data)
        rename_list = list(dict_reader)
    return rename_list

def send_commands(computer, creds, restart, queue):
    result = ''

    username = creds[0]
    password = creds[1]

    old_name = computer['Serial']
    new_name = computer['Name']


    #auto respond to sudo prompts with the password
    sudopass = Responder(
       pattern=r'Password:',
       response=password+'\n',
    )


    #TODO change commands after testing
    cmd_rename = "sudo /usr/local/jamf/bin/jamf getComputerName"
    cmd_recon = "sudo hostname"

    #cmd_rename = "/usr/local/jamf/bin/jamf setComputerName -name " + new_name]
    #cmd_recon = "/usr/local/jamf/bin/jamf recon"

    #open ssh connection
    print('Connecting to ' + old_name)
    c = Connection(
        host=old_name,
        user=username,
        connect_kwargs={
            "password": password,
        },
    )
    try:
        c.open()

        #rename
        print("renaming " + old_name + ' to ' + new_name)
        c.run(cmd_rename, pty=True, warn=True, hide=True, watchers=[sudopass])
        result = str(c.run('hostname', hide=True)).split('\n')[2]
        if result == new_name:
            queue.put(old_name + ' renamed to: ' + result)
        else:
            queue.put(old_name + ' rename failed')

        #recon
        c.run(cmd_recon, pty=True, warn=True, hide=True, watchers=[sudopass])

        #restart
        if restart:
            print('restarting...' + old_name)
            c.run("sudo shutdown -r now", pty=True, warn=True, hide=True, watchers=[sudopass])

        #close connection
        try:
            c.close()
        except:
            print('Unable to close connection')

    except:
        print("Connection to " + old_name + " failed")
        queue.put(old_name + ' rename failed')




def main():
    print("Welcome to the Mac Renaming Utility")
    #get credentials, list of computers, and restart option
    creds = get_creds()
    computers = open_rename_list()
    restart = click.confirm('Would you like to restart the computers after renaming?', default=False)

    #start a new process for each connection
    processes = []
    queue = multiprocessing.Queue()
    for computer in computers:
        #connect to each computer and send commands
        p = multiprocessing.Process(target= send_commands, args=(computer, creds, restart, queue,))
        processes.append(p)
        p.start()

    for process in processes:
        process.join()

    #display results
    print('--------------------\nResults\n--------------------') 
    while not queue.empty():
        print(queue.get())


if __name__ == "__main__":
    main()