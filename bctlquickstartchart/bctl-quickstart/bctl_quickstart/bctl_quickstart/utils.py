# Built-in modules 
import yaml 
import subprocess
import time
import json
import logging
from datetime import datetime, timedelta

# 3rd party modules
import requests
from kubernetes import client, config, utils, watch

# Global variables
BASE_URL = 'https://cloud.bastionzero.com/api/v1'
TIMEOUT=300

# Set our logging level
logging.getLogger().setLevel(logging.INFO)

def addUsersToPolicy(users, clusterName, apiKey):
    """
    Helper funnction to add users to a policy
    :param list(str) users: List of IDP users
    :param str clusterName: Cluster name to use to register this agent
    :param str apiKey: API Key to use to make HTTPS requests
    """
    logging.info(f'Adding users: [{",".join(users)}] to policy for cluster: {clusterName}...')
    # First get our policy
    policy = getPolicy(clusterName, apiKey)

    # Now loop over the users, and add each subject
    for user in users:
        # Get the user Id and create our subjectToAdd dict
        try:
            userInfo = getUserInfoFromEmail(user, apiKey)
        except Exception:
            logger.warning(f'Error getting user info for {user}. Ensure you used the right email. Skipping...')
            continue
        
        subjectToAdd = {
            'id': userInfo['id'],
            'type': 'User'
        }
        if subjectToAdd not in policy['subjects']:
            policy['subjects'].append(subjectToAdd)
        else:
            logging.warning(f'Skipping {user} as the policy already has them as a subject')
    
    # Now update the policy
    updatePolicy(policy, apiKey)
    logging.info(f'Finished updating users!')

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

    # Now loop over the users, and add each subject
    for targetUser in targetUsers:
        # Update the key in the context
        if targetUser not in policy['context']['clusterUsers'].keys():
            policy['context']['clusterUsers'][targetUser] = {
                'name': targetUser
            }
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

    # Now loop over the users, and add each subject
    for targetGroup in targetGroups:
        # Update the key in the context
        if targetGroup not in policy['context']['clusterGroups'].keys():
            policy['context']['clusterGroups'][targetGroup] = {
                'name': targetGroup
            }
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
    toReturn = requests.post(
        f'{BASE_URL}/{endpoint}',
        headers=headers,
        json=json
    ).json()

    if type(toReturn) is not list and 'errorType' in toReturn.keys():
        logging.error(f'Error making post request for endpoint: {endpoint}. Error: {toReturn["errorMsg"]}')
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
    toReturn = requests.get(
        f'{BASE_URL}/{endpoint}',
        headers=headers,
        data=data
    ).json()

    if type(toReturn) is not list and 'errorType' in toReturn.keys():
        logging.error(f'Error making get request for endpoint: {endpoint}. Error: {toReturn["errorMsg"]}')
        raise Exception()
    
    return toReturn

def getUserInfoFromEmail(userEmail, apiKey):
    """
    Helper function to get a users id from their email
    :ret dict: Users info including email and Id
    """
    return makeJsonPostRequest('kube/get-user', apiKey, {'email': userEmail})

def getPolicy(clusterName, apiKey):
    """
    Helper function to get the policy for us
    :param str clusterName: Cluster name to use to register this agent
    :param str apiKey: API Key to use to make HTTPS requests
    :ret dict: Dict of policy
    """
    # List all our policies
    policyList = makeJsonPostRequest('Policy/list', apiKey)

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
    # First json seralize the context 
    jsonSerializedContext = json.dumps(policy['context'])
    policy['context'] = jsonSerializedContext

    # Now update the metadata key -> policyMetadata
    policy['policyMetadata'] = policy.pop('metadata')

    makeJsonPostRequest('Policy/edit', apiKey, policy)

def getAgentEnvVars(apiKey, clusterName, namespace):
    """
    Helper funnction to get agent env vars from BastionZero
    :param str apiKey: API Key to use to make HTTPS requests
    :param str clusterName: Cluster name to use to register this agent
    :param str namespace: Namespace we are in
    :ret list(str, str): Touble of env var name : var value
    """
    logging.info(f'Getting agent yaml from BastionZero for agent name: {clusterName}...')
    # Build our headers
    headers = {'X-API-KEY': apiKey, 'Content-Type': 'application/json'}

    # Make our POST request and get the yaml
    agentYaml = makeJsonPostRequest('kube/get-agent-yaml', apiKey, {
        'ClusterName': clusterName,
        'Labels': {
            'cluster-name': f'{clusterName}-bzero'
        },
        'Namespace': namespace
    })['yaml']

    # Now get all the env vars and add it to a list
    envVarsUnformatted = [k8s_type['spec']['template']['spec']['containers'][0]['env'] for k8s_type in yaml.load_all(agentYaml, Loader=yaml.FullLoader) if k8s_type['kind'] == 'Deployment'][0]
    return [(envVar['name'], envVar['value']) for envVar in envVarsUnformatted]

def updateAgentEnvVars(agentEnvVars, deploymentName, namespace, clusterName):
    """
    Helper function to update our agent env vars
    :param list(str, str) agentEnvVars: Agent env vars to apply
    :param str deploymentName: Deployment name of the agent we are starting
    :param str namespace: Namespace we are in
    :param str clusterName: Cluster name we are looking for
    """
    logging.info(f'Updating agent env vars for deployment: {deploymentName}...')
    # Lets load our kube config
    config.load_incluster_config()
    k8s_client = client.ApiClient()

    # Now loop through the list of env vars and update the deployment
    envVarUpdate = ""
    for name, value in agentEnvVars:
        envVarUpdate += f' {name}={value}'
    
    try:
        subprocess.check_call(f'kubectl set env deployment/{deploymentName} -n {namespace} {envVarUpdate}', shell=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f'Error updating deployment {deploymentName} with env vars: {agentEnvVars}')
        raise Exception()
    
    logging.info(f'Waiting for {deploymentName} to be ready. Timeout set to: {TIMEOUT} seconds...')
    # Now wait for it to become ready and start
    w = watch.Watch()
    core_v1 = client.CoreV1Api()
    appNameTag = f'bctl-{clusterName}-agent'
    for event in w.stream(func=core_v1.list_namespaced_pod,
                            namespace=namespace,
                            label_selector=f'app={appNameTag}',
                            timeout_seconds=TIMEOUT):
        podTag = event['object'].metadata.labels['app']
        if podTag != appNameTag:
            pass 

        if event["object"].status.phase == "Running":
            w.stop()
            logging.info(f'{clusterName} agent is ready!')
            return
        
        logging.info(f'Still waiting...')

def checkAgentOnlineBastion(apiKey, clusterName):
    """
    Helper function to see if an agent is online via BastionZero
    :param str apiKey: API Key to use to make HTTPS requests
    :param str clusterName: Cluster name to use to register this agent
    """
    logging.info(f'Checking to see if agent: {clusterName} has come online in BastionZero. Timeout set to: {TIMEOUT}...')
    # Build our headers
    headers = {'X-API-KEY': apiKey, 'Content-Type': 'application/json'}

    # Keep making our POST request until we see our agent online
    agentOnline = False
    startTime = datetime.now()
    while not agentOnline and datetime.now() - startTime < timedelta(seconds=TIMEOUT):
        # Get the list of agent info
        clusters = makeDataGetRequest('kube/list', apiKey)

        if type(clusters) is not list and 'errorType' in clusters.keys():
            logging.error(f'Error making post request to get cluster list: {clusters["errorMsg"]}')
            raise Exception()

        # Loop through the list, if we see our clusterName see if its online
        for cluster in clusters:
            if cluster['clusterName'] == clusterName:
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

def skipIfAlreadyExists(e):
    """
    Helper function to skip if the exception states the object already exists
    Ref: https://stackoverflow.com/questions/45926889/with-python-kubernetes-client-how-to-replicate-kubectl-create-f-generally
    :param Exception e: Exception object we are handling
    """
    info = json.loads(e.api_exceptions[0].body)
    if info.get('reason').lower() == 'alreadyexists':
        pass
    else:
        raise e