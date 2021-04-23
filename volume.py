from subprocess import check_output
import os
volume_name = input("Enter the Volume Name you'd like to kill usage for:\n")
pid_check = check_output(f"lsof | grep {volume_name}", shell=True)
pid_list = pid_check.decode('utf-8').split('\n')
for id_ in pid_list:
    if id_ and 'Applications' in id_ and '/usr/bin/login' not in id_:
        os.system(f'kill -9 {id_.split()[1]} >/dev/null 2>&1')  # redirects stderr output to stdout
