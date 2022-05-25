import csv


#################################################################################################
# OBJECTS
#################################################################################################
def add_network_object(fmc, object_type, json_data, domain_uuid=None):
    """
    This method adds one individual object (Host, Network or FQDN).
    :param object_type: Host, Network or FQDN
    :param domain_uuid: Domain UUID
    :param json_data: POST data
    :return: response_data: Status of the creation
    """

    # Setting up the URL based on the Object we are going to add
    if object_type == "Host":
        path = f"object/hosts?bulk=false"
    elif object_type == "Network":
        path = f"object/networks?bulk=false"
    elif object_type == "FQDN":
        path = f"object/fqdns?bulk=false"

    retorno_json_chave = ["value"]
    response_data = fmc.add_information(path, json_data, retorno_json_chave)
    return response_data


def add_network_objects_csv(fmc, csv_input):
    """
    This method adds hosts, networks and FQDNs listed in a CSV File
    :param csv_input: CSV File with Name,Description,Type,Value
    :return: response_data: Array with the IP Address and ID of the host/network/fqdn created
    """
    input_data = {}
    response_data = {}

    # Reading CSV file
    with open(csv_input, "r") as input_file:
        input_csv = csv.reader(input_file, delimiter=",")
        for object in input_csv:
            # Skip header line and comments
            if object[0].startswith("#"):
                continue
            # Check the type of the object (host, network or FQDN) and build a JSON with the object type as
            # key, and the array of elements as value.
            if object[2] in input_data.keys():
                input_data[object[2]].append(
                    {
                        "name": object[0],
                        "description": object[1],
                        "type": object[2],
                        "value": object[3],
                    }
                )
            else:
                input_data[object[2]] = [
                    {
                        "name": object[0],
                        "description": object[1],
                        "type": object[2],
                        "value": object[3],
                    }
                ]

    # For each type of object (host, network, fqdn), add the objects
    for object_type in input_data.keys():
        # For each type object, we will have an array of objects. Let's loop this array to
        # add each host individually. It is better than bulk to receive individual status for each object
        for object in input_data[object_type]:
            # Store the status in response_data dictionary
            response_data.update(
                add_network_object(fmc, object_type, object, fmc.domain)
            )

    return response_data
