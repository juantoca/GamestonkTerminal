"""Crypto Technical Analysis Controller Module"""
__docformat__ = "numpy"
# pylint:disable=too-many-lines

import argparse
from typing import List
from datetime import datetime, timedelta

import pandas as pd
from prompt_toolkit.completion import NestedCompleter
from gamestonk_terminal.rich_config import console
from gamestonk_terminal.parent_classes import BaseController
from gamestonk_terminal.cryptocurrency.cryptocurrency_helpers import load
from gamestonk_terminal import feature_flags as gtff
from gamestonk_terminal.helper_funcs import (
    EXPORT_BOTH_RAW_DATA_AND_FIGURES,
    parse_known_args_and_warn,
    check_positive_list,
    check_positive,
    valid_date,
    valid_date_in_past,
)
from gamestonk_terminal.menu import session
from gamestonk_terminal.common.technical_analysis import (
    custom_indicators_view,
    momentum_view,
    overlap_view,
    trend_indicators_view,
    volatility_view,
    volume_view,
)


class TechnicalAnalysisController(BaseController):
    """Technical Analysis Controller class"""

    CHOICES_COMMANDS = [
        "load",
        "ema",
        "sma",
        "vwap",
        "zlma",
        "cci",
        "macd",
        "rsi",
        "stoch",
        "fisher",
        "cg",
        "adx",
        "aroon",
        "bbands",
        "donchian",
        "ad",
        "obv",
        "fib",
    ]

    def __init__(
        self,
        ticker: str,
        start: datetime,
        interval: str,
        stock: pd.DataFrame,
        queue: List[str] = None,
    ):
        """Constructor"""
        super().__init__("/crypto/ta/", queue)

        self.ticker = ticker
        self.start = start
        self.interval = interval
        self.stock = stock
        self.stock["Adj Close"] = stock["Close"]
        self.currency = ""

        if session and gtff.USE_PROMPT_TOOLKIT:
            choices: dict = {c: {} for c in self.controller_choices}
            self.completer = NestedCompleter.from_nested_dict(choices)

    def print_help(self):
        """Print help"""
        crypto_str = f" {self.ticker} (from {self.start.strftime('%Y-%m-%d')})"
        help_text = f"""[cmds]
[param]Coin Loaded: [/param]{crypto_str}

[info]Overlap:[/info]
    ema         exponential moving average
    sma         simple moving average
    wma         weighted moving average
    hma         hull moving average
    zlma        zero lag moving average
    vwap        volume weighted average price
[info]Momentum:[/info]
    cci         commodity channel index
    macd        moving average convergence/divergence
    rsi         relative strength index
    stoch       stochastic oscillator
    fisher      fisher transform
    cg          centre of gravity
[info]Trend:[/info]
    adx         average directional movement index
    aroon       aroon indicator
[info]Volatility:[/info]
    bbands      bollinger bands
    donchian    donchian channels
    kc          keltner channels
[info]Volume:[/info]
    ad          accumulation/distribution line
    adosc       chaikin oscillator
    obv         on balance volume
[info]Custom:[/info]
    fib         fibonacci retracement[/cmds]
"""
        console.print(text=help_text, menu="Cryptocurrency - Technical Analysis")

    def custom_reset(self):
        """Class specific component of reset command"""
        if self.ticker:
            return ["crypto", f"load {self.ticker}", "ta"]
        return []

    def call_load(self, other_args):
        """Process load command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="load",
            description="Load crypto currency to perform analysis on."
            "Available data sources are CoinGecko, CoinPaprika, Binance, Coinbase"
            "By default main source used for analysis is CoinGecko (cg). To change it use --source flag",
        )
        parser.add_argument(
            "-c",
            "--coin",
            help="Coin to get",
            dest="coin",
            type=str,
            required="-h" not in other_args,
        )
        parser.add_argument(
            "--source",
            help="Source of data",
            dest="source",
            choices=("cp", "cg", "bin", "cb"),
            default="cg",
            required=False,
        )
        parser.add_argument(
            "-s",
            "--start",
            type=valid_date_in_past,
            default=(datetime.now() - timedelta(days=366)).strftime("%Y-%m-%d"),
            dest="start",
            help="The starting date (format YYYY-MM-DD) of the crypto",
        )
        parser.add_argument(
            "--vs",
            help="Quote currency (what to view coin vs)",
            dest="vs",
            default="usd",
            type=str,
        )
        parser.add_argument(
            "-i",
            "--interval",
            help="Interval to get data (Only available on binance/coinbase)",
            dest="interval",
            default="1day",
            type=str,
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-c")

        ns_parser = parse_known_args_and_warn(parser, other_args)
        delta = (datetime.now() - ns_parser.start).days
        if ns_parser:
            source = ns_parser.source
            for arg in ["--source", source]:
                if arg in other_args:
                    other_args.remove(arg)

            # TODO: protections in case None is returned
            (self.ticker, _, _, _, self.stock, self.currency) = load(
                coin=ns_parser.coin,
                source=ns_parser.source,
                should_load_ta_data=True,
                days=delta,
                interval=ns_parser.interval,
                vs=ns_parser.vs,
            )
            console.print(f"{delta} Days of {self.ticker} vs {self.currency} loaded\n")

    # TODO: Go through all models and make sure all needed columns are in dfs

    def call_ema(self, other_args: List[str]):
        """Process ema command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="ema",
            description="""
            The Exponential Moving Average is a staple of technical
            analysis and is used in countless technical indicators. In a Simple Moving
            Average, each value in the time period carries equal weight, and values outside
            of the time period are not included in the average. However, the Exponential
            Moving Average is a cumulative calculation, including all data. Past values have
            a diminishing contribution to the average, while more recent values have a greater
            contribution. This method allows the moving average to be more responsive to changes
            in the data.
        """,
        )

        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive_list,
            default=[20, 50],
            help="Window lengths.  Multiple values indicated as comma separated values.",
        )

        parser.add_argument(
            "-o",
            "--offset",
            action="store",
            dest="n_offset",
            type=int,
            default=0,
            help="offset",
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            overlap_view.view_ma(
                ma_type="EMA",
                s_ticker=self.ticker,
                values=self.stock["Close"],
                length=ns_parser.n_length,
                offset=ns_parser.n_offset,
                export=ns_parser.export,
            )

    def call_sma(self, other_args: List[str]):
        """Process sma command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="sma",
            description="""
                Moving Averages are used to smooth the data in an array to
                help eliminate noise and identify trends. The Simple Moving Average is literally
                the simplest form of a moving average. Each output value is the average of the
                previous n values. In a Simple Moving Average, each value in the time period carries
                equal weight, and values outside of the time period are not included in the average.
                This makes it less responsive to recent changes in the data, which can be useful for
                filtering out those changes.
            """,
        )

        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive_list,
            default=[20, 50],
            help="Window lengths.  Multiple values indicated as comma separated values. ",
        )

        parser.add_argument(
            "-o",
            "--offset",
            action="store",
            dest="n_offset",
            type=int,
            default=0,
            help="offset",
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")
        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            overlap_view.view_ma(
                ma_type="SMA",
                s_ticker=self.ticker,
                values=self.stock["Close"],
                length=ns_parser.n_length,
                offset=ns_parser.n_offset,
                export=ns_parser.export,
            )

    def call_zlma(self, other_args: List[str]):
        """Process zlma command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="zlma",
            description="""
                The zero lag exponential moving average (ZLEMA) indicator
                was created by John Ehlers and Ric Way. The idea is do a
                regular exponential moving average (EMA) calculation but
                on a de-lagged data instead of doing it on the regular data.
                Data is de-lagged by removing the data from "lag" days ago
                thus removing (or attempting to) the cumulative effect of
                the moving average.
            """,
        )

        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive_list,
            default=[20],
            help="Window lengths.  Multiple values indicated as comma separated values.",
        )

        parser.add_argument(
            "-o",
            "--offset",
            action="store",
            dest="n_offset",
            type=int,
            default=0,
            help="offset",
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            overlap_view.view_ma(
                ma_type="ZLMA",
                s_ticker=self.ticker,
                values=self.stock["Close"],
                length=ns_parser.n_length,
                offset=ns_parser.n_offset,
                export=ns_parser.export,
            )

    def call_vwap(self, other_args: List[str]):
        """Process vwap command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="vwap",
            description="""
                The Volume Weighted Average Price that measures the average typical price
                by volume.  It is typically used with intraday charts to identify general direction.
            """,
        )

        parser.add_argument(
            "-o",
            "--offset",
            action="store",
            dest="n_offset",
            type=int,
            default=0,
            help="offset",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            if self.interval == "1440min":
                console.print("VWAP should be used with intraday data.\n")

            overlap_view.view_vwap(
                s_ticker=self.ticker,
                s_interval=self.interval,
                df_stock=self.stock,
                offset=ns_parser.n_offset,
                export=ns_parser.export,
            )

    def call_cci(self, other_args: List[str]):
        """Process cci command"""

        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="cci",
            description="""
                The CCI is designed to detect beginning and ending market trends.
                The range of 100 to -100 is the normal trading range. CCI values outside of this
                range indicate overbought or oversold conditions. You can also look for price
                divergence in the CCI. If the price is making new highs, and the CCI is not,
                then a price correction is likely.
            """,
        )

        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive,
            default=14,
            help="length",
        )
        parser.add_argument(
            "-s",
            "--scalar",
            action="store",
            dest="n_scalar",
            type=check_positive,
            default=0.015,
            help="scalar",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            momentum_view.display_cci(
                s_ticker=self.ticker,
                df=self.stock,
                length=ns_parser.n_length,
                scalar=ns_parser.n_scalar,
                export=ns_parser.export,
            )

    def call_macd(self, other_args: List[str]):
        """Process macd command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="macd",
            description="""
                The Moving Average Convergence Divergence (MACD) is the difference
                between two Exponential Moving Averages. The Signal line is an Exponential Moving
                Average of the MACD. \n \n The MACD signals trend changes and indicates the start
                of new trend direction. High values indicate overbought conditions, low values
                indicate oversold conditions. Divergence with the price indicates an end to the
                current trend, especially if the MACD is at extreme high or low values. When the MACD
                line crosses above the signal line a buy signal is generated. When the MACD crosses
                below the signal line a sell signal is generated. To confirm the signal, the MACD
                should be above zero for a buy, and below zero for a sell.
            """,
        )
        parser.add_argument(
            "-f",
            "--fast",
            action="store",
            dest="n_fast",
            type=check_positive,
            default=12,
            help="The short period.",
        )
        parser.add_argument(
            "-s",
            "--slow",
            action="store",
            dest="n_slow",
            type=check_positive,
            default=26,
            help="The long period.",
        )
        parser.add_argument(
            "--signal",
            action="store",
            dest="n_signal",
            type=check_positive,
            default=9,
            help="The signal period.",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            momentum_view.display_macd(
                s_ticker=self.ticker,
                values=self.stock["Adj Close"],
                n_fast=ns_parser.n_fast,
                n_slow=ns_parser.n_slow,
                n_signal=ns_parser.n_signal,
                export=ns_parser.export,
            )

    def call_rsi(self, other_args: List[str]):
        """Process rsi command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="rsi",
            description="""
                The Relative Strength Index (RSI) calculates a ratio of the
                recent upward price movements to the absolute price movement. The RSI ranges
                from 0 to 100. The RSI is interpreted as an overbought/oversold indicator when
                the value is over 70/below 30. You can also look for divergence with price. If
                the price is making new highs/lows, and the RSI is not, it indicates a reversal.
            """,
        )

        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive,
            default=14,
            help="length",
        )
        parser.add_argument(
            "-s",
            "--scalar",
            action="store",
            dest="n_scalar",
            type=check_positive,
            default=100,
            help="scalar",
        )
        parser.add_argument(
            "-d",
            "--drift",
            action="store",
            dest="n_drift",
            type=check_positive,
            default=1,
            help="drift",
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            momentum_view.display_rsi(
                s_ticker=self.ticker,
                prices=self.stock["Adj Close"],
                length=ns_parser.n_length,
                scalar=ns_parser.n_scalar,
                drift=ns_parser.n_drift,
                export=ns_parser.export,
            )

    def call_stoch(self, other_args: List[str]):
        """Process stoch command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="stoch",
            description="""
                The Stochastic Oscillator measures where the close is in relation
                to the recent trading range. The values range from zero to 100. %D values over 75
                indicate an overbought condition; values under 25 indicate an oversold condition.
                When the Fast %D crosses above the Slow %D, it is a buy signal; when it crosses
                below, it is a sell signal. The Raw %K is generally considered too erratic to use
                for crossover signals.
            """,
        )
        parser.add_argument(
            "-k",
            "--fastkperiod",
            action="store",
            dest="n_fastkperiod",
            type=check_positive,
            default=14,
            help="The time period of the fastk moving average",
        )
        parser.add_argument(
            "-d",
            "--slowdperiod",
            action="store",
            dest="n_slowdperiod",
            type=check_positive,
            default=3,
            help="The time period of the slowd moving average",
        )
        parser.add_argument(
            "--slowkperiod",
            action="store",
            dest="n_slowkperiod",
            type=check_positive,
            default=3,
            help="The time period of the slowk moving average",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            momentum_view.display_stoch(
                s_ticker=self.ticker,
                df_stock=self.stock,
                fastkperiod=ns_parser.n_fastkperiod,
                slowdperiod=ns_parser.n_slowdperiod,
                slowkperiod=ns_parser.n_slowkperiod,
                export=ns_parser.export,
            )

    def call_fisher(self, other_args: List[str]):
        """Process fisher command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="fisher",
            description="""
                The Fisher Transform is a technical indicator created by John F. Ehlers
                that converts prices into a Gaussian normal distribution.1 The indicator
                highlights when prices have   moved to an extreme, based on recent prices.
                This may help in spotting turning points in the price of an asset. It also
                helps show the trend and isolate the price waves within a trend.
            """,
        )
        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive,
            default=14,
            help="length",
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            momentum_view.display_fisher(
                s_ticker=self.ticker,
                df_stock=self.stock,
                length=ns_parser.n_length,
                export=ns_parser.export,
            )

    def call_cg(self, other_args: List[str]):
        """Process cg command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="cg",
            description="""
                The Center of Gravity indicator, in short, is used to anticipate future price movements
                and to trade on price reversals as soon as they happen. However, just like other oscillators,
                the COG indicator returns the best results in range-bound markets and should be avoided when
                the price is trending. Traders who use it will be able to closely speculate the upcoming
                price change of the asset.
            """,
        )
        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive,
            default=14,
            help="length",
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-l")

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            momentum_view.display_cg(
                s_ticker=self.ticker,
                values=self.stock["Adj Close"],
                length=ns_parser.n_length,
                export=ns_parser.export,
            )

    def call_adx(self, other_args: List[str]):
        """Process adx command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="adx",
            description="""
            The ADX is a Welles Wilder style moving average of the Directional Movement Index (DX).
            The values range from 0 to 100, but rarely get above 60. To interpret the ADX, consider
            a high number to be a strong trend, and a low number, a weak trend.
        """,
        )

        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive,
            default=14,
            help="length",
        )

        parser.add_argument(
            "-s",
            "--scalar",
            action="store",
            dest="n_scalar",
            type=check_positive,
            default=100,
            help="scalar",
        )

        parser.add_argument(
            "-d",
            "--drift",
            action="store",
            dest="n_drift",
            type=check_positive,
            default=1,
            help="drift",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            trend_indicators_view.display_adx(
                s_ticker=self.ticker,
                df_stock=self.stock,
                length=ns_parser.n_length,
                scalar=ns_parser.n_scalar,
                drift=ns_parser.n_drift,
                export=ns_parser.export,
            )

    def call_aroon(self, other_args: List[str]):
        """Process aroon command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="aroon",
            description="""
                The word aroon is Sanskrit for "dawn's early light." The Aroon
                indicator attempts to show when a new trend is dawning. The indicator consists
                of two lines (Up and Down) that measure how long it has been since the highest
                high/lowest low has occurred within an n period range. \n \n When the Aroon Up is
                staying between 70 and 100 then it indicates an upward trend. When the Aroon Down
                is staying between 70 and 100 then it indicates an downward trend. A strong upward
                trend is indicated when the Aroon Up is above 70 while the Aroon Down is below 30.
                Likewise, a strong downward trend is indicated when the Aroon Down is above 70 while
                the Aroon Up is below 30. Also look for crossovers. When the Aroon Down crosses above
                the Aroon Up, it indicates a weakening of the upward trend (and vice versa).
            """,
        )

        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive,
            default=25,
            help="length",
        )

        parser.add_argument(
            "-s",
            "--scalar",
            action="store",
            dest="n_scalar",
            type=check_positive,
            default=100,
            help="scalar",
        )

        parser.add_argument(
            "-o",
            "--offset",
            action="store",
            dest="n_offset",
            type=check_positive,
            default=0,
            help="offset",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            trend_indicators_view.display_aroon(
                s_ticker=self.ticker,
                df_stock=self.stock,
                length=ns_parser.n_length,
                scalar=ns_parser.n_scalar,
                export=ns_parser.export,
            )

    def call_bbands(self, other_args: List[str]):
        """Process bbands command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="bbands",
            description="""
                Bollinger Bands consist of three lines. The middle band is a simple
                moving average (generally 20 periods) of the typical price (TP). The upper and lower
                bands are F standard deviations (generally 2) above and below the middle band.
                The bands widen and narrow when the volatility of the price is higher or lower,
                respectively. \n \nBollinger Bands do not, in themselves, generate buy or sell signals;
                they are an indicator of overbought or oversold conditions. When the price is near the
                upper or lower band it indicates that a reversal may be imminent. The middle band
                becomes a support or resistance level. The upper and lower bands can also be
                interpreted as price targets. When the price bounces off of the lower band and crosses
                the middle band, then the upper band becomes the price target.
            """,
        )

        parser.add_argument(
            "-l",
            "--length",
            action="store",
            dest="n_length",
            type=check_positive,
            default=5,
            help="length",
        )

        parser.add_argument(
            "-s",
            "--std",
            action="store",
            dest="n_std",
            type=check_positive,
            default=2,
            help="std",
        )

        parser.add_argument(
            "-m",
            "--mamode",
            action="store",
            dest="s_mamode",
            default="sma",
            help="mamode",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            volatility_view.display_bbands(
                ticker=self.ticker,
                df_stock=self.stock,
                length=ns_parser.n_length,
                n_std=ns_parser.n_std,
                mamode=ns_parser.s_mamode,
                export=ns_parser.export,
            )

    def call_donchian(self, other_args: List[str]):
        """Process donchian command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="donchian",
            description="""
                Donchian Channels are three lines generated by moving average
                calculations that comprise an indicator formed by upper and lower
                bands around a midrange or median band. The upper band marks the
                highest price of a security over N periods while the lower band
                marks the lowest price of a security over N periods. The area
                between the upper and lower bands represents the Donchian Channel.
                """,
        )

        parser.add_argument(
            "-u",
            "--length_upper",
            action="store",
            dest="n_length_upper",
            type=check_positive,
            default=20,
            help="length",
        )

        parser.add_argument(
            "-l",
            "--length_lower",
            action="store",
            dest="n_length_lower",
            type=check_positive,
            default=20,
            help="length",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            volatility_view.display_donchian(
                ticker=self.ticker,
                df_stock=self.stock,
                upper_length=ns_parser.n_length_upper,
                lower_length=ns_parser.n_length_lower,
                export=ns_parser.export,
            )

    def call_ad(self, other_args: List[str]):
        """Process ad command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="ad",
            description="""
                The Accumulation/Distribution Line is similar to the On Balance
                Volume (OBV), which sums the volume times +1/-1 based on whether the close is
                higher than the previous close. The Accumulation/Distribution indicator, however
                multiplies the volume by the close location value (CLV). The CLV is based on the
                movement of the issue within a single bar and can be +1, -1 or zero. \n \n
                The Accumulation/Distribution Line is interpreted by looking for a divergence in
                the direction of the indicator relative to price. If the Accumulation/Distribution
                Line is trending upward it indicates that the price may follow. Also, if the
                Accumulation/Distribution Line becomes flat while the price is still rising (or falling)
                then it signals an impending flattening of the price.
            """,
        )

        parser.add_argument(
            "--open",
            action="store_true",
            default=False,
            dest="b_use_open",
            help="uses open value of stock",
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            volume_view.display_ad(
                s_ticker=self.ticker,
                df_stock=self.stock,
                use_open=ns_parser.b_use_open,
                export=ns_parser.export,
            )

    def call_obv(self, other_args: List[str]):
        """Process obv command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="obv",
            description="""
                The On Balance Volume (OBV) is a cumulative total of the up and
                down volume. When the close is higher than the previous close, the volume is added
                to the running total, and when the close is lower than the previous close, the volume
                is subtracted from the running total. \n \n To interpret the OBV, look for the OBV
                to move with the price or precede price moves. If the price moves before the OBV,
                then it is a non-confirmed move. A series of rising peaks, or falling troughs, in the
                OBV indicates a strong trend. If the OBV is flat, then the market is not trending.
            """,
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            volume_view.display_obv(
                s_ticker=self.ticker,
                df_stock=self.stock,
                export=ns_parser.export,
            )

    def call_fib(self, other_args: List[str]):
        """Process fib command"""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="fib",
            description="Calculates the fibonacci retracement levels",
        )

        parser.add_argument(
            "-p",
            "--period",
            dest="period",
            type=int,
            help="Days to lookback for retracement",
            default=120,
        )

        parser.add_argument(
            "--start",
            dest="start",
            type=valid_date,
            help="Starting date to select",
            required="--end" in other_args,
        )

        parser.add_argument(
            "--end",
            dest="end",
            type=valid_date,
            help="Ending date to select",
            required="--start" in other_args,
        )

        ns_parser = parse_known_args_and_warn(
            parser, other_args, EXPORT_BOTH_RAW_DATA_AND_FIGURES
        )
        if ns_parser:
            custom_indicators_view.fibonacci_retracement(
                s_ticker=self.ticker,
                df_stock=self.stock,
                period=ns_parser.period,
                start_date=ns_parser.start,
                end_date=ns_parser.end,
                export=ns_parser.export,
            )
