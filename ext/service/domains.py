from ext.service.connection import make_connection
from rich import print as rprint
from rich.console import Console


def get_domains(fmc):
    console = Console()

    while True:
        rprint(
            "[italic]Please wait while we collect the list of domains . . .[/italic]"
        )
        auth_token, refresh_token, domain_list = make_connection(fmc)
        try:
            if len(domain_list) > 1:
                counter = 1
                for domain in domain_list:
                    print(
                        f"{counter}) {domain_list[counter-1]['name']} ({domain_list[counter-1]['uuid']}) "
                    )
                    counter += 1
                domain_selected = int(
                    console.input("[cyan][bold]Choose a domain: [/cyan][/bold]")
                )
                rprint(
                    f"[yellow]Configurations will be made on the domain [bold]{domain_list[domain_selected - 1]['name']}[/bold][/yellow]"
                )
                domain_uuid = domain_list[domain_selected - 1]["uuid"]
            else:
                rprint(
                    f"[yellow]Configurations will be made on the domain [bold]{domain_list[0]['name']}[/bold][/yellow]"
                )
                domain_uuid = domain_list[0]["uuid"]
        except ValueError:
            rprint("[red]Invalid entry![/red]")
            continue
        except IndexError:
            rprint("[red]Invalid entry![/red]")
            continue

        fmc.domain = domain_uuid
        fmc.authtoken = auth_token
        fmc.refreshtoken = refresh_token
        return fmc
