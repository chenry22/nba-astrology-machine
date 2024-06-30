import pandas as pd
import numpy as np
from kerykeion import AstrologicalSubject, Report, RelationshipScore, KerykeionChartSVG

df = pd.read_csv("rostered-players.csv", index_col=0)

def getProfile(player):
    # Team, Name, Jersey, Pos, Ht, Wt, Sal, Age, Birthday (yyyy-mm-dd), Birth Loc
    if not isinstance(player, np.ndarray):
        print("Bad input formatting")
        return None
    print(player)
    name = player[1]
    birth_year = int(player[8].split("-")[0])
    birth_month = int(player[8].split("-")[1])
    birth_day = int(player[8].split("-")[2])
    city = player[9].split(", ")[0]
    profile = AstrologicalSubject(name, birth_year, birth_month, birth_day, 0, 0, city, geonames_username="chenry22")
    return profile

def getSynergy(player1, player2):
    if not isinstance(player1, np.ndarray) or not isinstance(player2, np.ndarray):
        print("Bad input formatting")
        return None
    
    p1 = getProfile(player1)
    p2 = getProfile(player2)
    match = RelationshipScore(p1, p2)
    print("*** Score: " + str(match.score))
    print("*** Relevant Aspects: "+ str(match.relevant_aspects))

    # Synastry Chart
    synastry_chart = KerykeionChartSVG(p1, "Synastry", p2, new_output_directory="saved_charts")
    synastry_chart.makeSVG()

def parseInput(str_in):
    match str_in:
        case "0":
            name = input("Get profile of:\n")
            while " " not in name and df.loc[df["Name"] == name].empty:
                print("Player not found...")
                name = input("Get profile of:\n")

            ret = getProfile(df.loc[df["Name"] == name].values[0])
            if ret is not None:
                report = Report(ret)
                report.print_report()
            return
        case "1":
            first = input("Match profile of:\n")
            while " " not in first and df.loc[df["Name"] == first].empty:
                print("Player not found...")
                first = input("Match profile of:\n")

            second = input("And:\n")
            while " " not in second and df.loc[df["Name"] == second].empty:
                print("Player not found...")
                second = input("And:\n")

            getSynergy(df.loc[df["Name"] == first].values[0], df.loc[df["Name"] == second].values[0])
            return
        case _:
            print("~Bad input. Failed to parse~")

while True:
    print("== Enter '0' to load a player profile or '1' to match two player profiles ==")
    choice = input("")
    parseInput(choice)