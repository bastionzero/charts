# Built in modules
import logging

# 3rd party modules
import click

# Local modules
import bctl_quickstart.utils as utils

# Set our logging level
logging.getLogger().setLevel(logging.INFO)

@click.group(invoke_without_command=True)
@click.option('-apiKey', 'apiKey', envvar='API_KEY', required=True, type=str, help='BastionZero API key to use to make HTTPS requests')
@click.option('-clusterName', 'clusterName', envvar='CLUSTER_NAME', required=True, type=str, help='Cluster/Agent name to use when registering')
@click.option('-users', 'users', required=False, type=str, multiple=True, help='IDP users to add to the policy')
@click.option('-targetUsers', 'targetUsers', required=False, type=str, multiple=True, help='Target users to add to the policy')
@click.option('-targetGroups', 'targetGroups', required=False, type=str, multiple=True, help='Target groups to add to the policy')
def cli(apiKey, clusterName, users, targetUsers, targetGroups):
    """
    Our main function to parse our args and perform our quickstart
    """
    logging.info('Starting quickstart....')

    # Once it's online, check with Bastion that its come online
    utils.checkAgentOnlineBastion(apiKey, clusterName)

    # Now add any users, targetUsers, targetGroups to the policy that was created
    if users:
        utils.addSubjectsToPolicy(users, clusterName, apiKey)

    if targetUsers:
        utils.addTargetUsersToPolicy(targetUsers, clusterName, apiKey)

    if targetGroups:
        utils.addTargetGroupsToPolicy(targetGroups, clusterName, apiKey)

    logging.info(f'Finished setting up agent: {clusterName}!')

    logging.info('Finishing running kubernetes agent quickstart!')