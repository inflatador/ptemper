#!/usr/bin/env python
# Copyright 2017 Brian King
# License: Apache

import argparse
import datetime
from getpass import getpass
import hmac
from hashlib import sha256
import json
import keyring
import os
import plac
import re
import requests
import sys
import time
from time import time

def parse_units(duration):
    try:
        duration,unit = filter(None, re.split(r'(\d+)', duration))
    except:
        print ("Syntax error, check your input.")
        sys.exit()
    unit = unit.upper()
    validated_unit = re.match(r"[MHD]", unit)
    if validated_unit:
        return duration, unit
    else:
        print("Invalid time unit. Valid units are M (minute), H (hour), or D (day).")
        sys.exit()

def calculate_ttl(duration,unit):
    if unit == "M": 
        time_multiplier = "1"
    elif unit == "H":
        time_multiplier = "60"
    elif unit == "D":
        time_multiplier = "1440"
    
    time_multiplier=int(time_multiplier)
    duration=int(duration)
    
    duration_in_seconds = duration * time_multiplier * 60
    expires = int(time() + duration_in_seconds)
    return duration_in_seconds

def getset_keyring_credentials(username=None, password=None):
    """Method to retrieve credentials from keyring."""
    username = keyring.get_password("raxcloud", "username" )
    if username is None:
        if sys.version_info.major < 3:
            username = raw_input("Enter Rackspace Username: ")
            keyring.set_password("raxcloud", 'username' , username )
            print ("Username value saved in keychain as raxcloud username.")
        elif creds == "username":        
            username = input("Enter Rackspace Username: ")
            keyring.set_password("raxcloud", 'username' , username )
            print ("Username value saved in keychain as raxcloud username.")
    else:
        print ("Authenticating to Rackspace cloud as %s" % username)
    password = keyring.get_password("raxcloud", "password" )
    if password is None:
        password = getpass("Enter Rackspace API key:")
        keyring.set_password("raxcloud", 'password' , password )
        print ("API key value saved in keychain as raxcloud password.")
    return username, password

def wipe_keyring_credentials(username, password):
    """Wipe credentials from keyring."""
    try:
        keyring.delete_password('raxcloud', 'username')
        keyring.delete_password('raxcloud', 'password')
    except:
        pass

    return True

#Request to authenticate using password
def get_auth_token(username,password):
    #setting up api call
    url = "https://identity.api.rackspacecloud.com/v2.0/tokens"
    headers = {'Content-type': 'application/json'}
    payload = {'auth':{'passwordCredentials':{'username': username,'password': password}}}
    payload2 = {'auth':{'RAX-KSKEY:apiKeyCredentials':{'username': username,'apiKey': password}}}

    #authenticating against the identity
    try:
        r = requests.post(url, headers=headers, json=payload)
    except requests.ConnectionError as e:
        print("Connection Error: Check your interwebs!")
        sys.exit()
        
    
    if r.status_code != 200:
        r = requests.post(url, headers=headers, json=payload2)
        if r.status_code != 200:
            print ("Error! API responds with %d" % r.status_code) 
            print("Rerun the script and you will be prompted to re-enter username/password.")
            wipe_keyring_credentials(username, password)
            sys.exit()
        else:
            print("Authentication was successful!")
    elif r.status_code == 200:
        print("Authentication was successful!")
    
#     elif r.status_code == 400:
#         print("Bad Request. Missing required parameters. This error also occurs if you include both the tenant name and ID in the request.")
#         sys.exit()
#     elif r.status_code == 401:
#         print("Unauthorized. This error message might indicate any of the following conditions:")
#         print("    -You are not authorized to complete this operation.")
#         print("    -Additional authentication credentials required. Submit a second authentication request with multi-factor authentication credentials")
#         sys.exit()
#     elif r.status_code == 403:
#         print("User disabled Forbidden")
#     elif r.status_code == 404:
#         print("Item not found. The requested resource was not found. The subject token in X-Subject-Token has expired or is no longer available. Use the POST token request to get a new token.")
#         sys.exit()
#     elif r.status_code == 500:
#         print("Service Fault. Service is not available")
#         sys.exit()
#     else:
#         print("Unknown Authentication Error")
#         sys.exit()

    #loads json reponse into data as a dictionary.
    data = r.json()
    #assign token and account variables with info from json response.
    auth_token = data["access"]["token"]["id"]
    return auth_token
    
def find_endpoint_and_user(auth_token, region):
    #region is always uppercase in the API response
    region = region.upper()
    #setting up api call
    url = ("https://identity.api.rackspacecloud.com/v2.0/tokens/%s/endpoints" % auth_token)
    headers = {'content-type': 'application/json', 'Accept': 'application/json',
               'X-Auth-Token': auth_token}
    raw_service_catalog = requests.get(url, headers=headers)
    the_service_catalog = raw_service_catalog.json()
    endpoints = the_service_catalog["endpoints"]
    for service in range(len(endpoints)):
#        print endpoints[service]["name"]
        if "cloudFiles" == endpoints[service]["name"] and endpoints[service]["region"] == region:
            cf_endpoint = endpoints[service]["publicURL"]
            cf_username = endpoints[service]["tenantId"]
    return cf_endpoint, cf_username

def get_temp_url_key(cf_endpoint, cf_username, auth_token):
    headers = {'content-type': 'application/json', 'Accept': 'application/json',
               'X-Auth-Token': auth_token}
    # To use tempURLs, we have to have a TempURL metadata key
    temp_url_check = requests.head(url=cf_endpoint, headers=headers)
    temp_url_key = temp_url_check.headers["X-Account-Meta-Temp-Url-Key"]
    return temp_url_key

def check_and_make_container(cf_endpoint, container, cf_object, auth_token):
    headers = {'content-type': 'application/json', 'Accept': 'application/json',
               'X-Auth-Token': auth_token}

    container_url = cf_endpoint + "/" + container
    object_url = container_url + "/" + cf_object

    cf_container = requests.get(url=container_url, headers=headers)

    if cf_container.status_code == 404:
        print ("Container %s does not already exist. Creating..." % container)
        cf_container_put = requests.put(url=container_url, headers=headers)
        # Create a 0-byte object for the file. This will be overwritten by the later PUT
        # command.
        cf_object_put = requests.put(url=object_url, headers=headers)

    else:
        print ("Error! container %s already exists, please pick a new container name and try again" % container)
        sys.exit()

    return object_url

def make_temp_url(duration_in_seconds, object_url, temp_url_key, cf_object, auth_token):
    method = 'PUT'
    expires = int(time() + duration_in_seconds)
    base_url, object_path = object_url.split('/v1/')
    object_path = '/v1/' + object_path
    #  print object_url
    hmac_body = '%s\n%s\n%s' % (method, expires, object_path)
    temp_url_sig = hmac.new(temp_url_key, hmac_body, sha256).hexdigest()
    s = '{object_url}?temp_url_sig={temp_url_sig}&temp_url_expires={expires}'
    temp_url = s.format(object_url=object_url, temp_url_sig=temp_url_sig, expires=expires)
    humandate = datetime.datetime.now() + (datetime.timedelta(seconds=duration_in_seconds))
    # splitting the URL to add snet
    protocol, url = temp_url.split('//')
    snet_temp_url = protocol + "//snet-" + url
    print ("Your new tempURL is %s" % temp_url)
    print ("Your tempURL expires at %s localtime" % humandate) 
    print ("example commands:")
    print ("#curl -vX PUT \"%s\" --data-binary @%s" % (temp_url, cf_object))
    print ("#curl -vX PUT \"%s\" --data-binary @%s" % (snet_temp_url, cf_object))
    print ("Remember, curl tries to put the entire file into memory before copying!")


@plac.annotations(
#    method=plac.Annotation("HTTP verb get, put, or both"),
    duration=plac.Annotation("Time to live for TempURL. Use M for Minutes, H for hours and D for days"),
    region=plac.Annotation("Rackspace datacenter"),
    container=plac.Annotation("name of Cloud Files container to create. Must not already exist."),
    cf_object=plac.Annotation("name of Cloud Files object that will be uploaded via the tempURL")
)

def main(duration, region, container, cf_object):
    duration, unit = parse_units(duration)
    duration_in_seconds = calculate_ttl(duration, unit)
    print (duration_in_seconds)
    username,password = getset_keyring_credentials()
    auth_token = get_auth_token(username,password)
    cf_endpoint, cf_username = find_endpoint_and_user(auth_token, region)
    temp_url_key = get_temp_url_key(cf_endpoint, cf_username, auth_token)
    object_url = check_and_make_container(cf_endpoint, container, cf_object, auth_token)
    make_temp_url(duration_in_seconds, object_url, temp_url_key, cf_object, auth_token)


if __name__ == '__main__':
    plac.call(main)
