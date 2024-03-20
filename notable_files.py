import requests
import time
from xml.etree import ElementTree as ET
from conf import *
import splunklib.client as client


# Notable event status to ID mapping
STATUS_NEW        = "0"
STATUS_PENDING    = "1"
STATUS_INPROGRESS = "2"
STATUS_RESOLVED   = "3"
STATUS_CLOSED     = "4"

#searches notable index
def searchNotables(splunkSearch, earliest_time, latest_time):
   url=SPLUNK_HOST+"/services/search/jobs"
   adhoc_search_level="fast"

   headers = {'adhoc_search_level': adhoc_search_level, "search": splunkSearch}

   response = requests.post(url, auth=SPLUNK_AUTH, data=headers, verify=False)

   if response.status_code == 201:
      searchSid = ET.fromstring(response.text).find('sid').text
      return searchSid
   else:
      print("Status: " + str(response.status_code))
      print(response.reason)
      return None
   
#gets state of event given searchid
def getSearchStatus(searchSid):
   url=SPLUNK_HOST+"/services/search/jobs/" + searchSid
   response = requests.post(url, auth=SPLUNK_AUTH, verify=False)

   if response.status_code == 200:
      return ET.fromstring(response.text).find('.//*[@name="dispatchState"]').text

   return None

#waits for search completion
def waitForSearchCompletion(searchSid):
   status=getSearchStatus(searchSid)

   while status != "DONE":
      status=getSearchStatus(searchSid)
      time.sleep(3)

#updates notable events with changes specified in comment, status, urgency and owner
def updateNotables(comment, status=None, urgency=None, owner=None, eventIDs=None, searchSid=None):
   username = ''
   password = ''
   baseurl = ''
   
   auth_req = requests.post(baseurl + 'services/auth/login', data={'username': username, 'password': password, 'output_mode': 'json'}, verify=False)
   sessionKey = auth_req.json()['sessionKey']

   # Make sure that the session ID was provided
   if sessionKey is None:
      raise Exception("A session key was not provided")
 
   # Make sure that rule IDs and/or a search ID is provided
   if eventIDs is None and searchSid is None:
      raise Exception("ID's not provided")
 
   # These the arguments to the REST handler
   args = {}
   args['comment'] = comment
 
   if status is not None:
      args['status'] = status
 
   if urgency is not None:
      args['urgency'] = urgency
 
   if owner is not None:
      args['newOwner'] = owner
 
   # Provide the list of event IDs that you want to change:
   if eventIDs is not None:
      args['ruleUIDs'] = eventIDs
 
   # If you want to manipulate the notable events returned by a search then include the search ID
   if searchSid is not None:
      args['searchID'] = searchSid

   auth_header = {'Authorization': 'Splunk %s' % sessionKey}

   args['output_mode'] = 'json'
   mod_notables = requests.post(baseurl + 'services/notable_update', data=args, headers=auth_header, verify=False)

   print(mod_notables.json())
   return mod_notables.json()
