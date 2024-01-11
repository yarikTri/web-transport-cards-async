from django.shortcuts import render
from django.http import HttpResponse
import requests
import time
import random
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from concurrent import futures

FAIL_PROBABILITY = 0.1
CORRECT_STATE_TO_FINALIZE = 'approved'
RETRIES_AMOUNT = 3

executor = futures.ThreadPoolExecutor(max_workers=1)

def callback_url(id):
    return f'http://localhost:8080/tickets/{id}/finalize_writing'

def do_long_writing(ticket_id):
    print('Starting long process of writting...')
    time.sleep(7)
    print('Almost done...')
    time.sleep(3)
    print('Long process of writing done!')

    return {
        'id': ticket_id,
        'res': get_res()
    }

def get_res():
    if random.random() < FAIL_PROBABILITY:
        return 'fail'
    return 'success'

def result_callback(task):
    result = task.result()

    code = 0
    tries_counter = 0
    while code != 200 and tries_counter < RETRIES_AMOUNT:
        resp = requests.put(
            url = callback_url(result["id"]),
            json = { 'state': result['res'] },
            timeout = 3,
            headers = { 'X-SERVICE': 'true' },
        )
        
        print(f'\nMain service response: {resp.json()}')
    
        code = resp.status_code
        tries_counter += 1

@api_view(['POST'])
def write_ticket(request, id):  
    ticketResp = requests.get(f'http://localhost:8080/tickets/{id}', headers={'X-SERVICE': 'true'})
    ticket = ticketResp.json()
    if ticket['state'] != CORRECT_STATE_TO_FINALIZE:
        return HttpResponse(f'Invalid ticket state "{ticket['state']}"', status=400)

    task = executor.submit(do_long_writing, id)
    task.add_done_callback(result_callback)

    return HttpResponse("Async job started")
