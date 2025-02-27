""" nftcalendar.io View """
__docformat__ = "numpy"

import os
from gamestonk_terminal.helper_funcs import export_data
from gamestonk_terminal.cryptocurrency.nft import nftcalendar_model
from gamestonk_terminal.rich_config import console


def display_nft_today_drops(num: int, export: str):
    """Display NFT today drops. [Source: nftcalendar.io]

    Parameters
    ----------
    num: int
        Number of NFT drops to display
    export : str
        Export dataframe data to csv,json,xlsx file
    """
    nft_drops = nftcalendar_model.get_nft_today_drops()

    if nft_drops.empty:
        console.print("No data found.", "\n")
    else:
        for _, nft in nft_drops.head(num).iterrows():
            console.print(nft["Dates"] + " - " + nft["Title"])
            console.print(nft["Link"])
            console.print(nft["Description"])
            console.print("")

    export_data(
        export,
        os.path.dirname(os.path.abspath(__file__)),
        "today",
        nft_drops,
    )


def display_nft_upcoming_drops(num: int, export: str):
    """Display NFT upcoming drops. [Source: nftcalendar.io]

    Parameters
    ----------
    num: int
        Number of NFT drops to display
    export : str
        Export dataframe data to csv,json,xlsx file
    """
    nft_drops = nftcalendar_model.get_nft_upcoming_drops()

    if nft_drops.empty:
        console.print("No data found.", "\n")
    else:
        for _, nft in nft_drops.head(num).iterrows():
            console.print(nft["Dates"] + " - " + nft["Title"])
            console.print(nft["Link"])
            console.print(nft["Description"])
            console.print("")

    export_data(
        export,
        os.path.dirname(os.path.abspath(__file__)),
        "upcoming",
        nft_drops,
    )


def display_nft_ongoing_drops(num: int, export: str):
    """Display NFT ongoing drops. [Source: nftcalendar.io]

    Parameters
    ----------
    num: int
        Number of NFT drops to display
    export : str
        Export dataframe data to csv,json,xlsx file
    """
    nft_drops = nftcalendar_model.get_nft_ongoing_drops()

    if nft_drops.empty:
        console.print("No data found.", "\n")
    else:
        for _, nft in nft_drops.head(num).iterrows():
            console.print(nft["Dates"] + " - " + nft["Title"])
            console.print(nft["Link"])
            console.print(nft["Description"])
            console.print("")

    export_data(
        export,
        os.path.dirname(os.path.abspath(__file__)),
        "ongoing",
        nft_drops,
    )


def display_nft_newest_drops(num: int, export: str):
    """Display NFT newest drops. [Source: nftcalendar.io]

    Parameters
    ----------
    num: int
        Number of NFT drops to display
    export : str
        Export dataframe data to csv,json,xlsx file
    """
    nft_drops = nftcalendar_model.get_nft_newest_drops()

    if nft_drops.empty:
        console.print("No data found.", "\n")
    else:
        for _, nft in nft_drops.head(num).iterrows():
            console.print(nft["Dates"] + " - " + nft["Title"])
            console.print(nft["Link"])
            console.print(nft["Description"])
            console.print("")

    export_data(
        export,
        os.path.dirname(os.path.abspath(__file__)),
        "newest",
        nft_drops,
    )
