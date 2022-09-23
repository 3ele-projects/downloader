#!/usr/bin/env python3

from pykeepass import PyKeePass
from ftplib import FTP
import fire 
import sys
import os
from os import listdir
from os.path import isfile, join
import getpass
from pathlib import Path
import pysftp  as SFTP
import json
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
class WPBackuper:

    def __init__(self):
        self.logs = []
        self.month = 1
 
    def json_log(self):
        pass

    def load_keepass_data(self,file, password):
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
            record['port'] = entry.custom_properties.get('port')
    #        record['target'] = entry.custom_properties['target']
            data.append(record)
        return data
        kp.save()

    def fetch_sftp_files(self, sftp, path, destination, overwrite=False):

        sftp.chdir(path)
        filelist = list(sftp.listdir())
        
        for file in filelist:
               
            if file.endswith('.zip') or file.endswith('.gz'):
                self.log_row['messages']['info'].append(file +  '   check') 
                fullpath = os.path.join(sftp.pwd, file)
                local_path = os.path.join(destination, file)
                if (overwrite == False and os.path.isfile(local_path) == False):
                    
                    sftp.get(fullpath,local_path, preserve_mtime=True)
                    self.log_row['downloaded_files'].append(file)
                if (overwrite == True):
                    sftp.get(fullpath,local_path, preserve_mtime=True)
                    self.log_row['downloaded_files'].append(file)

                 

 

    def fetch_ftp_files(self, ftp, path, destination, overwrite=False):
        try:
            ftp.cwd(path)
    #       ftp.retrlines('LIST')
        except OSError:  
          
            self.log_row['messages']['errors'].append(OSError)
            pass
        except ftplib.error_perm:
            
            self.log_row['messages']['errors'].append("error: could not change to " + path)
            sys.exit("ending session")
        filelist = [i for i in ftp.mlsd()]
        for file in filelist:      
            if file[1]['type'] == 'file' and (file[0].endswith('.zip') or file[0].endswith('.gz')):         
                
                self.log_row['messages']['info'].append(file[0] +  '   check')
                fullpath = os.path.join(destination, file[0])
        
             #   print (os.path.isfile(fullpath) , fullpath )
                if (overwrite and os.path.isfile(fullpath)):
                    continue

                else:
                    with open(fullpath, 'wb') as f:
                        ftp.retrbinary('RETR ' + file[0], f.write)
                    print(file[0] + '  downloaded')
                    self.log_row['downloaded_files'].append(file)

    def scan_files(self,full_path):
     
        self.log_row['files'] = [f for f in listdir(full_path) if isfile(join(full_path, f))]
        self.log_row['files_to_delete'] = []
        for file in self.log_row['files']:
            splited_name = file.split('_')
            if (splited_name[1]):
                today = datetime.today()
                date_time_obj = datetime.strptime(splited_name[1], '%Y-%m-%d-%H%M')
                
                
                past_date = today - relativedelta(months=self.month)
                if (date_time_obj < past_date):
                    self.log_row['files_to_delete'].append(file)


            
    def remove_files(self, full_path):
        for file in self.log_row['files_to_delete']:
            filepath = os.path.join(full_path, file)
            try:
                os.remove(filepath )
            except:
                pass
            


    def main(self, file, base_path='mnt/ARCHIV/', target="/wp/wp-content/updraft/", remove_files=False):
        password = getpass.getpass('Password: ')
        data = self.load_keepass_data(file, password)
        if data:

            for record in data:
                now = datetime.now()
                date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                self.log_row = {}
                self.log_row['downloaded_files'] = []
                self.log_row['files'] = []
                self.log_row['messages'] = {
                    'info' : [],
                    'warnings': [],
                    'errors': []
                    }   
                self.log_row['messages']['info'].append(record['project'] + '  start')
                self.log_row['datetime'] = date_time_str
              
                full_path = base_path + record['project'] + target
                self.log_row['full_path'] = full_path
                Path(full_path).mkdir(parents=True, exist_ok=True)
             
                if record['port'] == '22':
                
                    cnopts = SFTP.CnOpts()
                    cnopts.hostkeys = None
                    try:
                        sftp = SFTP.Connection(record['ftp_server'].strip(), username=record['ftp_user'],password=record['ftp_pass'], cnopts=cnopts)
                        self.fetch_sftp_files(sftp,record['source'], full_path, overwrite=False)
                        sftp.close()
                    except Exception as e:
                 
                        self.log_row['messages']['errors'].append(str(e))
                   
                else:
                    ftp = FTP(record['ftp_server'].strip())     
                    try:
                        ftp.login(record['ftp_user'], record['ftp_pass'])
                        self.fetch_ftp_files(ftp,record['source'], full_path, overwrite=False)
                        ftp.quit()
                    except Exception as e:
                    
                        self.log_row['messages']['errors'].append(str(e))
                      
                        
                
                self.scan_files(full_path)
                if remove_files == True:
                    self.remove_files(full_path)

                self.logs.append({
                    record['project']:self.log_row
                })

            with open('data.json', 'w') as f:
                    json.dump(self.logs, f,  indent=4)



if __name__ == '__main__':
        
    fire.Fire(WPBackuper)
    

