#!/usr/bin/env python
import sys
import requests
import html
import re
import curses
import getpass
import enum
import textwrap

def pull_msgs():
  """pulls recentish messages from the chat."""
  room_url = 'https://chat.stackexchange.com/rooms/9417/homotopy-theory'
  event_url = 'https://chat.stackexchange.com/chats/9417/events'

  r_room = requests.get(room_url)
  key = re.search(r"""id="fkey".*value="(\w+)" """,r_room.text).group(1) # got this from https://github.com/ghewgill/soirc.
  payload = {'fkey':key,'since':0,'mode':'Messages'}

  r_event = requests.post(event_url,json=payload)
  json_data = r_event.json()
  events = json_data['events']
  num_events = len(events)
  msg_dict = {'message_events':[]}
  for i in range(0,num_events):
    msg = {}
    msg['user_name'] = str(events[i].get('user_name'))
    msg['user_id'] = str(events[i].get('user_id'))
    msg['message_id'] = str(events[i].get('message_id'))
    msg['message_num'] = str(i)
    if 'content' not in events[i]:
      msg['content'] = ' [message was deleted]'
    else:
      cont = html.unescape(events[i].get('content'))
      msg['content'] = ' '+cont
    msg_dict['message_events'].append(msg)
  return msg_dict

# doesn't work
def user_auth():
  user_email = input('User email: ')
  pwd = getpass.getpass()
  auth_url = 'https://mathoverflow.net/users/login'
#  payload = {'client_id':user_id,'client_secret':pwd,'redirect_uri':'https://ryankeleti.github.io/ht.html'}
#  r_auth = requests.post(auth_url,json=payload)
#  if not not user_email or not not pwd:
#    print('Email or password not entered.')
#    sys.exit(1)
  payload = {'email':user_email,'password':pwd}
  r_auth = requests.post(auth_url,data=payload)
  if r_auth.status_code == 200:
    if r_auth.url != 'https://mathoverflow.net/':
      print('Auth failed')
      sys.exit(2)

  tok = ' '
#  auth_tok = r_auth.json()['access_token']
#  access_token = requests.get(auth_url+'/access_token?grant_type=client_credentials&client_id='+user_id+'&client_secret='+pwd).json()['access_token']
  return user_email,tok

#def user_input(user_name,user_id,s):
#  new_msg_url = 'https://chat.stackexchange.com/chats/9417/messages/new'
#  payload = {'user_name':user_name,'user_id':user_id,'content':s}

def print_msgs(stdscr,start):
  msgs = pull_msgs()['message_events']
  height, width = stdscr.getmaxyx()
  posy = 1
  if start < 0:
    start = 0
  elif start > len(msgs):
    start = 0
  for i in range(0,len(msgs)):
     if int(msgs[i]['message_num']) >= start:
       msg = msgs[i]
       if posy < height-4:
         user_info = '│ Username: '+msg['user_name']+' │ User id: '+msg['user_id']+' │ '
#+' message_id: '+msg['message_id']+' message_num: '
         stdscr.addstr(posy,2,'┌'+'─'*(len(user_info)-3)+'┐')
         posy += 1
         stdscr.addstr(posy,2,user_info)
         posy += 1
         stdscr.addstr(posy,2,'└'+'─'*(len(user_info)-3)+'┘')
         posy += 1
         out = '└─>'+msg['content']
         if len(user_info+out) > width-1:
           wrap_num = width-4
           wrap_out = textwrap.wrap(out,wrap_num)
           for line in wrap_out:
             stdscr.addstr(posy,2,textwrap.dedent(line))
             if posy < height-4:
               posy += 1
           posy -= 1
         else:
           stdscr.addstr(posy,2,out)
         posy += 1

class codes(enum.Enum):
  QUIT = 0
  REFR = 1
  WRIT = 2
  EXIT = 3
  ELSE = 4

help_str = '%q - quit, %r - refresh, %w - write message (./prog -u for user auth)'
def prompt(stdscr):
  entry = stdscr.getch()
  if entry == ord('q'):
    return codes.QUIT
  elif entry == ord('r'):
    return codes.REFR
  elif entry == ord('w'):
    return codes.WRIT
  else:
    return codes.ELSE

def chat_win(stdscr,user_id,tok):
  stdscr.clear()
  stdscr.refresh()

  status = -1
  key_pressed = 0
  start = 0
  if not not user_id and not not tok:
    login_yes = True
    user_name = ' '
    login_str = '│ [logged in as @'+user_name+'] '
  else:
    login_yes = False
    user_name = ' '
    login_str = '│ [not logged in] '
  bar = login_str+'│ up,down arrows to scroll │ press % to enter commands/view help '
  while status != codes.EXIT:
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    if key_pressed == curses.KEY_UP:
      start -= 1
    elif key_pressed == curses.KEY_DOWN:
      start += 1
    elif key_pressed == ord('%'):
      stdscr.addstr(height-3,0,'enter command [q,r,w,u] '+help_str)
      stdscr.addstr(height-2,0,'%')
      cmd = prompt(stdscr)
      if cmd == codes.QUIT:
        status = codes.EXIT
        continue
      elif cmd == codes.REFR:
        start = 0
      elif cmd == codes.WRIT:
        if login_yes:
          pass
        else:
          stdscr.addstr(height-2,len(bar)+2,'log in with \'./prog -u\' to post')
          pass
      else:
        pass

    # 0,...,0 gives │,│,─,─,┌,┐,└,┘
    stdscr.border(0,0,0,0,0,0,0,0)
    print_msgs(stdscr,start)
    stdscr.addstr(height-3,1,'─'*(width-2))
    stdscr.addstr(height-2,0,bar)
    stdscr.refresh()
    key_pressed = stdscr.getch()

def main():
  if len(sys.argv) > 1:
    if sys.argv[1] == '-u':
      user_email,user_id,tok = user_auth()
  else:
    user_id = ''
    tok = ''
  curses.wrapper(chat_win,user_id,tok)

if __name__ == "__main__":
  main()

