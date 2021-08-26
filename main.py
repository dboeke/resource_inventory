import os
import csv
import sys
import yaml
import click
import requests
from base64 import b64encode
from xdg import XDG_CONFIG_HOME

@click.command()
@click.option('-p', '--profile', default="default", help="[String] Profile to be used from config file.")

def main(profile):
    config = load_turbot_config(profile)

    aws_instances = get_aws_ec2_instances(config)
    if aws_instances:
        save_as_csv("aws_ec2_instances.csv", aws_instances)

    aws_ec2_volumes = get_aws_ec2_volumes(config)
    if aws_ec2_volumes:
        save_as_csv("aws_ec2_volumes.csv", aws_ec2_volumes)

    azure_compute_vms = get_azure_compute_virtual_machines(config)
    if azure_compute_vms:
        for azure_compute_vm in azure_compute_vms:
            # Get the latest VM status as the state
            statuses = azure_compute_vm["Statuses"]
            azure_compute_vm["State"] = statuses[-1].get("displayStatus","")
            del azure_compute_vm["Statuses"]

            # Get private IP and virtual network
            network_interface_id = azure_compute_vm["NetworkInterfaceId"]
            network_interface = get_azure_compute_virtual_machine_network_interface(f"azure://{network_interface_id}", config)

            azure_compute_vm["PrivateIp"] = network_interface.get("privateIPAddress","") if network_interface else ""
            subnetId = network_interface.get("subnetId","") if network_interface else ""
            azure_compute_vm["VirtualNetwork"] = subnetId.split("/")[-3] if subnetId else ""
            del azure_compute_vm["NetworkInterfaceId"]

        save_as_csv("azure_compute_vms.csv", azure_compute_vms)

def save_as_csv(csv_file_name, content):
    if not content:
        return

    os.makedirs(os.path.dirname(f"output/{csv_file_name}"), exist_ok=True)
    with open(f"output/{csv_file_name}", 'w') as csvfile:
        writer = csv.DictWriter(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, fieldnames=content[0].keys())
        writer.writeheader()
        for element in content:
            writer.writerow(element)


def run_query(query, variables, config):

    request = requests.post(
        workspace_graphql_ep(config['workspace']),
        headers={'Authorization': 'Basic {}'.format(basic_auth_token(config['accessKey'], config['secretKey']))},
        json={'query': query, 'variables': variables}
    )

    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(
        request.status_code, query))


def run_resources_query_with_pagination(query, variables, config):
    items = []
    next_page = ""
    while True:
        variables["paging"] = next_page
        query_result = run_query(query, variables, config)
        items = items + query_result["data"]["resources"]["items"]
        next_page = query_result["data"]["resources"]["paging"]["next"]
        if not next_page:
            break
    return items


def get_aws_ec2_instances(config):
    query = """
        query Instances($filter: [String!], $paging: String!) {
            resources(filter: $filter, paging: $paging) {
                items {
                    AWSAccount: get(path: "turbot.custom.aws.accountId")
                    ProjectShortTag: get(path: "turbot.tags.ProjectShort")
                    Platform: get(path: "Image.PlatformDetails")
                    AWSRegion: get(path: "turbot.custom.aws.regionName")
                    VPC: get(path: "VpcId")
                    InstanceId: get(path: "InstanceId")
                    PrivateIp: get(path: "PrivateIpAddress")
                    State: get(path: "State.Name")
                    Tags: tags
                    TurbotId: get(path: "turbot.id")
                    }
                paging {
                    next
                }
                metadata {
                    stats {
                        total
                    }
                }
            }
        }
    """

    variables = {
        "filter": "resourceTypeId:'tmod:@turbot/aws-ec2#/resource/types/instance'"
    }

    items = run_resources_query_with_pagination(query, variables, config)
    print(f"{len(items)} AWS EC2 instances found")
    return items


def get_aws_ec2_volumes(config):
    query = """
        query Volumes($filter: [String!], $paging: String!) {
            resources(filter: $filter, paging: $paging) {
                items {
                    AWSAccount: get(path: "turbot.custom.aws.accountId")
                    ProjectShortTag: get(path: "turbot.tags.ProjectShort")
                    AWSRegion: get(path: "turbot.custom.aws.regionName")
                    VolumeId: get(path: "VolumeId")
                    VolumeType: get(path: "VolumeType")
                    State: get(path: "State")
                    Size: get(path: "Size")
                    InstanceId: get(path: "Attachments[0].InstanceId")
                    Tags: tags
                    TurbotId: get(path: "turbot.id")
                }
                paging {
                    next
                }
                metadata {
                    stats {
                        total
                    }
                }
            }
        }
    """

    variables = {
        "filter": "resourceTypeId:'tmod:@turbot/aws-ec2#/resource/types/volume'"
    }

    items = run_resources_query_with_pagination(query, variables, config)
    print(f"{len(items)} AWS EC2 volumes found")
    return items


def get_azure_compute_virtual_machines(config):
    query = """
        query VirtualMachines($filter: [String!], $paging: String!) {
            resources(filter: $filter, paging: $paging) {
                items {
                    AzureSubscription: get(path: "turbot.custom.azure.subscriptionId")
                    ProjectShortTag: get(path: "turbot.tags.ProjectShort")
                    Platform: get(path: "storageProfile.osDisk.osType")
                    AzureRegion: get(path: "turbot.custom.azure.regionName")
                    VirtualMachineId: get(path: "name")
                    Tags: tags
                    TurbotId: get(path: "turbot.id")
                    Statuses: get(path: "statuses")
                    NetworkInterfaceId: get(path: "networkProfile.networkInterfaces[0].id")
                    }
                paging {
                    next
                }
                metadata {
                    stats {
                        total
                    }
                }
            }
        }
    """

    variables = {
        "filter": "resourceTypeId:'tmod:@turbot/azure-compute#/resource/types/virtualMachine'"
    }

    items = run_resources_query_with_pagination(query, variables, config)
    print(f"{len(items)} Azure compute VMs found")
    return items


def get_azure_compute_virtual_machine_network_interface(network_interface_id, config):
    query = """
        query VmNetworkInterface($id: ID!) {
            resource(id: $id) {
                subnetId: get(path: "ipConfigurations[0].subnet.id")
    	        privateIPAddress: get(path: "ipConfigurations[0].privateIPAddress")
            }
        }
    """

    variables = {
        "id": network_interface_id
    }

    query_result = run_query(query, variables, config)
    resource = query_result["data"]["resource"]
    return resource

def load_turbot_config(config_profile):
    config_loc = "{}/turbot/credentials.yml".format(XDG_CONFIG_HOME)
    if os.path.exists(config_loc):
        with open(config_loc, 'r') as stream:
            try:
                config_dict = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    else:
        print("Error: {} configuration file not found [{}].",format(type, config_loc))
        exit()
    if not config_profile in config_dict:
        print("Error: No matching profile.")
        exit()
    return config_dict[config_profile]

def workspace_graphql_ep(base_url):
    return get_endpoint(base_url, "api/latest/graphql")

def workspace_health_ep(base_url):
    return get_endpoint(base_url, "api/latest/turbot/health")

def get_endpoint(base_url, path):
    sep = "{}/{}"
    if base_url.endswith("/"):
        sep = "{}{}"
    return sep.format(base_url, path)

def basic_auth_token(key, secret):
    auth_bytes = '{}:{}'.format(key, secret).encode("utf-8")
    return b64encode(auth_bytes).decode()

if __name__ == "__main__":
    if (sys.version_info > (3, 4)):
        try:
            main()
        except Exception as e:
            print(e)
    else:
        print("This script requires Python v3.5+")
        print("Your Python version is: {}.{}.{}".format(
            sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
        if (sys.version_info < (3, 0)):
            hint = ["Maybe try: `python3"] + sys.argv
            hint[len(sys.argv)] = hint[len(sys.argv)] + "`"
            print(*hint)
