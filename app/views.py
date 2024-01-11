from django.shortcuts import render
from django.http import HttpResponse
import requests
import time
import random
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from concurrent import futures

FAIL_PROBABILITY = 30

executor = futures.ThreadPoolExecutor(max_workers=1)

def callback_url(id):
    return f'http://localhost:8080/tickets/{id}/finalize_writing'

def do_long_processing(id):
    print('Starting long processing...')
    time.sleep(5)
    print('Success or fail...')
    time.sleep(5)
    print('Long processing done')

    return {
        'id': id,
        'res': get_res()
    }

def get_res():
    if random.random() * 100 < FAIL_PROBABILITY:
        return 'fail'
    return 'success'

def result_callback(task):
    result = task.result()

    resp = requests.put(callback_url(result["id"]), json={'state': result['res']}, timeout=3, headers={'X-SERVICE': 'true'})
    print(f'\nMain service resp: {resp.json()}')

@api_view(['POST'])
def write_ticket(request, id):  
    ticketResp = requests.get(f'http://localhost:8080/tickets/{id}', headers={'X-SERVICE': 'true'})
    ticket = ticketResp.json()
    if ticket['state'] != 'approved':
        raise KeyError(f'Invalid ticket state {ticket['state']}')
      
    task = executor.submit(do_long_processing, id)
    task.add_done_callback(result_callback)

    return HttpResponse("Async job started")
