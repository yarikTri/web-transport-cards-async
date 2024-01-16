from django.shortcuts import render
from django.http import HttpResponse
import requests
import time
import random
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from concurrent import futures

FAIL_PROBABILITY = 0.3
CORRECT_STATE_TO_WRITE = 'approved'
RETRIES_AMOUNT = 3
SERVICE_TICKET_NAME = 'X-Service-Ticket'
SERVICE_TICKET_VALUE = 'Q5%7&fG*'

executor = futures.ThreadPoolExecutor(max_workers=1)

def callback_url(id):
    return f'http://localhost:8080/tickets/{id}/update_write_state'

def update_write_state(state, retries):
    code = 0
    tries_counter = 0
    while code != 200 and tries_counter < retries:
        resp = requests.put(
            url = callback_url(state["id"]),
            json = { 'state': state['state'] },
            timeout = 3,
            headers = { SERVICE_TICKET_NAME: SERVICE_TICKET_VALUE },
        )

        print(f'\n{tries_counter}: Main service response to update write state: {resp.json()}')
    
        code = resp.status_code
        tries_counter += 1

    if tries_counter == retries:
        raise SystemError(f"Can't update write state of ticket with id {state['id']}: code - {code}")

def do_long_writing(ticket_id):
    print('Starting long process of writting...')
    time.sleep(7)
    print('Almost done...')
    time.sleep(3)
    print('Long process of writing done!')

    return {
        'id': ticket_id,
        'state': get_write_res()
    }

def get_write_res():
    if random.random() < FAIL_PROBABILITY:
        return 'fail'
    return 'success'

def result_callback(task):
    result = task.result()
    update_write_state(result, RETRIES_AMOUNT)

@api_view(['POST'])
def write_ticket(request, id):  
    ticketResp = requests.get(f'http://localhost:8080/tickets/{id}', headers={ SERVICE_TICKET_NAME: SERVICE_TICKET_VALUE })
    ticket = ticketResp.json()
    if ticket['state'] != CORRECT_STATE_TO_WRITE:
        return HttpResponse(f'Invalid ticket state "{ticket['state']}"', status=400)

    update_write_state("updating", RETRIES_AMOUNT)

    task = executor.submit(do_long_writing, id)
    task.add_done_callback(result_callback)

    return HttpResponse("Async job started")
