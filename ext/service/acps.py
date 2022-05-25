import csv
import json
import re

import requests
from ext.service.fqdns import get_fqdn
from ext.service.hosts import get_hosts
from ext.service.networks import (get_host_network_id, get_network_groups,
                                  get_networks)
from ext.service.ports import add_ports, get_port_groups, get_ports
from ext.service.security_zones import get_security_zones
from rich import print as rprint


#################################################################################################
# ACP
#################################################################################################
def get_acp_policies(fmc):
    """
    This method gets the ACP Policies created in this FMC
    :return: response_data: List of policies and ID of every ACP Policy in FMC
    """
    path = "policy/accesspolicies?expanded=false&offset=0&limit=1000"
    retorno_json_chave = ["name"]
    response_data = fmc.get_information(path, retorno_json_chave)
    return response_data



def get_category(fmc, policy_id):
    path = f"policy/accesspolicies/{policy_id}/categories?expanded=false&offset=0&limit=1000"
    retorno_json_chave = ["name"]
    response_data = fmc.get_information(path, retorno_json_chave)
    return response_data


def add_category(fmc, acp_category, acp_policy_id):
    path = f"policy/accesspolicies/{acp_policy_id}/categories"
    retorno_json_chave = ["name"]
    response_data = fmc.add_information(path, acp_category, retorno_json_chave)
    return response_data


def add_acp_policy(fmc, post_data):
    path = f"policy/accesspolicies"
    retorno_json_chave = ["name"]
    response_data = fmc.add_information(path, post_data, retorno_json_chave)
    return response_data


def handle_network_list(fmc, networks, type, network_list, host_list, fqdn_list):
    """
    This method is used by the add_acp method, and receives a list of network inputs from the CSV file, and generate
    the JSON structure for networks to be added in the ACP Rule
    :param networks: Network list from the CSV file. Each occurrence can be a Network, Host, FQDN or Group
    :param type: source or destination
    :param network_list: network list from FMC
    :param host_list: host list from FMC
    :param fqdn_list: FQDN list frm FMC
    :return: JSON structure to be added in the POST to FMC when adding ACP
    """
    if type == "source":
        json_key = "sourceNetworks"
    elif type == "destination":
        json_key = "destinationNetworks"
    response_network_data = {json_key: {"objects": []}}
    if networks[0] != "":
        for network in networks:
            # Check if the address has an IP format
            isAddress = bool(re.match("^\d+.\d+.\d+.\d+", network))
            # Check if the address is FQDN
            isFQDN = bool(re.match(".*\..*", network))

            # Network is a Network or Host
            if isAddress or isFQDN:
                network_id, network_type = get_host_network_id(
                    fmc, network, network_list, host_list, fqdn_list
                )
                network_data = {"type": network_type, "id": network_id}
                response_network_data[json_key]["objects"].append(network_data)
            # Network is a Group
            else:
                try:
                    group_list = get_network_groups(fmc)
                    network_data = {
                        "type": "NetworkGroup",
                        "id": group_list[network],
                    }
                    response_network_data[json_key]["objects"].append(network_data)
                except KeyError:
                    rprint(
                        "[red]Network group does not exist! Please create this network group and modify this rule manually![/red]"
                    )
    return response_network_data


def handle_port_list(fmc, ports, type, port_list):
    """
    This method is used by the add_acp method, and receives a list of ports inputs from the CSV file, and generate
    the JSON structure for ports to be added in the ACP Rule
    :return: JSON structure to be added in the POST to FMC when adding ACP
    """
    if type == "source":
        json_key = "sourcePorts"
    elif type == "destination":
        json_key = "destinationPorts"
    response_port_data = {json_key: {"objects": []}}

    if ports[0] != "":
        for port in ports:
            # If the port has a "/", it is in Port/Protocol format
            if "/" in port:
                try:
                    port_id = port_list[port]
                except KeyError:
                    status_port = add_ports(fmc, port.split("/")[0], port.split("/")[1])
                    rprint(
                        f"[italic]Port {port} does not exist and will be created[/italic]"
                    )
                    port_id = status_port[port]
                port_data = {"type": "ProtocolPortObject", "id": port_id}
                response_port_data[json_key]["objects"].append(port_data)
            # Otherwise, it is a port group
            else:
                port_group_list = get_port_groups(fmc)
                try:
                    port_group_data = {
                        "type": "PortObjectGroup",
                        "id": port_group_list[port],
                    }
                    response_port_data[json_key]["objects"].append(port_group_data)
                except KeyError:
                    rprint(
                        "[red]Port group does not exist! Please create this port group and modify this rule manually![/red]"
                    )
    return response_port_data


def add_acp(fmc, csv_input):
    """
    This method adds ACPs listed in a CSV File
    :param csv_input: CSV File
    :return: response_data: Array with the Policies and IDs
    """
    rprint("[italic]Colecting Security Zones List . . . [/italic]")
    sec_zones_list = get_security_zones(fmc)  # Security Zones
    rprint("[italic]Colecting ACPs List . . . [/italic]")
    acp_policies_list = get_acp_policies(fmc)  # ACP Policies

    response_data = {}
    with open(csv_input, "r") as input_file:
        input_csv = csv.reader(input_file, delimiter=",")
        for acp in input_csv:
            # Skip header line and comments
            if acp[0].startswith("#"):
                continue
            rprint(f"[italic]Adding rule {acp[1]} . . .[/italic]")
            network_list = get_networks(fmc)  # Networks Objects
            host_list = get_hosts(fmc)  # Host Objects
            fqdn_list = get_fqdn(fmc)  # FQDN Objects
            port_list = get_ports(fmc)  # Ports Objects

            # Check if the Policy exists.
            try:
                acp_policy_id = acp_policies_list[acp[0]]
            # If it doesn't exist, create it!
            except:
                acp_policy = {
                    "type": "AccessPolicy",
                    "name": acp[0],
                    "defaultAction": {"action": "BLOCK"},
                }
                acp_policy_created = add_acp_policy(fmc, acp_policy)
                acp_policy_id = acp_policy_created[acp[0]]
                acp_policies_list = get_acp_policies(fmc)  # Update ACP Policies

            # Check if Category exists.
            try:
                acp_categories = get_category(fmc, acp_policy_id)
            except:
                acp_categories = {}
            try:
                category_id = acp_categories[acp[2]]
            except:
                category_data = {"type": "Category", "name": acp[2]}
                add_category(fmc, category_data, acp_policy_id)
            finally:
                acp_category = acp[2]

            acp_rule_name = acp[1]
            acp_action = acp[3]
            source_interface = acp[4]
            destination_interface = acp[5]
            # Getting the list of networks and hosts. If there are more than one, they are splited with a ; in the
            # CSV file
            try:
                source_network = acp[6].split(";")
            except:
                source_network = [acp[6]]
            try:
                destination_network = acp[7].split(";")
            except:
                destination_network = [acp[7]]

            # Getting the list of ports. If there are more than one, they are splited with a ; in the CSV file
            try:
                source_ports = acp[8].split(";")
            except:
                source_ports = [acp[8]]
            try:
                destination_ports = acp[9].split(";")
            except:
                destination_ports = [acp[9]]

            # Building the list of Source Networks in JSON Format.
            data_source = handle_network_list(
                fmc, source_network, "source", network_list, host_list, fqdn_list
            )
            # Building the íist of Destination Networks in JSON Format.
            data_destination = handle_network_list(
                fmc,
                destination_network,
                "destination",
                network_list,
                host_list,
                fqdn_list,
            )
            # Handling cases where source and destination are the same
            if "already exists" in json.dumps(data_destination):
                data_destination = data_source

            # Building the list of Source Ports
            data_port_source = handle_port_list(fmc, source_ports, "source", port_list)
            # Building the list of Destination Ports
            data_port_destination = handle_port_list(
                fmc, destination_ports, "destination", port_list
            )

            # Getting the Security Zones IDs. If it doesn't exist, abort!
            if source_interface != "":
                try:
                    source_interface_id = sec_zones_list[source_interface]
                    source_zone_list = {
                        "sourceZones": {
                            "objects": [
                                {"id": source_interface_id, "type": "SecurityZone"}
                            ]
                        }
                    }
                except KeyError:
                    rprint(
                        f"[red]Security Zone {source_interface} does not exist. Aborting![/red]"
                    )
                    source_interface_id = ""

            if destination_interface != "":
                try:
                    destination_interface_id = sec_zones_list[destination_interface]
                    destination_zone_list = {
                        "destinationZones": {
                            "objects": [
                                {
                                    "id": destination_interface_id,
                                    "type": "SecurityZone",
                                }
                            ]
                        }
                    }
                except KeyError:
                    rprint(
                        f"[red]Security Zone {destination_interface} does not exist. Aborting![/red]"
                    )
                    destination_interface_id = ""

            # Creating the JSON
            post_data = {
                "action": acp_action.upper(),
                "enabled": True,
                "type": "AccessRule",
                "name": acp_rule_name,
                "sendEventsToFMC": True,
                "logFiles": False,
                "logBegin": True,
                "logEnd": False,
            }
            # Appending the Source Zone JSON if a source zone was specified on the CSV
            if source_interface != "":
                post_data.update(source_zone_list)
            # Appending the Destination Zone JSON if a destination zone was specified on the CSV
            if destination_interface != "":
                post_data.update(destination_zone_list)
            # Appending the Source Ports JSON if ports were specified on the CSV
            if source_ports[0] != "":
                post_data.update(data_port_source)
            # Appending the Destination Ports JSON if ports were specified on the CSV
            if destination_ports[0] != "":
                post_data.update(data_port_destination)
            # Appending the Source Networks JSON if source networks were specified on the CSV
            if source_network[0] != "":
                post_data.update(data_source)
            # Appending the Destination Networks JSON if destination networks were specified on the CSV
            if destination_network[0] != "":
                post_data.update(data_destination)

            api_path = f"/api/fmc_config/v1/domain/{fmc.domain}/policy/accesspolicies/{acp_policy_id}/accessrules?bulk=false&category={acp_category}"
            url = "https://" + fmc.ipaddr + api_path
            headers = {
                "Content-Type": "application/json",
                "X-auth-access-token": fmc.authtoken,
                "X-auth-refresh-token": fmc.refreshtoken,
            }
            try:
                r = requests.post(
                    url, data=json.dumps(post_data), headers=headers, verify=False
                )
                if r.status_code == 201 or r.status_code == 202:
                    json_resp = json.loads(r.text)
                    response_data.update({json_resp["name"]: json_resp["id"]})
                else:
                    rprint(
                        f"[white]Error occurred in POST --> {json.dumps(r.text, sort_keys=True, indent=4, separators=(',', ': '))}[/white]".replace(
                            "error", "[red]error[/red]]"
                        )
                    )
            except requests.exceptions.HTTPError as err:
                print("Error in connection --> " + str(err))
            finally:
                if r:
                    r.close()

    return response_data


