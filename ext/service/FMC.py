import json
from urllib import response

import requests
import urllib3
from rich import print as rprint

urllib3.disable_warnings()
from ext.service.connection import refresh_token, validade_token


class FMC:
    def __init__(
        self, ipaddr, username, password, domain="", authtoken="", refreshtoken=""
    ):
        self.__ipaddr = ipaddr
        self.__username = username
        self.__password = password
        self.__domain = domain
        self.__authtoken = authtoken
        self.__refreshtoken = refreshtoken

    @property
    def ipaddr(self):
        return self.__ipaddr

    @property
    def username(self):
        return self.__username

    @property
    def password(self):
        return self.__password

    @property
    def domain(self):
        return self.__domain

    @domain.setter
    def domain(self, value):
        self.__domain = value

    @property
    def authtoken(self):
        return self.__authtoken

    @authtoken.setter
    def authtoken(self, value):
        self.__authtoken = value

    @property
    def refreshtoken(self):
        return self.__refreshtoken

    @refreshtoken.setter
    def refreshtoken(self, value):
        self.__refreshtoken = value

    #################################################################################################
    # GET
    #################################################################################################

    def get_information(self, path, retorno_json_chave):
        """
        This is a generic GET method to send a GET to FMC and handle the return. This is called by others GET methods.
        :param path: API Path
        :param retorno_json_chave: Array of values to serve as Key in our JSON return
        :return: JSON return with the entity and ID
        """

        # If retorno_json_chave is all, we will return a LIST of all elements in JSON format. It will be a list of dicts.
        # Otherwise, we will return only a dict of the element information and ID
        if retorno_json_chave[0] == "all":
            response_data = []
        else:
            response_data = {}
        headers = {
            "Content-Type": "application/json",
            "X-auth-access-token": self.authtoken,
            "X-auth-refresh-token": self.refreshtoken,
        }
        api_path = f"/api/fmc_config/v1/domain/{self.domain}/{path}"
        url = "https://" + self.ipaddr + api_path

        try:
            # Send GET to FMC. FMC paginates the return in 1000 occurrences
            r = requests.get(url, headers=headers, verify=False)
            json_resp = json.loads(r.text)
            # Check the response to see if the token was valid
            is_token_valid = validade_token(json_resp)
            if not is_token_valid:
                # If it was not valid, refresh it and run again (recursive call)
                self.authtoken, self.refreshtoken = refresh_token(
                    self.authtoken, self.refreshtoken
                )
                response_data.update(self.get_information(path, retorno_json_chave))
                return response_data

            # For each element in the return of the GET...
            try:
                for element in json_resp["items"]:
                    # Build the JSON to be returned, using the retorno_json_chave as Key
                    # If the key is "all", return the full JSON and append this to a list
                    if retorno_json_chave[0] == "all":
                        response_data.append(element)
                    # If the array has only one key, it is used. Some GETs uses "name", others use "values"
                    elif len(retorno_json_chave) == 1:
                        response_data.update(
                            {element[retorno_json_chave[0]]: element["id"]}
                        )
                    # Is some special cases such as Ports, we return as <PORTNUMBER>/<PROTOCOL>, ex: 443/TCP.
                    elif retorno_json_chave[0] == "port":
                        try:
                            response_data.update(
                                {
                                    f"{element['port']}/{element['protocol']}": element[
                                        "id"
                                    ]
                                }
                            )
                        except KeyError:
                            pass
                    # Cases such as routes, we return the host and gateway
                    elif retorno_json_chave[0] == "selectedNetworks":
                        try:
                            response_data.update(
                                {
                                    f"{element['interfaceName']}: {element['selectedNetworks'][0]['name']} --> {element['gateway']['literal']['value']}": element[
                                        "id"
                                    ]
                                }
                            )
                        except:
                            pass
            except:
                pass
                # response_data.update({retorno_json_chave[0]: "Not Found"})

            # Pagination check
            # If there are more than 1000 occurrences, FMC returns the next pages URL. So we need to place a new
            # GET to each of those.
            if (json_resp["paging"]["pages"]) > 1:
                try:
                    # Recursive call for each next page
                    for page in json_resp["paging"]["next"]:
                        # Set next_path variable so we can call the same function recursively.
                        next_path = page.replace(
                            f"https://{self.ipaddr}/api/fmc_config/v1/domain/{self.domain}/",
                            "",
                        )
                        next_page_data = self.get_information(
                            next_path, retorno_json_chave
                        )
                        if retorno_json_chave[0] == "all":
                            for item in next_page_data:
                                response_data.append(item)
                        else:
                            response_data.update(next_page_data)

                except KeyError:
                    # End of next pages
                    pass

        except requests.exceptions.HTTPError as err:
            print("Error in connection --> " + str(err))
        finally:
            if r:
                r.close()
        return response_data

    #################################################################################################
    # ADD
    #################################################################################################
    def add_information(self, path, json_data, retorno_json_chave):
        """
        This is a generic ADD method to send a POST to FMC and handle the return. This is called by others ADD methods.
        :param url: POST URL
        :param headers: Authentication Headers
        :param json_data: JSON Data
        :param retorno_json_chave: Array of values to serve as Key in our JSON return
        :return: JSON return with the entity created and ID
        """
        response_data = {}
        headers = {
            "Content-Type": "application/json",
            "X-auth-access-token": self.authtoken,
            "X-auth-refresh-token": self.refreshtoken,
        }
        api_path = f"/api/fmc_config/v1/domain/{self.domain}/{path}"
        url = "https://" + self.ipaddr + api_path

        try:
            r = requests.post(
                url, data=json.dumps(json_data), headers=headers, verify=False
            )
            json_resp = json.loads(r.text)

            is_token_valid = validade_token(json_resp)
            if not is_token_valid:
                # If it was not valid, refresh it and run again (recursive call)
                self.authtoken, self.refreshtoken = refresh_token(
                    self.authtoken, self.refreshtoken
                )
                response_data = {}
                # response_data.update(self.add_information(path, json_data, retorno_json_chave))
                # return (response_data)

            # If success, we will return the object created and the ID
            if r.status_code == 200 or r.status_code == 201 or r.status_code == 202:
                # If the return needs only one parameter (which is usually the case), we use this parameter
                # to search in the return JSON and build our return of this method
                if len(retorno_json_chave) == 1:
                    response_data.update(
                        {json_data[retorno_json_chave[0]]: json_resp["id"]}
                    )
                # In cases such as Ports, we use the port and protocol in the return JSON
                elif retorno_json_chave[0] == "port":
                    response_data.update(
                        {
                            f"{json_resp['port']}/{json_resp['protocol']}": json_resp[
                                "id"
                            ]
                        }
                    )
            # If not, we will return the error message
            else:
                response_data.update({json_data[retorno_json_chave[0]]: r.text})
        except requests.exceptions.HTTPError as err:
            print("Error in connection --> " + str(err))
        finally:
            if r:
                r.close()
        return response_data

    #################################################################################################
    # DELETE
    #################################################################################################
    def delete_information(self, id, path):
        """
        This is a generic DELETE method to send a DELETE to FMC and handle the return. This is called by others DELETE methods.
        :param id: ID of the entity to be deleted
        :param url: POST URL
        :param headers: Authentication Headers
        """
        response_data = {}
        headers = {
            "Content-Type": "application/json",
            "X-auth-access-token": self.authtoken,
            "X-auth-refresh-token": self.refreshtoken,
        }
        api_path = f"/api/fmc_config/v1/domain/{self.domain}/{path}"
        url = "https://" + self.ipaddr + api_path

        try:
            r = requests.delete(url, headers=headers, verify=False)
            json_resp = json.loads(r.text)

            is_token_valid = validade_token(json_resp)
            if not is_token_valid:
                # If it was not valid, refresh it and run again (recursive call)
                self.authtoken, self.refreshtoken = refresh_token(
                    self.authtoken, self.refreshtoken
                )
                response_data.update(self.delete_information(path, id, path))
                return response_data

            # If success, we will return the object created and the ID
            if r.status_code == 200 or r.status_code == 201 or r.status_code == 202:
                rprint(f"[green]Element ID {id} deleted![/green]")
            else:
                rprint(f"[red]Error deleting Element ID {id}![/red]")
        except requests.exceptions.HTTPError as err:
            print("Error in connection --> " + str(err))
        finally:
            if r:
                r.close()

        return response_data
