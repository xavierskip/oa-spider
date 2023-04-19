import subprocess
import psutil
import pickle
import yaml

''' ssl-vpn.yml
sslvpn1: EasierConnect -server [] -port [] -username [] -password [] -socks-bind 127.0.0.1:55555
sslvpn2: EasierConnect -server [] -port [] -username [] -password [] -socks-bind 127.0.0.1:55556
'''
with open('ssl-vpn.yml', 'r', encoding='utf-8') as f:
    commands = yaml.safe_load(f.read())

# 存储进程PID的字典
pids = {}
pids_file = "pids"
try:
    with open(pids_file, "rb") as f:
        pids = pickle.load(f)
except FileNotFoundError as e:
    with open(pids_file, "wb") as f:
        pickle.dump(pids, f)

# 运行每个程序
for ps,exe in commands.items():
    if ps in pids and psutil.pid_exists(pids[ps]):
        print(f'{pids[ps]}:[{ps}] is already run...')
        continue
    else:
        print(f'run ... [{ps}]')
        p = subprocess.Popen(
            exe.split(" "),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin =subprocess.PIPE
            )
        pids[ps] = p.pid

with open(pids_file, "wb") as f:
    pickle.dump(pids, f)

# python oa-spider.py
from oa_spider.run import main
from oa_spider import OAini

main(OAini)