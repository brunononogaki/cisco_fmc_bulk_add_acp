import sys
from datetime import datetime
from getpass import getpass

from rich import print as rprint
from rich.console import Console


from ext.service.domains import get_domains
from ext.service.FMC import *
from ext.service.acps import add_acp

console = Console()
DATE_TIME = "%D - %H:%M:%S: "

# Reading the config file
try:
    with open("ext/config/fmc_info.json", "r") as fmc_info:
        fmc_info_json = json.load(fmc_info)
    fmc_ip = fmc_info_json["fmc_ip"]
    fmc_user = fmc_info_json["fmc_user"]
    fmc_passwd = fmc_info_json["fmc_passwd"]
except:
    rprint("[red]fmc_info.json file not found![/red]")
    fmc_ip = input("FMC IP Address: ")
    fmc_user = input("FMC Username: ")
    fmc_passwd = getpass("FMC Password: ")
    fmc_info_json = {"fmc_ip": fmc_ip, "fmc_user": fmc_user, "fmc_passwd": fmc_passwd}
    with open("ext/config/fmc_info.json", "w") as fmc_info:
        fmc_info.write(json.dumps(fmc_info_json))


def bulk_add_acps(fmc):
    console = Console()
    DATE_TIME = "%D - %H:%M:%S: "
    console.input("[yellow]Please make sure you have a [bold]acp.csv[/bold] file in the Root directory. Press <ENTER> to continue...[/yellow]")
    file = "acp.csv"
    rprint(f"[yellow]{datetime.now().strftime(DATE_TIME)} Starting...[/yellow]")
    rprint("[italic]Adding Access Policies . . .[/italic]")
    status = add_acp(fmc, file)
    rprint("\n[green]Operation completed. Check the results below:[/green]")
    print(json.dumps(status, sort_keys=True, indent=4, separators=(",", ": ")))


# Instantiating FMC object
fmc = FMC(fmc_ip, fmc_user, fmc_passwd)
fmc = get_domains(fmc)
bulk_add_acps(fmc)
