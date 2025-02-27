"""Backtesting Controller Module"""
__docformat__ = "numpy"

import argparse
from typing import List

import matplotlib as mpl
import pandas as pd
from prompt_toolkit.completion import NestedCompleter
from gamestonk_terminal.rich_config import console

from gamestonk_terminal.parent_classes import BaseController
from gamestonk_terminal import feature_flags as gtff
from gamestonk_terminal.helper_funcs import (
    check_non_negative_float,
    check_positive,
    parse_known_args_and_warn,
    EXPORT_ONLY_RAW_DATA_ALLOWED,
    valid_date,
)
from gamestonk_terminal.menu import session


# This code below aims to fix an issue with the fnn module, used by bt module
# which forces matplotlib backend to be 'agg' which doesn't allow to plot
# Save current matplotlib backend
default_backend = mpl.get_backend()
# pylint: disable=wrong-import-position
from gamestonk_terminal.stocks.backtesting import bt_view  # noqa: E402

# Restore backend matplotlib used
mpl.use(default_backend)


class BacktestingController(BaseController):
    """Backtesting Controller class"""

    CHOICES_COMMANDS = ["ema", "ema_cross", "rsi", "whatif"]

    def __init__(self, ticker: str, stock: pd.DataFrame, queue: List[str] = None):
        """Constructor"""
        super().__init__("/stocks/bt/", queue)

        self.ticker = ticker
        self.stock = stock

        if session and gtff.USE_PROMPT_TOOLKIT:
            choices: dict = {c: {} for c in self.controller_choices}
            self.completer = NestedCompleter.from_nested_dict(choices)

    def print_help(self):
        """Print help"""
        help_text = f"""
[param]Ticker: [/param]{self.ticker.upper()}[cmds]

    whatif      what if you had bought X shares on day Y

    ema         buy when price exceeds EMA(l)
    ema_cross   buy when EMA(short) > EMA(long)
    rsi         buy when RSI < low and sell when RSI > high[/cmds]
        """
        console.print(text=help_text, menu="Stocks - Backtesting")

    def custom_reset(self):
        """Class specific component of reset command"""
        if self.ticker:
            return ["stocks", f"load {self.ticker}", "bt"]
        return []

    def call_whatif(self, other_args: List[str]):
        """Call whatif"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="whatif",
            description="Displays what if scenario of having bought X shares at date Y",
        )
        parser.add_argument(
            "-d",
            "--date",
            default=None,
            dest="date_shares_acquired",
            type=valid_date,
            help="Date at which the shares were acquired",
        )
        parser.add_argument(
            "-n",
            "--number",
            default=1.0,
            type=check_non_negative_float,
            help="Number of shares acquired",
            dest="num_shares_acquired",
        )
        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-d")
        ns_parser = parse_known_args_and_warn(parser, other_args)
        if ns_parser:
            bt_view.display_whatif_scenario(
                ticker=self.ticker,
                num_shares_acquired=ns_parser.num_shares_acquired,
                date_shares_acquired=ns_parser.date_shares_acquired,
            )

    def call_ema(self, other_args: List[str]):
        """Call EMA strategy"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="ema",
            description="Strategy where stock is bought when Price > EMA(l)",
        )
        parser.add_argument(
            "-l",
            default=20,
            dest="length",
            type=check_positive,
            help="EMA period to consider",
        )
        parser.add_argument(
            "--spy",
            action="store_true",
            default=False,
            help="Flag to add spy hold comparison",
            dest="spy",
        )
        parser.add_argument(
            "--no_bench",
            action="store_true",
            default=False,
            help="Flag to not show buy and hold comparison",
            dest="no_bench",
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:

            bt_view.display_simple_ema(
                ticker=self.ticker,
                df_stock=self.stock,
                ema_length=ns_parser.length,
                spy_bt=ns_parser.spy,
                no_bench=ns_parser.no_bench,
                export=ns_parser.export,
            )

    def call_ema_cross(self, other_args: List[str]):
        """Call EMA Cross strategy"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="ema_cross",
            description="Cross between a long and a short Exponential Moving Average.",
        )
        parser.add_argument(
            "-l",
            "--long",
            default=50,
            dest="long",
            type=check_positive,
            help="Long EMA period",
        )
        parser.add_argument(
            "-s",
            "--short",
            default=20,
            dest="short",
            type=check_positive,
            help="Short EMA period",
        )
        parser.add_argument(
            "--spy",
            action="store_true",
            default=False,
            help="Flag to add spy hold comparison",
            dest="spy",
        )
        parser.add_argument(
            "--no_bench",
            action="store_true",
            default=False,
            help="Flag to not show buy and hold comparison",
            dest="no_bench",
        )
        parser.add_argument(
            "--no_short",
            action="store_false",
            default=True,
            dest="shortable",
            help="Flag that disables the short sell",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:

            if ns_parser.long < ns_parser.short:
                console.print("Short EMA period is longer than Long EMA period\n")

            bt_view.display_ema_cross(
                ticker=self.ticker,
                df_stock=self.stock,
                short_ema=ns_parser.short,
                long_ema=ns_parser.long,
                spy_bt=ns_parser.spy,
                no_bench=ns_parser.no_bench,
                shortable=ns_parser.shortable,
                export=ns_parser.export,
            )

    def call_rsi(self, other_args: List[str]):
        """Call RSI Strategy"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="rsi",
            description="""Strategy that buys when the stock is less than a threshold
            and shorts when it exceeds a threshold.""",
        )
        parser.add_argument(
            "-p",
            "--periods",
            dest="periods",
            help="Number of periods for RSI calculation",
            type=check_positive,
            default=14,
        )
        parser.add_argument(
            "-u",
            "--high",
            default=70,
            dest="high",
            type=check_positive,
            help="High (upper) RSI Level",
        )
        parser.add_argument(
            "-l",
            "--low",
            default=30,
            dest="low",
            type=check_positive,
            help="Low RSI Level",
        )
        parser.add_argument(
            "--spy",
            action="store_true",
            default=False,
            help="Flag to add spy hold comparison",
            dest="spy",
        )
        parser.add_argument(
            "--no_bench",
            action="store_true",
            default=False,
            help="Flag to not show buy and hold comparison",
            dest="no_bench",
        )
        parser.add_argument(
            "--no_short",
            action="store_false",
            default=True,
            dest="shortable",
            help="Flag that disables the short sell",
        )
        ns_parser = parse_known_args_and_warn(
            parser, other_args, export_allowed=EXPORT_ONLY_RAW_DATA_ALLOWED
        )
        if ns_parser:
            if ns_parser.high < ns_parser.low:
                console.print("Low RSI value is higher than Low RSI value\n")

            bt_view.display_rsi_strategy(
                ticker=self.ticker,
                df_stock=self.stock,
                periods=ns_parser.periods,
                low_rsi=ns_parser.low,
                high_rsi=ns_parser.high,
                spy_bt=ns_parser.spy,
                no_bench=ns_parser.no_bench,
                shortable=ns_parser.shortable,
                export=ns_parser.export,
            )
