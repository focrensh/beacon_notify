#!/usr/bin/python
import os
import apprise
import json
import yaml
import requests
import logging
import datetime as dt
import time

open('webhook.log', 'w').close()
logging.basicConfig(format='%(levelname)s:%(message)s', filename='webhook.log',level=logging.WARNING)

#### VARIABLE SETUP
apobj = apprise.Apprise()
config = apprise.AppriseConfig()
config.add('./config.yml')
apobj.add(config)


cur_state = {}
tmp_state = {}

beaconun = os.environ['BEACON_UN']
beaconpw = os.environ['BEACON_PW']
beaconacct = os.environ['BEACON_ACCT']

bc = open("beacon_config.yaml", "r")
bcinput = yaml.load(bc,  Loader=yaml.FullLoader)
monitor_apps = bcinput['apps']
checkInterval = bcinput['checkInterval']
repeatMessage = bcinput['repeatMessage']
alert_states = bcinput['alert_states']
clear_states = bcinput['clear_states']

def login(un, pw):
    url = "https://api.cloudservices.f5.com/v1/svc-auth/login"
    headers = {'Content-Type': 'application/json'}
    payload = {'username': un, 'password': pw}
    response = requests.request("POST", url, headers=headers, data = json.dumps(payload))
    if response.status_code != 200:
        print ("Login Failed")
        logging.warning('Login Failed')
    return response.json()['access_token']

def get_apps(tkn, acct):
    url = "https://api.cloudservices.f5.com/beacon/v1/applications"
    headers = {
        'Authorization': 'Bearer %s' % (tkn),
        'Content-Type': 'application/json',
        'X-F5aas-Preferred-Account-Id': acct
    }
    response = requests.request("GET", url, headers=headers)
    if response.status_code != 200:
        print ("Failed to retrieve Apps")
        logging.warning('Failed to retrieve Apps')
    return response.json()['apps']

def clearOld():
    # print(cur_state)
    ct = dt.datetime.now()
    for k,v in cur_state.items():
        # past_time = dt.datetime.strptime(v['time'], '%Y-%m-%d %H:%M:%S.%f')
        # print(ct - past_time)
        if (ct - v['time']) > dt.timedelta(minutes=repeatMessage):
            pass
        else:
            tmp_state[k] = v
    cur_state.clear()
    cur_state.update(tmp_state)
    tmp_state.clear()
    # print(cur_state)



def notify(t,b,nt):
    apobj.notify(
        body = b,
        title = t,
        notify_type = nt
    )


def poll():
    print(cur_state)
    clearOld()
    tkn = login(beaconun, beaconpw)
    beacon_apps = get_apps(tkn, beaconacct)
    for app in beacon_apps:
        name = app['name']
        currentHealth = app['currentHealth']
        reason = app['rollupHealthStatusReasons']
        if currentHealth == "Critical":
            notify_t = "failure"
        if currentHealth == "Warning":
            notify_t = "warning"
        if name in monitor_apps:
            if currentHealth in alert_states:
                if name in cur_state:
                    if currentHealth in clear_states:
                        cur_state.pop(name) # Remove from tracked apps if not in alert_state
                    if currentHealth == cur_state[name]['currentHealth']:
                        continue
                    else:
                        #STATUS CHANGED from previous state, SEND and update
                        print("Status Changed, send update ||App: %s | Status: %s | Reason: %s" % (name, currentHealth, reason))
                        logging.warning("Status Changed, send update ||App: %s | Status: %s | Reason: %s" % (name, currentHealth, reason))
                        notify("%s" % (name),"Status: %s | Reason: %s" % (currentHealth, reason), notify_t)
                        cur_state[name] = {"currentHealth": currentHealth, "reason": reason, "time": dt.datetime.now()}
                else:
                    #New alert state app
                    print("New Status, send update ||App: %s | Status: %s | Reason: %s" % (name, currentHealth, reason))
                    logging.warning("New Status, send update ||App: %s | Status: %s | Reason: %s" % (name, currentHealth, reason))
                    notify("%s" % (name),"Status: %s | Reason: %s" % (currentHealth, reason), notify_t)
                    cur_state[name] = {"currentHealth": currentHealth, "reason": reason, "time": dt.datetime.now()}
            

while True:
    poll()
    time.sleep(checkInterval)