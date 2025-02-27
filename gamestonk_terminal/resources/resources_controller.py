"""Resource Collection Controller Module"""
__docformat__ = "numpy"

import webbrowser
from typing import List

from prompt_toolkit.completion import NestedCompleter
from gamestonk_terminal.rich_config import console
from gamestonk_terminal import feature_flags as gtff
from gamestonk_terminal.parent_classes import BaseController
from gamestonk_terminal.menu import session


class ResourceCollectionController(BaseController):
    """Resources Controller class"""

    CHOICES_COMMANDS = [
        "hfletters",
        "arxiv",
        "finra",
        "edgar",
        "fred",
        "learn",
        "econiverse",
    ]

    def __init__(self, queue: List[str] = None):
        """Constructor"""
        super().__init__("/resources/", queue)

        if session and gtff.USE_PROMPT_TOOLKIT:
            choices: dict = {c: {} for c in self.controller_choices}
            self.completer = NestedCompleter.from_nested_dict(choices)

    def print_help(self):
        """Print help"""
        help_text = """
[info]Resource Collection:[/info][cmds]
   hfletters     hedge fund letters or reports
   arxiv         open-access archive for academic articles
   finra         self-regulatory organization
   edgar         online public database from SEC
   fred          economic research data
   learn         trading analysis, tips and resources
   econiverse    compilation of free knowledge and educational resources[/cmds]
        """
        console.print(text=help_text, menu="Resources")

    def call_hfletters(self, _):
        """Process hfletters command"""
        webbrowser.open("https://miltonfmr.com/hedge-fund-letters/")
        console.print("")

    def call_arxiv(self, _):
        """Process arxiv command"""
        webbrowser.open("https://arxiv.org")
        console.print("")

    def call_finra(self, _):
        """Process finra command"""
        webbrowser.open("https://www.finra.org/#/")
        console.print("")

    def call_edgar(self, _):
        """Process edgar command"""
        webbrowser.open("https://www.sec.gov/edgar.shtml")
        console.print("")

    def call_fred(self, _):
        """Process fred command"""
        webbrowser.open("https://fred.stlouisfed.org")
        console.print("")

    def call_learn(self, _):
        """Process learn command"""
        webbrowser.open("https://moongangcapital.com/free-stock-market-resources/")
        console.print("")

    def call_econiverse(self, _):
        """Process econiverse command"""
        webbrowser.open("https://econiverse.github.io")
        console.print("")
