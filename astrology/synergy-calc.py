import os
import pandas as pd
import numpy as np
from kerykeion import AstrologicalSubject, Report, RelationshipScore, KerykeionChartSVG

team_abbreviatons = {
    "SA" : "San Antonio Spurs", "NO" : "New Orleans Pelicans", "MEM" : "Memphis Grizzlies",
    "HOU" : "Houston Rockets", "DAL" : "Dallas Mavericks", "WSH" : "Washington Wizards",
    "ORL" : "Orlando Magic", "MIA" : "Miami Heat", "CHA" : "Charlotte Hornets",
    "ATL" : "Atlanta Hawks", "SAC" : "Sacramento Kings", "PHX" : "Phoenix Suns",
    "LAL" : "Los Angeles Lakers", "LAC" : "Los Angeles Clippers", "GS" : "Golden State Warriors",
    "UTAH" : "Utah Jazz", "POR" : "Portland Trailblazers", "OKC" : "Oklahoma City Thunder",
    "MIN" : "Minnesota Timberwolves", "DEN" : "Denver Nuggets", "MIL" : "Milwaukee Bucks",
    "IND" : "Indiana Pacers", "DET" : "Detroit Pistons", "CLE" : "Cleveland Cavaliers",
    "CHI" : "Chicago Bulls", "TOR" : "Toronto Raptors", "PHI" : "Philadelphia 76ers",
    "BOS" : "Boston Celtics", "BKN" : "Brooklyn Nets", "NY" : "New York Knicks"
}

df = pd.read_csv("../datascraper/data/all_players.csv", index_col=0)

# converts synergy score to letter grade string
def scoreToLetter(score):
    # 0 = F, 10 = , 19-21 = B, 28-30 = A, >30 = A+
    # on a 44 point scale...
    # 0-3 // F
    if score < 4:
        return "F"
    # 4-6 // D-
    elif score < 7:
        return "D-"
    # 7-8 // D
    elif score < 9:
        return "D"
    # 9-11 // D+
    elif score < 12:
        return "D+"
    # 12-14 // C-
    elif score < 15:
        return "C-"
    # 15-17 // C
    elif score < 18:
        return "C"
    # 18-19 // C+
    elif score < 20:
        return "C+"
    # 20-21 // B-
    elif score < 22:
        return "B-"
    # 22-23 // B
    elif score < 24:
        return "B"
    # 24-25 // B+
    elif score < 26:
        return "B+"
    # 26-28 // A-
    elif score < 29:
        return "A-"
    # 29-31 // A
    elif score < 32:
        return "A"
    # 32-37 // A+
    elif score < 38:
        return "A+"
    # 38+ // A+++
    else:
        return "A+++"

# return AstrologicalProfile object from player Series object
def getProfile(player, v=True):
    # Team, Name, Jersey, Pos, Ht, Wt, Sal, Age, Birthday (yyyy-mm-dd), Birth Loc
    if not isinstance(player, np.ndarray):
        print("Bad input formatting")
        return None
    if v:
        print(player)
    name = player[1]
    birth_year = int(player[8].split("-")[0])
    birth_month = int(player[8].split("-")[1])
    birth_day = int(player[8].split("-")[2])
    city = player[9].split(", ")[0]
    profile = AstrologicalSubject(name, birth_year, birth_month, birth_day, 0, 0, city, geonames_username="chenry22")
    return profile

# returns RelationshipScore object from two player Series objects
def getSynergy(player1, player2, chart=False, v=True):
    if not isinstance(player1, np.ndarray) or not isinstance(player2, np.ndarray):
        print("Bad input formatting")
        return None
    
    p1 = getProfile(player1, v=False)
    p2 = getProfile(player2, v=False)
    match = RelationshipScore(p1, p2)
    if v:
        print("*** Grade: " + scoreToLetter(match.score))
        print("*** Score: " + str(match.score))
        print("*** Relevant Aspects:")
        for aspect in match.relevant_aspects:
            print("   " + str(aspect))

    # Synastry Chart
    if chart: 
        # create directory if it doesn't already exist
        if not os.path.exists("saved_charts"):
            os.mkdir("saved_charts")
        synastry_chart = KerykeionChartSVG(p1, "Synastry", p2, new_output_directory="saved_charts")
        synastry_chart.makeSVG()

    return match

# input:
    # player: Series object with appropriate data
    # team: String of team abbreviation
# returns: list of synergy scores
def getPlayerTeamSynergy(player, team, v=True):
    # no team synergy of free agency group
    if team == "FA":
        print("*** Free Agents are not on a team.")
        return
    elif df[df["Team"] == team].values[0] is None:
        print("*** Team not found.")
        return

    # get list of all players on team
    players = df[df["Team"] == team]["Name"].tolist()
    # for every player, calculate synergy match score
    scores = []
    for teammate in players:
        # don't calculate synergy score with self
        if teammate == player[1]:
            scores.append(-1)
        else:
            scores.append(getSynergy(player, df[df["Name"] == teammate].values[0], v=False).score)

    if v:
        # get teammate scores sorted
        grades = list(map(scoreToLetter, scores))
        top_scores = sorted(zip(players, grades, scores), reverse=True, key=lambda x:x[2])
        print("\n*** Scores for " + player[1] + ":")
        for x in range(len(top_scores) - 1):
            print("   " + str(x + 1) + ". " + str(top_scores[x]))

        # calculate average disregarding -1
        for_avg = scores.copy()
        for_avg.remove(-1)
        avg_score = np.average(for_avg)
        print("\n*** Average Teammate Synergy Score: " + str(round(avg_score, 2)))
        print("*** Team Synergy Grade: " + scoreToLetter(avg_score) + "\n")
    return scores

# calculates average synergy of team and generates a report (csv)
    # returns list of average synergy scores of each player
def getTeamSynergy(team, v=True):
    # make all caps
    team = str(team).upper()
    if df[df["Team"] == team].values[0] is None:
        print("*** Team not found.")
        return
    
    # get list of all players on team
    team_scores = []
    players = df[df["Team"] == team]["Name"].tolist()
    for player in players:
        scores = getPlayerTeamSynergy(df.loc[df["Name"] == player].values[0], team, v=False)
        for_avg = scores.copy()
        for_avg.remove(-1)
        scores.insert(0, player)
        scores.append(round(sum(for_avg) / len(for_avg), 2))
        team_scores.append(scores)

    team_df = pd.DataFrame(team_scores)
    cols = players.copy()
    cols.insert(0, "Name")
    cols.append("Average")
    team_df.columns = cols

    # save output to csv file
    if not os.path.exists("tables"):
        os.mkdir("tables")
    team_df.to_csv("tables/" + team + ".csv")

    avg_scores = team_df["Average"].tolist()
    if v:
        grades = list(map(scoreToLetter, avg_scores))
        best_scores = sorted(zip(players, grades, avg_scores), reverse=True, key=lambda x : x[2])
        avg_score = round(np.average(avg_scores), 2)
        print("*** Scores for " + team_abbreviatons[team] + " [" + team + "] ***")
        print("   --- Saved to tables/" + team + ".csv")
        print("   --- Team Synergy Grade: " + scoreToLetter(avg_score))
        print("   --- Average Score: " + str(avg_score))
        for i in range(len(best_scores)):
            print("      " + str(i + 1) + ". " + str(best_scores[i]))
    return avg_scores

def getAllTeamsSynergy():
    league_scores = []
    for team in team_abbreviatons.keys():
        team_arr = [team]
        temp = getTeamSynergy(team, v=False) # returns list of individual scores
        team_arr.append(len(temp)) # num players
        team_arr.append(scoreToLetter(np.average(temp))) # avg grade
        team_arr.append(round(np.average(temp), 2)) # avg score
        team_arr.append(np.max(temp)) # max score
        team_arr.append(np.min(temp)) # min score
        team_arr.append(np.median(temp)) # median val
        league_scores.append(team_arr)
        print("   *** Completed [" + team + "]")

    league_df = pd.DataFrame(league_scores)
    cols = ["Team", "Players", "Grade", "Average", "Max", "Min", "Median"]
    league_df.columns = cols
    league_df.to_csv("tables/all_team_scores.csv")
    # print some ouput
    print("*** League Synergy ***")
    sorted_scores = sorted(zip(league_df["Team"].tolist(), league_df["Grade"].tolist(), league_df["Average"].tolist()), reverse=True, key=lambda x : x[2])
    for i in range(len(sorted_scores)):
        print("   " + str(i + 1) + ". " + str(sorted_scores[i]))

# function for basic use of program
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
            first = input("Match profile of:\n   ")
            while " " not in first or df.loc[df["Name"] == first].empty:
                print("Player not found...")
                first = input("Match profile of:\n   ")

            second = input("And:\n   ")
            while " " not in second or df.loc[df["Name"] == second].empty:
                print("Player not found...")
                second = input("And:\n   ")

            getSynergy(df.loc[df["Name"] == first].values[0], df.loc[df["Name"] == second].values[0])
            return
        case "2":
            player = input("Get team profile of player:\n   ")
            while " " not in player or df.loc[df["Name"] == player].empty:
                print("Player not found...")
                player = input("Get team profile of player:\n   ")

            player = df.loc[df["Name"] == player].values[0]
            getPlayerTeamSynergy(player, player[0])
        case "3":
            team = input("Get team profile of team:\n   ").upper()
            while df.loc[df["Team"] == team].empty:
                print("Team not found...")
                print("   --- Teams: " + str(team_abbreviatons.keys()))
                team = input("Get team profile of team:\n   ").upper()

            getTeamSynergy(team)
        case "4":
            getAllTeamsSynergy()
        case _:
            print("~Bad input. Failed to parse~")

# -- MAIN --
while True:
    print("== Enter '0' to load a player profile ==")
    print("== '1' to match two player profiles ==")
    print("== '2' to get the team synergy of a player ==")
    print("== '3' to get the synergy of a whole team ==")
    print("== '4' to generate a synergy report of all teams ==")
    print("== or 'x' to exit ==")
    choice = input("   ")
    if choice == "x":
        break
    parseInput(choice)