#################################################################################################
# HOSTS
#################################################################################################
def get_hosts(fmc):
    """
    This method returns a JSON with all Hosts created in a FMC
    :return: response_data: List of Name and ID of every host in FMC
    """
    path = "object/hosts?expanded=true&offset=0&limit=1000"
    retorno_json_chave = ["value"]
    response_data = fmc.get_information(path, retorno_json_chave)
    return response_data
