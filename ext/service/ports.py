#################################################################################################
# PORTS
#################################################################################################
def get_ports(fmc):
    """
    This method gets the ports objects created in this FMC
    :return: response_data: List of Ports and ID of every FTD Device in FMC
    """
    response_data = {}
    path = "object/protocolportobjects?expanded=true&offset=0&limit=1000"
    retorno_json_chave = ["port", "protocol"]
    response_data.update(fmc.get_information(path, retorno_json_chave))

    path = "object/icmpv4objects?expanded=true&offset=0&limit=1000"
    retorno_json_chave = ["name"]
    response_data.update(fmc.get_information(path, retorno_json_chave))

    return response_data


def get_port_groups(fmc):
    """
    This method gets the ports objects created in this FMC
    :return: response_data: List of Ports and ID of every FTD Device in FMC
    """
    response_data = {}
    path = "object/portobjectgroups?expanded=true&offset=0&limit=1000"
    retorno_json_chave = ["name"]
    response_data.update(fmc.get_information(path, retorno_json_chave))
    return response_data


def add_ports(fmc, port, protocol):
    """
    This method gets the ports objects created in this FMC
    :return: response_data: List of Ports and ID of every FTD Device in FMC
    """
    response_data = {}

    # Check if the port exists. If it does, return the port/protocol and ID
    port_list = get_ports(fmc)
    port_protocol = f"{port}/{protocol}"
    if port_protocol in port_list.keys():
        response_data = {port_protocol: port_list[port_protocol]}
        return response_data

    # If the port does not exist, let's create it!
    path = f"object/protocolportobjects?bulk=false"
    post_data = {
        "name": f"{port}_{protocol}",
        "protocol": protocol,
        "port": port,
        "type": "ProtocolPortObject",
    }
    retorno_json_chave = ["port", "protocol"]
    response_data = fmc.add_information(path, post_data, retorno_json_chave)

    return response_data
