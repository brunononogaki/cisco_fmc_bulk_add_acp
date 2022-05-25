import csv
import json
import re

import requests
from ext.service.hosts import get_hosts
from ext.service.objects import add_network_object
from rich import print as rprint


#################################################################################################
# NETWORKS
#################################################################################################
def get_networks(fmc):
    """
    This method returns a JSON with all Hosts created in a FMC
    :return: response_data: List of Name and ID of every host in FMC
    """
    path = "object/networks?expanded=true&offset=0&limit=1000"
    retorno_json_chave = ["value"]
    response_data = fmc.get_information(path, retorno_json_chave)
    return response_data


def get_host_network_id(fmc, address, network_list, host_list, fqdn_list):
    """
    This method returns a JSON with all Hosts, networks and FQDNs objects created in a FMC
    :return: response_data: List of Name and ID of every host, network of fqdn in FMC
    """
    isAddress = bool(
        re.match("^\d+.\d+.\d+.\d+", address)
    )  # Check if address has an IP Address format
    isFQDN = bool(
        re.match(".*\..*", address)
    )  # Check if address has a . (dot), indicating that it is FQDN

    # If the address has an IP Address format, it is a host or network
    if isAddress:
        if "/" in address:
            address_type = "Network"
            try:
                id = network_list[address]
            except KeyError:
                rprint(
                    f"[italic]Network {address} does not exist and will be created![/italic]"
                )
                # If the network does not exist, let's create it!
                network_json_data = {
                    "name": address.replace("/", "_"),
                    "description": address,
                    "type": "Network",
                    "value": address,
                }
                status_network = add_network_object(fmc, "Network", network_json_data)
                if "error" in json.dumps(status_network):
                    rprint(
                        f"[white]{json.dumps(status_network).replace('error','[red]error[/red]')}[/white]"
                    )
                id = status_network[address]
        else:
            address_type = "Host"
            try:
                id = host_list[address]
            except KeyError:
                rprint(
                    f"[italic]Host {address} does not exist and will be created![/italic]"
                )
                # If the network does not exist, let's create it!
                network_json_data = {
                    "name": address.replace("/", "_"),
                    "description": address,
                    "type": "Host",
                    "value": address,
                }
                status_network = add_network_object(fmc, "Host", network_json_data)
                id = status_network[address]
    # Otherwise, if the address has a dot in its name, it is a FQDN
    elif isFQDN:
        address_type = "FQDN"
        try:
            id = fqdn_list[address]
        except KeyError:
            rprint(
                f"[italic]FQDN {address} does not exist and will be created![/italic]"
            )
            # If the FQDN does not exist, let's create it!
            network_json_data = {
                "name": address,
                "description": address,
                "type": "FQDN",
                "value": address,
            }
            status_network = add_network_object(fmc, "FQDN", network_json_data)
            id = status_network[address]
    # Otherwise, it is a group
    else:
        address_type = "NetworkGroup"
        group_list = get_network_groups(fmc)
        id = group_list[address]

    return id, address_type


#################################################################################################
# GROUPS
#################################################################################################
def get_network_groups(fmc):
    """
    This method returns a JSON with all Network Groups created in a FMC
    :return: response_data: Group name and ID of every host in FMC
    """
    path = "object/networkgroups?expanded=false&offset=0&limit=1000"
    retorno_json_chave = ["name"]
    response_data = fmc.get_information(path, retorno_json_chave)
    return response_data


def add_network_groups(fmc, group_name, address_list):
    """
    This method adds a single Network Group
    :return: response_data: Group name and ID of every host in FMC
    """
    host_list = get_hosts(fmc)
    network_list = get_networks(fmc)

    json_objects = []
    for address in address_list:
        # If the host/network does not exist, create it!
        if not (address in host_list or address in network_list):
            # If the address is a Network
            if "/" in address:
                rprint(f"[italic][white]Creating network {address}[/italic][/white]")
                address_type = "Network"
                network_json_data = {
                    "name": address.replace("/", "_"),
                    "description": address,
                    "type": "Network",
                    "value": address,
                }
                status_network = add_network_object("Network", network_json_data)
                id = status_network[address]
                network_list.update({address: id})
            # If the address is a Host
            else:
                address_type = "Host"
                rprint(f"[italic][white]Creating host {address}[/italic][/white]")
                # If the network does not exist, let's create it!
                network_json_data = {
                    "name": address.replace("/", "_"),
                    "description": address,
                    "type": "Host",
                    "value": address,
                }
                status_network = add_network_object("Host", network_json_data)
                id = status_network[address]
                host_list.update({address: id})
        else:
            if "/" in address:
                address_type = "Network"
                id = network_list[address]
            else:
                address_type = "Host"
                id = host_list[address]
        json_objects.append({"type": address_type, "id": id})
    json_data = {"name": group_name, "objects": json_objects}

    path = f"object/networkgroups?bulk=false"
    retorno_json_chave = ["name"]
    response_data = fmc.add_information(path, json_data, retorno_json_chave)
    return response_data


def add_network_groups_csv(fmc, csv_input):
    """
    This method reads a CSV file with Network Groups and add them one by one
    :return: response_data: Group name and ID of every host in FMC
    """
    response_data = {}

    with open(csv_input, "r") as input_file:
        input_csv = csv.reader(input_file, delimiter=",")
        for group in input_csv:
            # Skip header line and comments
            if group[0].startswith("#"):
                continue
            group_name = group[0]
            address_list = group[1].split(";")
            response_data.update(add_network_groups(fmc, group_name, address_list))
    return response_data


def get_network_group_detail(fmc, group_id):
    """
    This method returns a list of objects in a network group
    :return: response_data: List of Name and ID of every host in FMC
    """
    path = f"object/networkgroups/{group_id}"
    response_data = []
    headers = {
        "Content-Type": "application/json",
        "X-auth-access-token": fmc.authtoken,
        "X-auth-refresh-token": fmc.refreshtoken,
    }
    api_path = f"/api/fmc_config/v1/domain/{fmc.domain}/{path}"
    url = "https://" + fmc.ipaddr + api_path

    r = requests.get(url, headers=headers, verify=False)
    json_resp = json.loads(r.text)
    # For each element in the return of the GET...
    try:
        for element in json_resp["objects"]:
            response_data.append(element)
    except:
        for element in json_resp["literals"]:
            response_data.append(element)
    return response_data
