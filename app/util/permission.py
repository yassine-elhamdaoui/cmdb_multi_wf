# -*- coding: utf-8 -*-
"""Authservice module for user authorization."""

import traceback
import requests
from fastapi import Request
from fastapi import status, HTTPException
import os
from json import JSONDecodeError


PERMISSION_DICT = {
    "cmdb_customer_read": {
        "platform_object_type": "platform",      
        "platform_object_id": "0",             
        "permission": "cmdb_customer_read" 
    },
    "cmdb_service_read": {
        "platform_object_type": "platform",
        "platform_object_id": "0",
        "permission": "cmdb_service_read"
    },
    "cmdb_environment_read": {
        "platform_object_type": "platform",
        "platform_object_id": "0",
        "permission": "cmdb_environment_read"
    },
    "cmdb_contact_read": {
        "platform_object_type": "platform",
        "platform_object_id": "0",
        "permission": "cmdb_contact_read"
    },
    "cmdb_user_roles_read": {
        "platform_object_type": "platform",
        "platform_object_id": "0",
        "permission": "cmdb_user_roles_read"
    },
    "cmdb_asset_read": {
        "platform_object_type": "platform",
        "platform_object_id": "0",
        "permission": "cmdb_asset_read"
    },
    "cmdb_contract_read": {
        "platform_object_type": "platform",
        "platform_object_id": "0",
        "permission": "cmdb_contract_read"
    },
    "cmdb_sr_read": {
        "platform_object_type": "platform",
        "platform_object_id": "0",
        "permission": "cmdb_sr_read"
    },
    "cmdb_rfc_read": {
        "platform_object_type": "platform",
        "platform_object_id": "0",
        "permission": "cmdb_rfc_read"
    }
}


#for User Validation
def validate_permission_user(request: Request, feature: str, user_details: dict, org_obj_id: str = None):
    """Function to validate user permission for given feature

    Args:
        request (Request): FastAPI request object containing details of client request including auth bearer token
        feature (str): Feature for which the user permission is to be validated
                        supported features: dashboard_read, tenancy_read
        user_details (dict): A dictionary containing user details. The AuthN reponse of valid user
        org_obj_id (str): Organization object ID. Applicable only for
                         tenancy/inventory permission checks.

    Returns:
        Boolean: Returns True if user is authorized to access the feature, else returns False
    """
    # return True
    user_email = user_details['account']['email']
    try:
        feature = feature.lower()
        supported_feature_list = ["CMDB_CUST_READ", "CMDB_SVC_READ",]
        print(f"Validating permissions for {user_email} user to access {feature} feature.")
        if feature not in supported_feature_list:
            err_msg = f"Invalid feature '{feature}', supported features are {supported_feature_list}"
            print(err_msg)
            raise Exception(err_msg)
        permission_details = PERMISSION_DICT[feature]

 
        print(f"Permission details for {feature} feature are {permission_details}")


        
        bearer_token = request.headers.get('authorization')
        headers = {
            "accept": "application/json",
            "Authorization": bearer_token,
            "Content-Type": "application/json"
        }
        payload = {
            "subject": {
                "object_type": "user",
                "object_id": user_details["account"]["id"]
            },
            "object": {
                "object_type": permission_details['platform_object_type'],
                "object_id": permission_details['platform_object_id']
            },
            "permission": permission_details['permission']
        }
        authz_base_url = os.getenv("BASE_URL")
        response = requests.post(
            f'{authz_base_url}/v1/permissions/check',
            headers=headers, json=payload, verify=False)
        print(f"AuthZ request completed in {response.elapsed.total_seconds()} seconds")
        authz_status = response.json()
        print(f"Response from AuthZ service: {authz_status}")
        if response.status_code != 200 or not authz_status:
            print("Authz failed : user %s does not have %s permission of %s , AuthZ status_code %s" % (
                        user_email, payload['permission'],
                        payload['object']['object_type'],
                        response.status_code))
            return False
            # response_body = "User %s does not have %s permissions" % (
            #     user_email, payload['permission'])
            # raise HTTPException(detail=response_body,
            #                     status_code=status.HTTP_403_FORBIDDEN)
        print("User %s is authorized for %s permission of %s feature with status code : %s" % (
            user_email, payload['permission'], feature, response.status_code))
        return True
    except Exception as ex:
        print("Exception while %s user authorization for %s feature: %s" % (
            user_email, feature, traceback.format_exc()))
        return False
        # raise HTTPException(detail="Authorization failed : User %s does not have permissions to access this feature" % user_email,
        #                     status_code=status.HTTP_403_FORBIDDEN)




""" Example payload for client verification
{
  "object": {
    "object_type": "platform",
    "object_id": "0"
  },
  "subject": {
    "object_type": "service",
    "object_id": "ocid1.service_client.oc1..acaibaaagfew2nbwob4hsqlynf5eg5lile4eknkmjr5ekvzqnrjts32cjzid"
  },
  "permission": "cmdb_asset_read"
}
"""

#Function to validate client permission for given feature
def validate_permission_client(request: Request, feature: str, client_ocid: str):


    # return True
    try:
        feature = feature.lower()
        supported_feature_list = list(PERMISSION_DICT.keys())
        #print(f"Validating permissions for {client_ocid} user to access {feature} feature.")
        if feature not in supported_feature_list:
            err_msg = f"Invalid feature '{feature}', supported features are {supported_feature_list}"
            print(err_msg)
            raise Exception(err_msg)
        permission_details = PERMISSION_DICT[feature]
 
        #print(f"Permission details for {feature} feature are {permission_details}")
        
        bearer_token = request.headers.get('authorization')
        headers = {
            "accept": "application/json",
            "Authorization": bearer_token,
            "Content-Type": "application/json"
        }
        payload = {
            "object": {
                "object_type": permission_details['platform_object_type'],
                "object_id": permission_details['platform_object_id']
            },
             "subject": {
                "object_type": "service",
                "object_id": client_ocid
            },           
            "permission": permission_details['permission']
        }
        authz_base_url = os.getenv("BASE_URL")
        authz_url=f'{authz_base_url}/authorization-microservice/v1/permissions/check'
        response = requests.post(authz_url,headers=headers, json=payload, verify=False)
        #print(f"AuthZ request completed in {response.elapsed.total_seconds()} seconds")
        print(response.text)
        authz_status = response.json()
        print(f"Response from AuthZ service: {authz_status}")

        #not permmited
        if response.status_code != 200 or not authz_status:
            print("Authz failed : client %s does not have %s permission of %s , AuthZ status_code %s" % (
                        client_ocid, payload['permission'],
                        payload['object']['object_type'],
                        response.status_code))
            raise HTTPException(detail="Authorization failed : Client %s does not have permissions to access this feature" % client_ocid,
                                status_code=status.HTTP_403_FORBIDDEN)
        
        #permitted
        print("Client %s is authorized for %s permission of %s feature with status code : %s" % (
            client_ocid, payload['permission'], feature, response.status_code))
        return True
    except JSONDecodeError:
        raise HTTPException(detail=f"Invalid JSON response from {authz_url}: {response.text}", status_code=400)
    except Exception as ex:
        print("Exception while %s client authorization for %s feature: %s" % (
            client_ocid, feature, traceback.format_exc()))
        raise HTTPException(detail=ex.detail,status_code = ex.status_code)


def find_permission(entity, permission):
    entity_lower = entity.lower()
    permission_lower = permission.lower()

    for key in PERMISSION_DICT.keys():
        if entity_lower in key.lower():
            if permission_lower in key.lower():
                return key
            
    return None