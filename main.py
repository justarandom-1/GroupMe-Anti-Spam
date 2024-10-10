TOKEN = "TOKEN HERE"
GROUP_LIST_PATH = "groups.txt"
BLACKLIST_PATH = "blacklist.txt"
CONTACT_EMAIL = ""


import os
import time
import groupy
from groupy.client import Client


client = Client.from_token(TOKEN)

group_list = open(GROUP_LIST_PATH, "r").read().split('\n')
ids = [group.id for group in client.groups.list()]
monitored_groups = [client.groups.get(id) for id in group_list if id in ids]
last_messages = [group.messages.list()[0] for group in monitored_groups]


blacklist = open(BLACKLIST_PATH, "r").read().split('\n')
for i in range(len(blacklist)):
    if ' | ' in blacklist[i]:
        blacklist[i] = blacklist[i].split(' | ')
    else:
        blacklist[i] = [blacklist[i]]
        
print("On")

while True:
    time.sleep(1)
    for i in range(len(monitored_groups)):
        monitored_groups[i].refresh_from_server()
        new_messages = list(monitored_groups[i].messages.list(since_id = last_messages[i].id))
        if new_messages:        
            last_messages[i] = new_messages[0]
            for message in new_messages:

                if message.text.startswith('-setup'):
                    try:
                        group_data = message.text[message.text.index('https://groupme.com/join_group/') + 31:].split('/')
                        client.groups.join(group_data[0], group_data[1])
                        monitored_groups[i].post(f"Joined group \'{client.groups.get(group_data[0]).name}\'")

                        open(GROUP_LIST_PATH, "a").write('\n' + str(group_data[0]))
                        monitored_groups.append(client.groups.get(group_data[0]))
                        last_messages.append(client.groups.get(group_data[0]).messages.list()[0] )
                    except:
                        monitored_groups[i].post('Could not join group.')
                
                if message.text.startswith('-ping'):
                    monitored_groups[i].post('Bot is online.')
                    
                if message.text.startswith('-purge'):
                    for m in monitored_groups[i].messages.list():
                        text = m.text.upper()
                        if any(all([y in text for y in x]) for x in blacklist)\
                        and m.user_id not in [monitored_groups[i].creator_user_id, client.user.get_me()['user_id']]:
                            try:
                                target = [member for member in monitored_groups[i].members if member.user_id == m.user_id][0]
                                target_name = target.name
                                target.remove()
                                if CONTACT_EMAIL:
	                                monitored_groups[i].post(f"(This was an automated action, email {CONTACT_EMAIL} if this was a mistake.)")
                            except:
                                pass
                        
                    
                text = message.text.upper()
                if any(all([y in text for y in x]) for x in blacklist)\
                and message.user_id not in [monitored_groups[i].creator_user_id, client.user.get_me()['user_id']]:                 
                    try:
                        target = [member for member in monitored_groups[i].members if member.user_id == message.user_id][0]
                        target_name = target.name
                        target.remove()
                        monitored_groups[i].post(f"{target_name} removed for possible bot spam.")
                        if CONTACT_EMAIL:
                            monitored_groups[i].post(f"(This was an automated action, email {CONTACT_EMAIL} if this was a mistake.)")
                    except:
                        pass
            break
