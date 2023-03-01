# Built-in modules 
import os
import time
import logging
from datetime import datetime, timedelta

# 3rd party modules
import requests

# Global variables
SERVICE_URL = os.environ.get('SERVICE_URL', 'https://cloud.bastionzero.com')
BASE_URL = f'{SERVICE_URL}/api/v2'
TIMEOUT=300

# Set our logging level
logging.getLogger().setLevel(logging.INFO)

def addSubjectsToPolicy(subjects, clusterName, apiKey):
    """
    Helper function to add subjects to a policy
    :param list(str) subjects: List of IDP subjects
    :param str clusterName: Cluster name to use to register this agent
    :param str apiKey: API Key to use to make HTTPS requests
    """
    logging.info(f'Adding subjects: [{",".join(subjects)}] to policy for cluster: {clusterName}...')
    # First get our policy
    policy = getPolicy(clusterName, apiKey)
    if policy is None:
        logging.info(f'Skipping adding target groups as we could not find the policy for {clusterName}')
        return

    # Now loop over the users, and add each subject
    for subject in subjects:
        # Get the user Id and create our subjectToAdd dict
        try:
            subjectInfo = getSubjectInfoFromEmail(subject, apiKey)
        except Exception:
            logging.warning(f'Error getting user info for {subject}. Ensure you used the right email. Skipping...')
            continue
        
        subjectToAdd = {
            'id': subjectInfo['id'],
            'type':  subjectInfo['type']
        }
        if subjectInfo['id'] not in [subject['id'] for subject in policy['subjects']]:
            policy['subjects'].append(subjectToAdd)
        else:
            logging.warning(f'Skipping {subject} as the policy already has them as a subject')
    
    # Now update the policy
    updatePolicy(policy, apiKey)
    logging.info(f'Finished updating subjects!')

def addTargetUsersToPolicy(targetUsers, clusterName, apiKey):
    """
    Helper funnction to add targetUsers to a policy
    :param list(str) targetUsers: List of kube Target users
    :param str clusterName: Cluster name to use to register this agent
    :param str apiKey: API Key to use to make HTTPS requests
    """
    logging.info(f'Adding targetUsers: [{",".join(targetUsers)}] to policy for cluster: {clusterName}...')
    # First get our policy
    policy = getPolicy(clusterName, apiKey)
    if policy is None:
        logging.info(f'Skipping adding target groups as we could not find the policy for {clusterName}')
        return

    # Now loop over the users, and add each subject
    for targetUser in targetUsers:
        # Update the key in the context
        if targetUser not in [clusterUser['name'] for clusterUser in policy['clusterUsers']]:
            policy['clusterUsers'].append({
                'name': targetUser
            })
        else:
            logging.warning(f'Skipping {targetUser} as the policy already has them as a targetUser')
    
    # Now update the policy
    updatePolicy(policy, apiKey)
    logging.info(f'Finished updating targetUsers!')

def addTargetGroupsToPolicy(targetGroups, clusterName, apiKey):
    """
    Helper funnction to add targetGroups to a policy
    :param list(str) targetGroups: List of kube Target users
    :param str clusterName: Cluster name to use to register this agent
    :param str apiKey: API Key to use to make HTTPS requests
    """
    logging.info(f'Adding targetGroups: [{",".join(targetGroups)}] to policy for cluster: {clusterName}...')
    # First get our policy
    policy = getPolicy(clusterName, apiKey)
    if policy is None:
        logging.info(f'Skipping adding target groups as we could not find the policy for {clusterName}')
        return

    # Now loop over the users, and add each subject
    for targetGroup in targetGroups:
        # Update the key in the context
        if targetGroup not  in [clusterGroups['name'] for clusterGroups in policy['clusterGroups']]:
            policy['clusterGroups'].append({
                'name': targetGroup
            })
        else:
            logging.warning(f'Skipping {targetGroup} as the policy already has them as a targetGroup')
    
    # Now update the policy
    updatePolicy(policy, apiKey)
    logging.info(f'Finished updating targetGroups!')

def makeJsonPostRequest(endpoint, apiKey, json={}):
    """
    Helper function to make post request
    :param str endpoint: Endpoint to hit
    :param str apiKey: Api key to use to build header
    :param dict json: Optional json data
    """
    headers = {'X-API-KEY': apiKey, 'Content-Type': 'application/json'}

    resp = requests.post(
        f'{BASE_URL}/{endpoint}',
        headers=headers,
        json=json
    )
    resp.raise_for_status()

    toReturn = resp.json()
    if type(toReturn) is not list and 'errorType' in toReturn.keys():
        logging.error(f'Error making post request for endpoint: {endpoint}. Error: {toReturn["errorMsg"]}')
        raise Exception()
    
    return toReturn

def makeJsonPatchRequest(endpoint, apiKey, json={}):
    """
    Helper function to make patch request
    :param str endpoint: Endpoint to hit
    :param str apiKey: Api key to use to build header
    :param dict json: Optional json data
    """
    headers = {'X-API-KEY': apiKey, 'Content-Type': 'application/json'}

    resp = requests.patch(
        f'{BASE_URL}/{endpoint}',
        headers=headers,
        json=json
    )
    resp.raise_for_status()

    toReturn = resp.json()
    if type(toReturn) is not list and 'errorType' in toReturn.keys():
        logging.error(f'Error making patch request for endpoint: {endpoint}. Error: {toReturn["errorMsg"]}')
        raise Exception()
    
    return toReturn

def makeJsonGetRequest(endpoint, apiKey):
    """
    Helper function to make get request
    :param str endpoint: Endpoint to hit
    :param str apiKey: Api key to use to build header
    :param dict json: Optional json data
    """
    headers = {'X-API-KEY': apiKey, 'Content-Type': 'application/json'}

    resp = requests.get(
        f'{BASE_URL}/{endpoint}',
        headers=headers
    )
    resp.raise_for_status()

    toReturn = resp.json()
    if type(toReturn) is not list and 'errorType' in toReturn.keys():
        logging.error(f'Error making get request for endpoint: {endpoint}. Error: {toReturn["errorMsg"]}')
        raise Exception()
    
    return toReturn

def makeDataGetRequest(endpoint, apiKey, data={}):
    """
    Helper function to make post request
    :param str endpoint: Endpoint to hit
    :param str apiKey: Api key to use to build header
    :param dict json: Optional json data
    """
    headers = {'X-API-KEY': apiKey, 'Content-Type': 'application/json'}
    resp = requests.get(
        f'{BASE_URL}/{endpoint}',
        headers=headers,
        data=data
    )
    resp.raise_for_status()
    
    toReturn = resp.json()
    if type(toReturn) is not list and 'errorType' in toReturn.keys():
        logging.error(f'Error making get request for endpoint: {endpoint}. Error: {toReturn["errorMsg"]}')
        raise Exception()
    
    return toReturn

def getSubjectInfoFromEmail(subjectEmail, apiKey):
    """
    Helper function to get a subject id from their email
    :ret dict: Subject info including email, Id, and type
    """
    return makeJsonGetRequest(f'subjects/{subjectEmail}', apiKey)

def getPolicy(clusterName, apiKey):
    """
    Helper function to get the policy for us
    :param str clusterName: Cluster name to use to register this agent
    :param str apiKey: API Key to use to make HTTPS requests
    :ret dict: Dict of policy
    """
    # List all our policies
    policyList = makeJsonGetRequest('policies/kubernetes', apiKey)

    # Loop till we find the one we want 
    policyName = f'{clusterName}-policy'
    for policy in policyList:
        if policy['name'] == policyName:
            return policy

def updatePolicy(policy, apiKey):
    """
    Helper function to update a policy
    :param dict policy: Updated policy
    :param str apiKey: Api key to use to make HTTPS requests
    """
    makeJsonPatchRequest(f'policies/kubernetes/{policy["id"]}', apiKey, policy)

def checkAgentOnlineBastion(apiKey, clusterName):
    """
    Helper function to see if an agent is online via BastionZero
    :param str apiKey: API Key to use to make HTTPS requests
    :param str clusterName: Cluster name to use to register this agent
    """
    logging.info(f'Checking to see if agent: {clusterName} has come online in BastionZero. Timeout set to: {TIMEOUT}...')

    # Keep making our POST request until we see our agent online
    agentOnline = False
    startTime = datetime.now()
    while not agentOnline and datetime.now() - startTime < timedelta(seconds=TIMEOUT):
        # Get the list of agent info
        clusters = makeDataGetRequest('targets/kube', apiKey)

        if type(clusters) is not list and 'errorType' in clusters.keys():
            logging.error(f'Error making post request to get cluster list: {clusters["errorMsg"]}')
            raise Exception()

        # Loop through the list, if we see our clusterName see if its online
        for cluster in clusters:
            if cluster['name'] == clusterName:
                if cluster['status'] == 'Online':
                    agentOnline = True
                    continue
        
        # Else sleep for a bit and wait for the agent to come online
        if not agentOnline:
            logging.info(f'Still waiting...')
            time.sleep(2)
        
    if not agentOnline:
        logging.error(f'Agent: {clusterName} never came online!')
        raise Exception()

    logging.info(f'Agent: {clusterName} has come online!')