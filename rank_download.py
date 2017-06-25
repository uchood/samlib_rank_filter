# -*- coding: utf-8 -*-
import re
import codecs
import os
import sys
import logging
import traceback
import time
import requests

from bs4 import BeautifulSoup
import gevent
from gevent.queue import Queue

logging.basicConfig(filename="log.log", level=logging.ERROR,
            format="%(levelname)s "
            "[%(asctime)-16s [%(filename)18s:%(lineno)-4s - %(funcName)20s() ]"
            ":[%(name)s:%(lineno)s] %(message)s")

number_of_threads = 10

host = "samlib.ru"
top500 = "/rating/top100/"
page_1_top_100 = "index.shtml"
page_n_top_100 = "index-{}.shtml"


try:
    """fenerate list of pages"""
    count_pages = 159
    q = []
    for x in xrange(count_pages):
        q.append({'num_page': x + 1})

    tasks = Queue()
    result_pages = {}

    for x in q:
        n = x["num_page"]
        page = page_n_top_100.format(n) if not n == 1 else page_1_top_100
        uri = "http://{}{}{}".format(host, top500, page)
        tasks.put_nowait({"num": n, "uri": uri})

    def worker_download_pages(n):
        error_counter = 0
        max_error_counter = 5
        while error_counter < max_error_counter and not tasks.empty():
            try:
                task = tasks.get()
                task["uri"]
                task["num"]
                retry = True
                while retry and error_counter < max_error_counter:
                    try:
                        r = requests.get(task["uri"])
                        print("{}:{} : {}b".format(task["num"], 
                                                   r.status_code, 
                                                   len(r.content)))
                        result_pages[task["num"]] = r.content
                        error_counter = 0
                        retry = False
                    except Exception as e:
                        logging.warning("page [{}] : [{}]".
                                        format(task['num'], e))
                        error_counter += 1
                if error_counter >= max_error_counter:
                    logging.error("page not readed : [{}]: [{}]".
                                  format(task['num'], task['uri']))
                gevent.sleep(0)
            except Exception as e:
                logging.exception("Error in read page: {}".format(e))
                logging.exception(traceback.format_exc())
        print('Quitting time!')

    def info_worker():
        reminder = tasks.qsize()
        last_reminder = reminder
        sleep_interval_in_sec = 1
        while reminder > 10 and not tasks.empty():
            speed = (last_reminder - reminder) / sleep_interval_in_sec
            print("remain {} sequnses: speed {}/seq".format(reminder, speed))
            gevent.sleep(sleep_interval_in_sec)
            last_reminder = reminder
            reminder = tasks.qsize()

    threads = []
    for x in xrange(number_of_threads):
        threads.append(gevent.spawn(worker_download_pages,
                                    "worker_download_pages_{}".format(x)))

    gevent.joinall(threads)

    print(len(result_pages.keys()))
    print(result_pages.keys())

except Exception as e:
    logging.exception("Error in python.py: {}".format(e))
    raise
