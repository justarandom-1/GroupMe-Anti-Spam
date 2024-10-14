TOKEN = "TOKEN HERE"
GROUP_LIST_PATH = "groups.txt"
BLACKLIST_PATH = "blacklist.txt"
LAST_MESSAGES_PATH = "last_messages.txt"
CONTACT_EMAIL = ""


import os
import time
import groupy
from groupy.client import Client

client = Client.from_token(TOKEN)
self_id = client.user.get_me()['user_id']

group_list = open(GROUP_LIST_PATH, "r").read().split('\n')
ids = [group.id for group in client.groups.list()]

monitored_groups = [client.groups.get(id) for id in group_list if id in ids]

last_messages = {}

for group in monitored_groups:
    last_messages[group.id] = group.messages.list()[0].id

try:
    last_messages_archive = open(LAST_MESSAGES_PATH, "r").read().split('\n')
    for line in last_messages_archive:
        data = line.split(' | ')
        last_messages[data[0]] = data[1]
except:
    pass

blacklist = open(BLACKLIST_PATH, "r").read().split('\n')
for i in range(len(blacklist)):
    if ' | ' in blacklist[i]:
        blacklist[i] = blacklist[i].split(' | ')
    else:
        blacklist[i] = [blacklist[i]]
        
def check(group, message):
    text = message.text.upper()
    if any(all([word in text for word in trigger]) for trigger in blacklist)\
    and message.user_id not in [group.creator_user_id, self_id]:
        try:
            target = [member for member in group.members if member.user_id == message.user_id][0]
            target_name = target.name
            target.remove()
            group.post(f"{target_name} removed for possible bot spam.")
            if CONTACT_EMAIL:
                group.post(f"(This was an automated action, email {CONTACT_EMAIL} if this was a mistake.)")
        except:
            pass

print("On")

while True:
    time.sleep(5)
    for group in monitored_groups:
        group.refresh_from_server()
        new_messages = list(group.messages.list(since_id = last_messages[group.id]))
        if new_messages:
            last_messages[group.id] = new_messages[0].id
            for message in new_messages:

                if message.text.startswith('-setup'):
                    try:
                        group_data = message.text[message.text.index('https://groupme.com/join_group/') + 31:].split('/')
                        client.groups.join(group_data[0], group_data[1])
                        group.post(f"Joined group \'{client.groups.get(group_data[0]).name}\'")

                        open(GROUP_LIST_PATH, "a").write('\n' + str(group_data[0]))
                        new_group = client.groups.get(group_data[0])
                        monitored_groups.append(new_group)
                        last_messages[group_data[0]] = new_group.messages.list()[0].id
                    except:
                        group.post('Could not join group.')
                
                if message.text.startswith('-ping'):
                    group.post('Bot is online.')
                    
                if message.text.startswith('-purge'):
                    try:
                        target_group = group
                        if len(message.text) > 7:
                            target_group = client.groups.get(message.text[7:])

                        for m in target_group.messages.list():
                            check(group, m)                        
                    except:
                        group.post('Unable to purge.')

                check(group, message)

    open(LAST_MESSAGES_PATH, "w").write('\n'.join([f"{id} | {last_messages[id]}" for id in last_messages.keys()]))
