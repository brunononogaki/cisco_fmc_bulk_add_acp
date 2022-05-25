import ast
import sys

import requests


#################################################################################################
# CONNECTION
#################################################################################################
def make_connection(fmc):
    """
    This method creates a connection to a FMC and get the auth_token, refresh_token and domain list
    :return: auth_token, refresh_token, domain_list
    """
    headers = {"Content-Type": "application/json"}
    api_auth_path = "/api/fmc_platform/v1/auth/generatetoken"
    auth_url = "https://" + fmc.ipaddr + api_auth_path
    domain_list = []

    try:
        r = requests.post(
            auth_url,
            headers=headers,
            auth=requests.auth.HTTPBasicAuth(fmc.username, fmc.password),
            verify=False,
        )
        auth_headers = r.headers
        auth_token = auth_headers.get("X-auth-access-token", default=None)
        refresh_token = auth_headers.get("X-auth-refresh-token", default=None)
        domains = ast.literal_eval(auth_headers.get("DOMAINS", default=None))
        for domain in domains:
            domain_list.append(domain)
        if auth_token == None:
            print("auth_token not found. Exiting...")
            sys.exit()
    except Exception as err:
        print("Error in generating auth token --> " + str(err))
        sys.exit()
    return auth_token, refresh_token, domain_list


def refresh_token(fmc, auth_token, refresh_token):
    """
    This method refreshes the Authentication Token and get a new auth_token, refresh_token and domain_uuid
    :return: auth_token, domain_uuid, refresh_token
    """
    headers = {
        "Content-Type": "application/json",
        "X-auth-access-token": auth_token,
        "X-auth-refresh-token": refresh_token,
    }
    api_auth_path = "/api/fmc_platform/v1/auth/refreshtoken"
    auth_url = "https://" + fmc.ipaddr + api_auth_path

    try:
        r = requests.post(
            auth_url,
            headers=headers,
            auth=requests.auth.HTTPBasicAuth(fmc.username, fmc.password),
            verify=False,
        )
        auth_headers = r.headers
        auth_token = auth_headers.get("X-auth-access-token", default=None)
        refresh_token = auth_headers.get("X-auth-refresh-token", default=None)
        if auth_token == None:
            auth_token, refresh_token, domain_uuid = make_connection()
    except Exception as err:
        print("Error in generating auth token --> " + str(err))
        sys.exit()
    print("Token refreshed")
    return auth_token, refresh_token


def validade_token(json_resp):
    """
    This method parses the JSON result of a request to check if the access token is still valid
    :return: True (valid) or False (not valid)
    """
    try:
        if json_resp["error"]["messages"][0]["description"] == "Access token invalid.":
            return False
        else:
            return True
    except:
        return True
