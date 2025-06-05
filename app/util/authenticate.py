import requests
from app.util import osutil
from fastapi import  HTTPException ,Request, status
import traceback
import os
from json import JSONDecodeError


def validate_token(var_token: str, scope: str):
    client_url = os.getenv("BASE_URL")
    print("token url --> %s", client_url)
    token = 'Bearer ' + var_token
    response = requests.get(client_url, headers={
        "accept": "application/json",
        "Authorization": token})
    oauth_token_valid_response = response.json()
    print(oauth_token_valid_response)
    # print (oauth_token_valid_response)
    if "account" in oauth_token_valid_response:
        return oauth_token_valid_response["account"]["is_active"]

    else:
        return False



#Function to authenticate API by bearer token-AuthN
def authorize_request(request: Request):

    try:
        print("Validating user")
        bearer_token = request.headers.get('authorization')

        headers = {
            'accept': 'application/json',
            'Authorization': bearer_token
        }

        user_ms_base_url = os.getenv("BASE_URL") #'https://omcs-ssp2-pre-dev.opc.oracleoutsourcing.com'
        print(user_ms_base_url)
        authn_url = f'{user_ms_base_url}/user-microservice/v1/principal'
        response = requests.get(authn_url, headers=headers, verify=False)
        #print(f"AuthN request completed in {response.elapsed.total_seconds()} seconds")
        print(f"Response status from user management {response.status_code}")

        Authorization_details = response.json()
        #print(f"Response from AuthN service: {Authorization_details}")
        if response.status_code != 200:
            print("Invalid user, AuthN status_code %s " % response.status_code)
            response_body = Authorization_details.get("detail", "Could not validate credentials or account unauthorised")
            raise HTTPException(detail=response_body, status_code=response.status_code)
        
        #for response.status_code = 200, bool
        is_active = Authorization_details.get('account', {}).get('is_active')
        account_id = Authorization_details.get('account', {}).get('id')
        return is_active, account_id

        #return Authorization_details["account"]["is_active"]
    except JSONDecodeError:
        raise HTTPException(detail=f"Invalid JSON response from {authn_url}: {response.text}", status_code=400)
    except Exception as ex:
        print("Exception while user authentication : %s" % traceback.format_exc())
        raise HTTPException(detail=ex.detail,status_code = ex.status_code)

