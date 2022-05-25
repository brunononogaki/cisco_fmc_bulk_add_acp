#################################################################################################
# SECURITY ZONES
#################################################################################################
def get_security_zones(fmc):
    """
    This method returns a JSON with all Security Zones created in a FMC
    :return: response_data: List of Name and ID of every Security Zone in FMC
    """
    path = "object/securityzones?expanded=true&offset=0&limit=1000"
    retorno_json_chave = ["name"]
    response_data = fmc.get_information(path, retorno_json_chave)
    return response_data
