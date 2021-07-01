#!/usr/bin/env python3

from pykeepass import PyKeePass
from ftplib import FTP
import fire 
import sys
import os
import getpass
from pathlib import Path

def load_keepass_data(file, password):
    kp = PyKeePass(file, password=password)
    group = kp.find_groups(name='Root',first=True)
    data = []
    for entry in group.entries:
        record = dict()
        record['project'] = entry.title
        record['ftp_pass'] = entry.password
        record['ftp_user'] = entry.username
        record['ftp_server'] = entry.custom_properties['ftp_server']
        record['source'] = entry.custom_properties['source']
        record['target'] = entry.custom_properties['target']
        data.append(record)
    return data
    kp.save()

def fetch_files(ftp, path, destination, overwrite=False):
    try:
        ftp.cwd(path)
        ftp.retrlines('LIST')
    except OSError:  
        pass
    except ftplib.error_perm:
        print("error: could not change to " + path)
        sys.exit("ending session")
    filelist = [i for i in ftp.mlsd()]
    for file in filelist:      
        if file[1]['type'] == 'file' and (file[0].endswith('.zip') or file[0].endswith('.gz')):         
            fullpath = os.path.join(destination, file[0])
            if (not overwrite and os.path.isfile(fullpath)):
                continue
            else:
                with open(fullpath, 'wb') as f:
                    ftp.retrbinary('RETR ' + file[0], f.write)
                print(file[0] + '  downloaded')
        
def main(file, base_path='mnt/ARCHIV/', target="/wp/wp-content/updraft/"):
    password = getpass.getpass('Password: ') 
    data = load_keepass_data(file, password)
    if data:
        for record in data:
            full_path = base_path + record['project'] + target
            Path(full_path).mkdir(parents=True, exist_ok=True)
            ftp = FTP(record['ftp_server'])
            ftp.login(record['ftp_user'], record['ftp_pass'])
            fetch_files(ftp,record['source'], full_path, overwrite=True)
            ftp.quit()
if __name__ == '__main__':
    fire.Fire(main)
    

