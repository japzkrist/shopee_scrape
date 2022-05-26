import requests
import json

import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import os


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

out_file = 'current_data.json'
dif_file = 'diff_data.json'

token = '<telegram bot token>'

shop = '<shop name>'
get_id_url = 'https://shopee.co.id/api/v4/shop/get_shop_detail?username={}'.format(
    shop)
ref = 'https://shopee.co.id/{}'.format(shop)

headers = {

    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'X-API-SOURCE': 'pc',
    'Cache-Control': 'no-cache'
}


current_item_list = []
last_item_list = []

s = requests.Session()

s.get(ref, headers=headers)
id = s.get(get_id_url, headers=headers)
id = json.loads(id.text)
id = id['data']['shopid']


def print_diff(obj):
    print(obj['name'])
    for o in obj['model']:
        print("\t" + o['name'])
        print("\tstock: " + str(o['stock']))
        print('\n')


def get_items(count, send):
    global current_item_list

    url = 'https://shopee.co.id/api/v4/search/search_items?by=relevancy&match_id=' + id + \
        '&limit=100&newest=' + \
        str(count) + '&order=desc&page_type=shop&scenario=PAGE_OTHERS&version=2'
    print('url: {}'.format(url))

    req = s.get(url, headers=headers, verify=False)

    res = json.loads(req.text)
    items = len(res['items'])

    tot = res['total_count']

    new_item_list = []
    prn = []
    prn.clear()
    for item in res['items']:

        url = 'https://shopee.co.id/api/v4/item/get?itemid=' + \
            str(item['item_basic']['itemid']) + '&shopid=' + \
            str(item['item_basic']['shopid'])
        req_det = s.get(url, headers=headers, verify=False)

        res_det = json.loads(req_det.text)

        model_list = []

        try:
            models = res_det['data']['models']
        except:
            models = []
        n_list = {
            'item': item,
            'models': models
        }

        fnd = False
        print('find itemid')
        print(item['itemid'])

        for cr_lst in current_item_list:

            if cr_lst['item']['item_basic']['itemid'] == item['itemid']:
                fnd = True
                break
        if not fnd:

            print('itemid not found')

            current_item_list.append(n_list)
            new_item = {
                'name': item['item_basic']['name'],
                'model': n_list['models']
            }
            prn.append(new_item)
            print('itemid add new')
            if send:
                print_diff(prn)

            continue

        print('itemid found')
        print(cr_lst['item']['item_basic']['name'])
        mdl_tmp = cr_lst['models']
        n_mdl = []
        n_mdl.clear()
        for m1 in n_list['models']:
            for mdl in mdl_tmp:
                if mdl['name'] == m1['name'] and mdl['stock'] != m1['stock']:
                    n_mdl.append(m1)

                    print(m1['name'])
                    print('different stock')
                    print('current stock: {}'.format(mdl['stock']))
                    print('new stock: {}'.format(m1['stock']))
                    mdl.update({'stock':  m1['stock']})
                    if send:
                        print_diff(prn)
                    break
        if len(n_mdl) > 0:
            new_item = {
                'name': item['item_basic']['name'],
                'model': n_mdl
            }
            prn.append(new_item)

        model_list.clear()
        n_list.clear()

    return tot, items, prn


def get_data():
    global last_item_list

    count = 0

    tot, items, prn = get_items(count, False)

    mod = tot % 100
    while items == 100:
        count += 100
        tot, items, prn1 = get_items(count, False)
        prn.extend(prn1)

    prn = list(filter(None, prn))

    jsonString = json.dumps(current_item_list)
    f = open(out_file, "w")
    f.write(jsonString)
    f.close()

    if prn:
        last_item_list.clear()
        last_item_list.extend(prn)

        jsonString = json.dumps(last_item_list)
        f = open(dif_file, "w")
        f.write(jsonString)
        f.close()

    return prn


def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    lst = get_data()

    print('current item: {}'.format(len(current_item_list)))
    print('new item: {}'.format(len(lst)))
    job = context.job
    msg = ''
    if len(lst) == 0:

        context.bot.send_message(job.context, text='no change')
    else:

        msg = '--------------new items----------------'
        context.bot.send_message(job.context, text=msg)
        msg = ''
        for l in lst:

            msg = msg + '{}\n'.format(l['name'])
            for mm in l['model']:
                msg = msg + \
                    '..name: {}, stock: {}\n'.format(mm['name'], mm['stock'])
                if len(msg) > 3500:
                    context.bot.send_message(job.context, text=msg)
                    msg = ''
        context.bot.send_message(job.context, text=msg)
    lst.clear()


def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    text = ' Bot start!'
    update.message.reply_text(text)


def current(update: Update, context: CallbackContext) -> None:
    msg = '--------------current items----------------'
    update.message.reply_text(text=msg)
    msg = ''
    for l in current_item_list:
        msg = msg + '{}\n'.format(l['item']['item_basic']['name'])
        for mm in l['models']:
            msg = msg + \
                '..name: {}, stock: {}\n'.format(mm['name'], mm['stock'])
            if len(msg) > 3500:
                update.message.reply_text(text=msg)
                msg = ''
    if msg:
        update.message.reply_text(text=msg)


def last(update: Update, context: CallbackContext) -> None:
    msg = '--------------last items----------------'
    update.message.reply_text(text=msg)
    msg = ''

    for l in last_item_list:

        msg = msg + '{}\n'.format(l['name'])
        for mm in l['model']:
            msg = msg + \
                '..name: {}, stock: {}\n'.format(mm['name'], mm['stock'])
            if len(msg) > 3500:
                update.message.reply_text(text=msg)
                msg = ''
    if msg:
        update.message.reply_text(text=msg)


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_timer(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:

        due = int(context.args[0])
        if due < 300:
            update.message.reply_text('min 300s')
            return

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(
            alarm, due, first=10, context=chat_id, name=str(chat_id))

        text = 'Timer successfully set!'
        if job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <seconds>')


def load_last_data():
    global current_item_list
    global last_item_list
    if os.path.exists(out_file) and os.stat(out_file).st_size != 0:
        print('open {}'.format(out_file))
        f = open(out_file, "r")
        from_file = f.read()

        current_item_list.extend(json.loads(from_file))

        f.close()

    if os.path.exists(dif_file) and os.stat(dif_file).st_size != 0:
        print('open {}'.format(dif_file))
        f = open(dif_file, "r")
        from_file = f.read()

        last_item_list.extend(json.loads(from_file))

        f.close()


def main():

    load_last_data()

    lst = get_data()
    print('current item: {}'.format(len(current_item_list)))
    print('new item: {}'.format(len(lst)))

    updater = Updater(token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set", set_timer))
    dp.add_handler(CommandHandler("current", current))
    dp.add_handler(CommandHandler("last", last))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
