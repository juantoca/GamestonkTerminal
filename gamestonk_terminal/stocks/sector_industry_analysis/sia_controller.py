"""Sector and Industry Analysis Controller Module"""
__docformat__ = "numpy"

import argparse
import difflib
from typing import List
import yfinance as yf
from prompt_toolkit.completion import NestedCompleter
from gamestonk_terminal.rich_config import console
from gamestonk_terminal.parent_classes import BaseController
from gamestonk_terminal.helper_funcs import (
    EXPORT_BOTH_RAW_DATA_AND_FIGURES,
    parse_known_args_and_warn,
    check_positive,
    check_proportion_range,
)
from gamestonk_terminal.stocks import stocks_helper
from gamestonk_terminal.menu import session
from gamestonk_terminal import feature_flags as gtff
from gamestonk_terminal.stocks.sector_industry_analysis import (
    financedatabase_model,
    financedatabase_view,
)
from gamestonk_terminal.stocks.comparison_analysis import ca_controller


# pylint: disable=inconsistent-return-statements,C0302,R0902


class SectorIndustryAnalysisController(BaseController):
    """Sector Industry Analysis Controller class"""

    CHOICES_COMMANDS = [
        "load",
        "clear",
        "industry",
        "sector",
        "country",
        "mktcap",
        "exchange",
        "cps",
        "cpic",
        "cpis",
        "cpcs",
        "cpci",
        "sama",
        "metric",
    ]
    CHOICES_MENUS = [
        "ca",
    ]

    metric_choices = [
        "roa",
        "roe",
        "cr",
        "qr",
        "de",
        "tc",
        "tcs",
        "tr",
        "rps",
        "rg",
        "eg",
        "pm",
        "gp",
        "gm",
        "ocf",
        "om",
        "fcf",
        "td",
        "ebitda",
        "ebitdam",
        "rec",
        "mc",
        "fte",
        "er",
        "bv",
        "ss",
        "pb",
        "beta",
        "fs",
        "peg",
        "ev",
        "fpe",
    ]
    metric_yf_keys = {
        "roa": ("financialData", "returnOnAssets"),
        "roe": ("financialData", "returnOnEquity"),
        "cr": ("financialData", "currentRatio"),
        "qr": ("financialData", "quickRatio"),
        "de": ("financialData", "debtToEquity"),
        "tc": ("financialData", "totalCash"),
        "tcs": ("financialData", "totalCashPerShare"),
        "tr": ("financialData", "totalRevenue"),
        "rps": ("financialData", "revenuePerShare"),
        "rg": ("financialData", "revenueGrowth"),
        "eg": ("financialData", "earningsGrowth"),
        "pm": ("financialData", "profitMargins"),
        "gp": ("financialData", "grossProfits"),
        "gm": ("financialData", "grossMargins"),
        "ocf": ("financialData", "operatingCashflow"),
        "om": ("financialData", "operatingMargins"),
        "fcf": ("financialData", "freeCashflow"),
        "td": ("financialData", "totalDebt"),
        "ebitda": ("financialData", "ebitda"),
        "ebitdam": ("financialData", "ebitdaMargins"),
        "rec": ("financialData", "recommendationMean"),
        "mc": ("price", "marketCap"),
        "fte": ("summaryProfile", "fullTimeEmployees"),
        "er": ("defaultKeyStatistics", "enterpriseToRevenue"),
        "bv": ("defaultKeyStatistics", "bookValue"),
        "ss": ("defaultKeyStatistics", "sharesShort"),
        "pb": ("defaultKeyStatistics", "priceToBook"),
        "beta": ("defaultKeyStatistics", "beta"),
        "fs": ("defaultKeyStatistics", "floatShares"),
        "sr": ("defaultKeyStatistics", "shortRatio"),
        "peg": ("defaultKeyStatistics", "pegRatio"),
        "ev": ("defaultKeyStatistics", "enterpriseValue"),
        "fpe": ("defaultKeyStatistics", "forwardPE"),
    }
    mktcap_choices = ["Small", "Mid", "Large", "small", "mid", "large"]
    clear_choices = ["industry", "sector", "country", "mktcap"]

    def __init__(
        self,
        ticker: str,
        queue: List[str] = None,
    ):
        """Constructor"""
        super().__init__("/stocks/sia/", queue)

        self.country = "United States"
        self.sector = "Financial Services"
        self.industry = "Financial Data & Stock Exchanges"
        self.mktcap = "Large"
        self.exclude_exchanges = True

        self.ticker = ticker

        self.stocks_data: dict = {}
        self.tickers: List = list()

        if ticker:
            data = yf.utils.get_json(f"https://finance.yahoo.com/quote/{ticker}")

            if "summaryProfile" in data:
                self.country = data["summaryProfile"]["country"]
                if self.country not in financedatabase_model.get_countries():
                    similar_cmd = difflib.get_close_matches(
                        self.country,
                        financedatabase_model.get_countries(),
                        n=1,
                        cutoff=0.7,
                    )
                    if similar_cmd:
                        self.country = similar_cmd[0]
                self.sector = data["summaryProfile"]["sector"]
                if self.sector not in financedatabase_model.get_sectors():
                    similar_cmd = difflib.get_close_matches(
                        self.sector,
                        financedatabase_model.get_sectors(),
                        n=1,
                        cutoff=0.7,
                    )
                    if similar_cmd:
                        self.sector = similar_cmd[0]
                self.industry = data["summaryProfile"]["industry"]
                if self.industry not in financedatabase_model.get_industries():
                    similar_cmd = difflib.get_close_matches(
                        self.industry,
                        financedatabase_model.get_industries(),
                        n=1,
                        cutoff=0.7,
                    )
                    if similar_cmd:
                        self.industry = similar_cmd[0]
            if "price" in data:
                mktcap = data["price"]["marketCap"]
                if mktcap < 2_000_000_000:
                    self.mktcap = "Small"
                elif mktcap > 10_000_000_000:
                    self.mktcap = "Large"
                else:
                    self.mktcap = "Mid"

        if session and gtff.USE_PROMPT_TOOLKIT:
            choices: dict = {c: {} for c in self.controller_choices}
            choices["mktcap"] = {c: None for c in self.mktcap_choices}
            choices["clear"] = {c: None for c in self.clear_choices}
            choices["metric"] = {c: None for c in self.metric_choices}
            # This menu contains dynamic choices that may change during runtime
            self.choices = choices
            self.completer = NestedCompleter.from_nested_dict(choices)

    def update_runtime_choices(self):
        """Update runtime choices"""
        if session and gtff.USE_PROMPT_TOOLKIT:
            self.choices["industry"] = {
                i: None
                for i in financedatabase_model.get_industries(
                    country=self.country, sector=self.sector
                )
            }
            self.choices["sector"] = {
                s: None
                for s in financedatabase_model.get_sectors(
                    industry=self.industry, country=self.country
                )
            }
            self.choices["country"] = {
                c: None
                for c in financedatabase_model.get_countries(
                    industry=self.industry, sector=self.sector
                )
            }
            self.completer = NestedCompleter.from_nested_dict(self.choices)

    def print_help(self):
        """Print help"""
        s = "[unvl]" if not self.sector else ""
        i = "[unvl]" if not self.industry else ""
        c = "[unvl]" if not self.country else ""
        m = "[unvl]" if not self.mktcap else ""
        s_ = "[/unvl]" if not self.sector else ""
        i_ = "[/unvl]" if not self.industry else ""
        c_ = "[/unvl]" if not self.country else ""
        m_ = "[/unvl]" if not self.mktcap else ""
        has_no_tickers = "[unvl]" if len(self.tickers) == 0 else ""
        has_no_tickers_ = "[unvl/]" if len(self.tickers) == 0 else ""
        help_text = f"""[cmds]
    load          load a specific ticker and all it's corresponding parameters

    clear         clear all or one of industry, sector, country and market cap parameters
    industry      see existing industries, or set industry if arg specified
    sector        see existing sectors, or set sector if arg specified
    country       see existing countries, or set country if arg specified
    mktcap        set mktcap between small, mid or large
    exchange      revert exclude international exchanges flag
[/cmds]
[param]Industry          : [/param]{self.industry}
[param]Sector            : [/param]{self.sector}
[param]Country           : [/param]{self.country}
[param]Market Cap        : [/param]{self.mktcap}
[param]Exclude Exchanges : [/param]{self.exclude_exchanges}

[info]Statistics[/info]{c}[cmds]
    cps           companies per Sector based on Country{c_}{m} and Market Cap{m_}{c}
    cpic          companies per Industry based on Country{c_}{m} and Market Cap{m_}{s}
    cpis          companies per Industry based on Sector{s_}{m} and Market Cap{m_}{s}
    cpcs          companies per Country based on Sector{s_}{m} and Market Cap{m_}{i}
    cpci          companies per Country based on Industry{i_}{m} and Market Cap{m_}[/cmds]

[info]Financials {'- loaded data (fast mode) 'if self.stocks_data else ''}[/info][cmds]
    sama          see all metrics available
    metric        visualise financial metric across filters selected[/cmds]
{has_no_tickers}
[param]Returned tickers: [/param]{', '.join(self.tickers)}
[menu]>   ca            take these to comparison analysis menu[/menu]
{has_no_tickers_}"""
        console.print(text=help_text, menu="Stocks - Sector and Industry Analysis")

    def custom_reset(self):
        """Class specific component of reset command"""
        if self.ticker:
            return ["stocks", f"load {self.ticker}", "sia"]
        return []

    def call_load(self, other_args: List[str]):
        """Process load command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="load",
            description="Load stock ticker to perform analysis on. When the data source"
            + " is 'yf', an Indian ticker can be loaded by using '.NS' at the end,"
            + " e.g. 'SBIN.NS'. See available market in"
            + " https://help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html.",
        )
        parser.add_argument(
            "-t",
            "--ticker",
            action="store",
            dest="ticker",
            required="-h" not in other_args,
            help="Stock ticker",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-t")
        ns_parser = parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            df_stock_candidate = stocks_helper.load(
                ns_parser.ticker,
            )
            if not df_stock_candidate.empty:
                if "." in ns_parser.ticker:
                    self.ticker = ns_parser.ticker.upper().split(".")[0]
                else:
                    self.ticker = ns_parser.ticker.upper()

                data = yf.utils.get_json(
                    f"https://finance.yahoo.com/quote/{self.ticker}"
                )

                if "summaryProfile" in data:
                    self.country = data["summaryProfile"]["country"]
                    if self.country not in financedatabase_model.get_countries():
                        similar_cmd = difflib.get_close_matches(
                            self.country,
                            financedatabase_model.get_countries(),
                            n=1,
                            cutoff=0.7,
                        )
                        if similar_cmd:
                            self.country = similar_cmd[0]

                    self.sector = data["summaryProfile"]["sector"]
                    if self.sector not in financedatabase_model.get_sectors():
                        similar_cmd = difflib.get_close_matches(
                            self.sector,
                            financedatabase_model.get_sectors(),
                            n=1,
                            cutoff=0.7,
                        )
                        if similar_cmd:
                            self.sector = similar_cmd[0]

                    self.industry = data["summaryProfile"]["industry"]
                    if self.industry not in financedatabase_model.get_industries():
                        similar_cmd = difflib.get_close_matches(
                            self.industry,
                            financedatabase_model.get_industries(),
                            n=1,
                            cutoff=0.7,
                        )
                        if similar_cmd:
                            self.industry = similar_cmd[0]

                if "price" in data:
                    mktcap = data["price"]["marketCap"]

                    if mktcap < 2_000_000_000:
                        self.mktcap = "Small"
                    elif mktcap > 10_000_000_000:
                        self.mktcap = "Large"
                    else:
                        self.mktcap = "Mid"

                self.stocks_data = {}
                self.update_runtime_choices()

    def call_industry(self, other_args: List[str]):
        """Process industry command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="industry",
            description="See existing industries, or set industry if arg specified",
        )
        parser.add_argument(
            "-n",
            "--name",
            type=str,
            dest="name",
            nargs="+",
            help="industry to select",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-n")
        ns_parser = parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            possible_industries = financedatabase_model.get_industries(
                country=self.country,
                sector=self.sector,
            )
            if ns_parser.name:
                if " ".join(ns_parser.name) in possible_industries:
                    self.industry = " ".join(ns_parser.name)
                    # if we get the industry, then we also automatically know the sector
                    self.sector = financedatabase_model.get_sectors(
                        industry=self.industry
                    )[0]
                    self.update_runtime_choices()
                else:
                    console.print(
                        f"Industry '{' '.join(ns_parser.name)}' does not exist."
                    )
                    similar_cmd = difflib.get_close_matches(
                        " ".join(ns_parser.name),
                        possible_industries,
                        n=1,
                        cutoff=0.75,
                    )
                    if similar_cmd:
                        console.print(f"Replacing by '{similar_cmd[0]}'")
                        self.industry = similar_cmd[0]
                        # if we get the industry, then we also automatically know the sector
                        self.sector = financedatabase_model.get_sectors(
                            industry=self.industry
                        )[0]
                        self.update_runtime_choices()
                    else:
                        similar_cmd = difflib.get_close_matches(
                            " ".join(ns_parser.name),
                            possible_industries,
                            n=1,
                            cutoff=0.5,
                        )
                        if similar_cmd:
                            console.print(f"Did you mean '{similar_cmd[0]}'?")
            else:
                for industry in possible_industries:
                    console.print(industry)

            self.stocks_data = {}
            console.print("")

    def call_sector(self, other_args: List[str]):
        """Process sector command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="sector",
            description="See existing sectors, or set sector if arg specified",
        )
        parser.add_argument(
            "-n",
            "--name",
            type=str,
            dest="name",
            nargs="+",
            help="sector to select",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-n")
        ns_parser = parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            possible_sectors = financedatabase_model.get_sectors(
                self.industry, self.country
            )
            if ns_parser.name:
                if " ".join(ns_parser.name) in possible_sectors:
                    self.sector = " ".join(ns_parser.name)
                    self.update_runtime_choices()
                else:
                    console.print(
                        f"Sector '{' '.join(ns_parser.name)}' does not exist."
                    )

                    similar_cmd = difflib.get_close_matches(
                        " ".join(ns_parser.name),
                        possible_sectors,
                        n=1,
                        cutoff=0.75,
                    )

                    if similar_cmd:
                        console.print(f"Replacing by '{similar_cmd[0]}'")
                        self.sector = similar_cmd[0]
                        self.update_runtime_choices()
                    else:
                        similar_cmd = difflib.get_close_matches(
                            " ".join(ns_parser.name),
                            possible_sectors,
                            n=1,
                            cutoff=0.5,
                        )
                        if similar_cmd:
                            console.print(f"Did you mean '{similar_cmd[0]}'?")

            else:
                for sector in possible_sectors:
                    console.print(sector)

            self.stocks_data = {}
            console.print("")

    def call_country(self, other_args: List[str]):
        """Process country command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="country",
            description="See existing countries, or set country if arg specified",
        )
        parser.add_argument(
            "-n",
            "--name",
            type=str,
            dest="name",
            nargs="+",
            help="country to select",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-n")
        ns_parser = parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            possible_countries = financedatabase_model.get_countries(
                industry=self.industry, sector=self.sector
            )
            if ns_parser.name:
                if " ".join(ns_parser.name) in possible_countries:
                    self.country = " ".join(ns_parser.name)
                    self.update_runtime_choices()
                else:
                    console.print(
                        f"Country '{' '.join(ns_parser.name)}' does not exist."
                    )
                    similar_cmd = difflib.get_close_matches(
                        " ".join(ns_parser.name),
                        possible_countries,
                        n=1,
                        cutoff=0.75,
                    )
                    if similar_cmd:
                        console.print(f"Replacing by '{similar_cmd[0]}'")
                        self.country = similar_cmd[0]
                        self.update_runtime_choices()
                    else:
                        similar_cmd = difflib.get_close_matches(
                            " ".join(ns_parser.name),
                            possible_countries,
                            n=1,
                            cutoff=0.5,
                        )
                        if similar_cmd:
                            console.print(f"Did you mean '{similar_cmd[0]}'?")
            else:
                for country in possible_countries:
                    console.print(country)

            self.stocks_data = {}
            console.print("")

    def call_mktcap(self, other_args: List[str]):
        """Process mktcap command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="mktcap",
            description="Set mktcap between small, mid or large",
        )
        parser.add_argument(
            "-n",
            "--name",
            type=str,
            dest="name",
            choices=self.mktcap_choices,
            help="market cap to select",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-n")
        ns_parser = parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            if ns_parser.name:
                self.mktcap = ns_parser.name.capitalize()
            else:
                console.print("Select between market cap: Small, Mid and Large")

            self.stocks_data = {}
            console.print("")

    # pylint:disable=attribute-defined-outside-init
    def call_exchange(self, other_args: List[str]):
        """Process exchange command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="exchange",
            description="Swap exclude international exchanges flag",
        )
        ns_parser = parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            self.exclude_exchanges = not self.exclude_exchanges
            console.print(
                f"International exchanges {'excluded' if self.exclude_exchanges else 'included'}",
                "\n",
            )

        self.stocks_data = {}
        console.print("")

    def call_clear(self, other_args: List[str]):
        """Process clear command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="clear",
            description="Clear all or a particular parameter",
        )
        parser.add_argument(
            "-p",
            "--param",
            type=str,
            dest="parameter",
            choices=self.clear_choices,
            help="parameter to clear",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-p")
        ns_parser = parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            if ns_parser.parameter == "industry":
                self.industry = ""
            elif ns_parser.parameter == "sector":
                self.sector = ""
            elif ns_parser.parameter == "country":
                self.country = ""
            elif ns_parser.parameter == "mktcap":
                self.mktcap = ""
            else:
                self.industry = ""
                self.sector = ""
                self.country = ""
                self.mktcap = ""

            self.exclude_exchanges = True
            self.ticker = ""
            self.update_runtime_choices()
            self.stocks_data = {}
            console.print("")

    def call_sama(self, other_args: List[str]):
        """Process sama command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="sama",
            description="See all metrics available",
        )
        ns_parser = parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            help_text = """
        roa           return on assets
        roe           return on equity
        cr            current ratio
        qr            quick ratio
        de            debt to equity
        tc            total cash
        tcs           total cash per share
        tr            total revenue
        rps           revenue per share
        rg            revenue growth
        eg            earnings growth
        pm            profit margins
        gp            gross profits
        gm            gross margins
        ocf           operating cash flow
        om            operating margins
        fcf           free cash flow
        td            total debt
        ebitda        earnings before interest, taxes, depreciation and amortization
        ebitdam       ebitda margins
        rec           recommendation mean
        mc            market cap
        fte           full time employees
        er            enterprise to revenue
        bv            book value
        ss            shares short
        pb            price to book
        beta          beta
        fs            float shares
        sr            short ratio
        peg           peg ratio
        ev            enterprise value
        fpe           forward P/E
            """
            console.print(help_text)

    def call_metric(self, other_args: List[str]):
        """Process metric command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="metric",
            description="Visualize a particular metric with the filters selected",
        )
        parser.add_argument(
            "-m",
            "--metric",
            dest="metric",
            required="-h" not in other_args,
            help="Metric to visualize",
            choices=self.metric_choices,
        )
        parser.add_argument(
            "-l",
            "--limit",
            dest="limit",
            default=10,
            help="Limit number of companies to display",
            type=check_positive,
        )
        parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            dest="raw",
            default=False,
            help="Output all raw data",
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-m")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            (
                self.stocks_data,
                self.tickers,
            ) = financedatabase_view.display_bars_financials(
                self.metric_yf_keys[ns_parser.metric][0],
                self.metric_yf_keys[ns_parser.metric][1],
                self.country,
                self.sector,
                self.industry,
                self.mktcap,
                self.exclude_exchanges,
                ns_parser.limit,
                ns_parser.export,
                ns_parser.raw,
                self.stocks_data,
            )

    def call_cps(self, other_args: List[str]):
        """Process cps command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="cps",
            description="Companies per Sectors based on Country and Market Cap",
        )
        parser.add_argument(
            "-M",
            "--max",
            dest="max_sectors_to_display",
            default=15,
            help="Maximum number of sectors to display",
            type=check_positive,
        )
        parser.add_argument(
            "-m",
            "--min",
            action="store",
            dest="min_pct_to_display_sector",
            type=check_proportion_range,
            default=0.015,
            help="Minimum percentage to display sector",
        )
        parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            dest="raw",
            default=False,
            help="Output all raw data",
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            if not self.country:
                console.print("The country parameter needs to be selected!\n")
            else:
                financedatabase_view.display_companies_per_sector_in_country(
                    self.country,
                    self.mktcap,
                    self.exclude_exchanges,
                    ns_parser.export,
                    ns_parser.raw,
                    ns_parser.max_sectors_to_display,
                    ns_parser.min_pct_to_display_sector,
                )

    def call_cpic(self, other_args: List[str]):
        """Process cpic command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="cpic",
            description="Companies per Industry based on Country and Market Cap",
        )
        parser.add_argument(
            "-M",
            "--max",
            dest="max_industries_to_display",
            default=15,
            help="Maximum number of industries to display",
            type=check_positive,
        )
        parser.add_argument(
            "-m",
            "--min",
            action="store",
            dest="min_pct_to_display_industry",
            type=check_proportion_range,
            default=0.015,
            help="Minimum percentage to display industry",
        )
        parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            dest="raw",
            default=False,
            help="Output all raw data",
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            if not self.country:
                console.print("The country parameter needs to be selected!\n")
            else:
                financedatabase_view.display_companies_per_industry_in_country(
                    self.country,
                    self.mktcap,
                    self.exclude_exchanges,
                    ns_parser.export,
                    ns_parser.raw,
                    ns_parser.max_industries_to_display,
                    ns_parser.min_pct_to_display_industry,
                )

    def call_cpis(self, other_args: List[str]):
        """Process cpis command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="cpis",
            description="Companies per Industry based on Sector and Market Cap",
        )
        parser.add_argument(
            "-M",
            "--max",
            dest="max_industries_to_display",
            default=15,
            help="Maximum number of industries to display",
            type=check_positive,
        )
        parser.add_argument(
            "-m",
            "--min",
            action="store",
            dest="min_pct_to_display_industry",
            type=check_proportion_range,
            default=0.015,
            help="Minimum percentage to display industry",
        )
        parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            dest="raw",
            default=False,
            help="Output all raw data",
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            if not self.sector:
                console.print("The sector parameter needs to be selected!\n")
            else:
                financedatabase_view.display_companies_per_industry_in_sector(
                    self.sector,
                    self.mktcap,
                    self.exclude_exchanges,
                    ns_parser.export,
                    ns_parser.raw,
                    ns_parser.max_industries_to_display,
                    ns_parser.min_pct_to_display_industry,
                )

    def call_cpcs(self, other_args: List[str]):
        """Process cpcs command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="cpcs",
            description="Companies per Country based on Sector and Market Cap",
        )
        parser.add_argument(
            "-M",
            "--max",
            dest="max_countries_to_display",
            default=15,
            help="Maximum number of countries to display",
            type=check_positive,
        )
        parser.add_argument(
            "-m",
            "--min",
            action="store",
            dest="min_pct_to_display_country",
            type=check_proportion_range,
            default=0.015,
            help="Minimum percentage to display country",
        )
        parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            dest="raw",
            default=False,
            help="Output all raw data",
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            if not self.sector:
                console.print("The sector parameter needs to be selected!\n")
            else:
                financedatabase_view.display_companies_per_country_in_sector(
                    self.sector,
                    self.mktcap,
                    self.exclude_exchanges,
                    ns_parser.export,
                    ns_parser.raw,
                    ns_parser.max_countries_to_display,
                    ns_parser.min_pct_to_display_country,
                )

    def call_cpci(self, other_args: List[str]):
        """Process cpci command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="cpci",
            description="Companies per Country based on Industry and Market Cap",
        )
        parser.add_argument(
            "-M",
            "--max",
            dest="max_countries_to_display",
            default=15,
            help="Maximum number of countries to display",
            type=check_positive,
        )
        parser.add_argument(
            "-m",
            "--min",
            action="store",
            dest="min_pct_to_display_country",
            type=check_proportion_range,
            default=0.015,
            help="Minimum percentage to display country",
        )
        parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            dest="raw",
            default=False,
            help="Output all raw data",
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            if not self.industry:
                console.print("The industry parameter needs to be selected!\n")
            else:
                financedatabase_view.display_companies_per_country_in_industry(
                    self.industry,
                    self.mktcap,
                    self.exclude_exchanges,
                    ns_parser.export,
                    ns_parser.raw,
                    ns_parser.max_countries_to_display,
                    ns_parser.min_pct_to_display_country,
                )

    def call_ca(self, _):
        """Call the comparison analysis menu with selected tickers"""
        if self.tickers:
            self.queue = ca_controller.ComparisonAnalysisController(
                self.tickers, self.queue
            ).menu(custom_path_menu_above="/stocks/")
        else:
            console.print(
                "No main ticker loaded to go into comparison analysis menu", "\n"
            )
