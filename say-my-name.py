import shelve
import time
import string
from operator import itemgetter
from shlex import split

import yaml

from slack_sdk import WebClient
from slack_sdk.rtm import RTMClient

from asteval import Interpreter

aeval = Interpreter()

# Todo: Config checking
CONFIG = yaml.load(open('config.yaml'), Loader=yaml.Loader)

slack_token = CONFIG['token']
command = CONFIG['command'].strip(' "')
db_name = CONFIG['db_name']
case_sensitive = str(CONFIG.get('case_sensitive')).lower() == 'true'
timeout = int(CONFIG['timeout'])

use_ocr = str(CONFIG.get('use_ocr')).lower() == 'true'

if use_ocr:
    print('WARNING: you have enabled OCR. This is likely to be slow.')
    import ocr

    ocr_cleaner = ocr.OCRcleaner(CONFIG['font_file'], CONFIG.get('font_size', 25), CONFIG.get('font_gap', 5))

def clean_dict(dct):
    out = {}
    for k, v in dct.items():
        if isinstance(v, dict):
            out[k] = clean_dict(v)
        elif isinstance(v, list):
            out[k] = clean_list(v)
        else:
            # if case_sensitive: out[k] = str(v)
            out[k] = str(v)

    return out

def clean_list(lst):
    out = []
    for x in lst:
        if isinstance(x, dict):
            out.append(clean_dict(x))
        elif isinstance(x, list):
            out.append(clean_list(x))
        else:
            # if case_sensitive: out.append(str(x))
            out.append(str(x))

    return out

keywords = clean_dict(CONFIG['keywords'])

print('Keywords:', keywords)

# TODO: Use async
@RTMClient.run_on(event="message")
def handle_message(**payload):
    
    data = payload['data']
    
    if data.get('subtype', None) == 'message_changed':
        data = data['message']

    user = data['user']

    print(data['blocks'], end=' ')

    try:
        message = parse_blocks(data['blocks'])
    except KeyError as e: print('KeyError:', e)
    except Exception as e: print('Exception:', e)

    client = payload['web_client']

    channel_id = data['channel']
    # thread_ts = data['ts']

    print(message)

    if message.startswith(command):
        handle_command(message, channel_id, client)
        return

    # message = message.strip(string.punctuation + string.whitespace)

    if use_ocr:
        message = ocr_cleaner(message)

    for kwname, kwrds in keywords.items():
        for kwrd in kwrds:
            if isinstance(kwrd, dict):
                if 'eval' in kwrd and eval_math(message) == kwrd['eval']:
                    handle_keyword(kwname, user, channel_id, client)
                if 'case_sensitive' in kwrd and message == kwrd['case_sensitive']:
                    handle_keyword(kwname, user, channel_id, client)
            else:
                if message.lower() == kwrd.lower():
                    handle_keyword(kwname, user, channel_id, client)

def handle_command(inp, channel_id, client):
    # cmd = message.replace(command, '').strip()
    cmd = split(inp)[1:]

    if cmd == []: cmd = 'top 5'
    print('command:', cmd)

    match cmd:
        case 'top', amount:
            with shelve.open(db_name) as db:
                board = []
                for user, udata in db.items():
                    times = sum(udata['kwords'].values())
                    username = get_username(user, client)
                    board.append((username, times, udata['lasttime']))

                board = list(reversed(sorted(board, key=itemgetter(1, 2))))

                message = 'Leaderboard of shame: ' + ', '.join(f'{b[0]}: {b[1]}' for b in board[:amount])
        
        case 'user', name:
            with shelve.open(db_name) as db:
                times = sum(db[name]['kwords'].values())
                message = f'{get_username(name, client)} has been gotten {times} times'

    client.chat_postMessage(
        channel = channel_id,
        text = message.strip(',')
    )

def handle_keyword(kwname, user, channel_id, client):
    username = get_username(user, client)

    with shelve.open(db_name, writeback=True) as db:
        if user not in db:
            db[user] = {'lasttime': time.time(), 'kwords': {}}
        else:
            newtime = db[user]['lasttime'] + timeout
            now = int(time.time())
            if newtime > now:
                client.chat_postMessage(
                    channel = channel_id,
                    text = f"{username} cannot be {kwname}'d again for {int(newtime-now)} seconds"
                )
                return
            else:
                db[user]['lasttime'] = now

        if kwname not in db[user]['kwords']:
            db[user]['kwords'][kwname] = 1
            total = 1
        else:
            db[user]['kwords'][kwname] += 1
            total = sum(db[user]['kwords'].values())

    client.chat_postMessage(
        channel = channel_id,
        text = f"Whoops! {username} got {kwname}'d! (total: {total})"
    )
    return

def parse_blocks(blocks):
    '''
    Parses Slack text blocks in a naive way to just extract raw text
    Naive in the sense that it iterates through looking for blocks named text
    '''
    out = ''
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get('type') == 'text':
            out += block.get('text')
        if block.get('type') == 'user':
            out += ' ' + block.get('user_id')
        elif 'elements' in block:
            out += parse_blocks(block['elements'])
    return out

def get_username(user, client):
    '''
    get the username of the given user object
    requires a slack client to be passed
    '''
    user_info = client.users_info(user=user).get('user')['profile']
    disp = user_info['display_name_normalized']
    return disp if disp else user_info['real_name_normalized']

def eval_math(expr:str) -> str:
    x = aeval(expr)
    try:
        if x.is_integer():
            return str(int(x))
    except AttributeError:
        pass

    return str(x)

# Ensure the shelve file exists
with shelve.open(db_name, flag='c'): pass

rtm_client = RTMClient(token=slack_token)
rtm_client.start()
