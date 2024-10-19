# -- NECESSARY LIBRARIES --
    # for web scraping
from bs4 import BeautifulSoup
import requests
import time
    # for string parsing
from unidecode import unidecode
    # for age calculations
from datetime import date
from datetime import datetime
    # for data management/storage
import pandas as pd
    # for user input
import sys
    # for checking if files exist
import os.path

# for age calculations
today = date.today()

# to get list of free agents
free_agent_list = "https://www.spotrac.com/nba/free-agents/_/year/2024"
# to get current rostered players
espn = "https://www.espn.com"
espn_team = "https://www.espn.com/nba/teams"
# to get birth dates and locations of players
birth_link = "https://www.basketball-reference.com/players/"
# to get coaching data
coach_link = "https://www.basketball-reference.com/coaches/"
coach_link_base = "https://www.basketball-reference.com/"
# to get rotation/starter-bench data
# NOTE: MAY BECOME OUTDATED/DEAD LINK AT SOME POINT
rotation_link = "https://hoopshype.com/lists/2022-23-depth-charts-an-early-look-at-team-rotations/"

# calculates age Int provided birthDate Date object
def calculateAge(birthDate):
    age = today.year - birthDate.year - ((today.month, today.day) < (birthDate.month, birthDate.day))
    return age

def getRosteredPlayers():
    if os.path.isfile("temp.csv"):
        data = pd.read_csv("temp.csv")
    else:
        data = []

    # create list of all team links
        # header necessary for proper connection to site
        # shoutout this post: https://stackoverflow.com/questions/77281333/espn-nba-web-scraping
    headers = { "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0" }
    soup = BeautifulSoup(requests.get(espn_team, headers=headers).content, "html.parser")
    team_link_list = []

    # page broken up into two columns of teams
    team_columns = soup.find("main").find("div", class_="page-container").find("div", class_="is-split").find_all("div", class_="layout__column")
    for column in team_columns:
        # each column broken up into divisions
        for division in column.find_all("div", class_="mt7"):
            # each division contains a list of teams
            teams = division.find("div", class_="ContentList").find_all("div", class_="ContentList__Item")
            for team in teams:
                team_link = team.find("div", class_="TeamLinks__Links").find_all("span")[2].find("a", href=True)['href']
                team_link_list.append(team_link)

    # keep track of current player data
    if os.path.exists("data/player-data.csv"):
        player_df = pd.read_csv("data/player-data.csv")

    # go to each link and get list of players
    for team_link in team_link_list:
        print("   --- Team: " + team_link)
        team_abbrv = str(team_link).split("/")[6].upper()
        soup = BeautifulSoup(requests.get(espn + team_link, headers=headers).content, "html.parser")
        roster = soup.find("main").find("div", class_="page-container").find("tbody", class_="Table__TBODY").find_all("tr", class_="Table__TR")
        for player in roster:
            player_arr = []
            player_arr.append(team_abbrv)

            player_data = player.find_all("td", class_="Table__TD")
            name = player_data[1].find("a").text

            if isinstance(data, pd.DataFrame) and not data.loc[data['Name'] == name].empty:
                # print("      --- Found " + str(data.loc[data['Name'] == name]["Name"].item()))
                continue

            player_arr.append(name)
            player_arr.append(player.find("span", class_="pl2").text if player.find("span", class_="pl2") is not None else "--") # jersey number
            player_arr.append(player_data[2].find("div").text) # position
            player_arr.append(player_data[4].find("div").text) # height (ft)
            player_arr.append(player_data[5].find("div").text.split(" ")[0]) # weight (lbs)
            player_arr.append(player_data[7].find("div").text) # salary

            # for last names with spaces in them
            names = str(name).lower().split(" ")
            fname = names[0]
            lname = names[1]
            if len(names) > 2:
                lname += names[2]

            # if we already have this data stored, 
            if player_df is not None and not player_df[player_df["Name"] == name].empty: 
                # use data stored to make entry
                entry = player_df.loc[player_df["Name"] == name].iloc[0]
                player_arr.append(entry["Age"])
                player_arr.append(entry["Birth Date"])
                player_arr.append(entry["Birth Location"])
                if not isinstance(data, pd.DataFrame):
                    data.append(player_arr)
                else:
                    data = pd.concat([pd.DataFrame([player_arr], columns=data.columns), data], ignore_index=True)

                continue

            # link is first letter of last name / first 5 of last + first 2 of first + 01 (or other index maybe)
            player_link = str(lname)[:1] + "/" + str(lname.replace("'", "").replace("-", ""))[:5] + str(fname.replace(".", "").replace("'", ""))[:2]
            
            # fixing random discrepancies
            if name == "KJ Martin":
                # for some reason they use Kenyon which messes all this up so I'm just manually casing for that
                player_link = "m/martike"
            elif name == "Sasha Vezenkov":
                # they use aleks (his real name) instead of sasha for the link
                player_link = "v/vezenal"
            elif name == "Taylor Hendricks":
                # they just randomly used 6 letters in the last name for this one idek
                player_link = "h/hendrita"
            elif name == "Bub Carrington":
                # this will probably get fixed at some point
                name = "Carlton Carrington"
                player_link = "c/carrica"
            elif name == "Clint Capela":
                # this is just plain wrong tbh
                player_link = "c/capelca"
            elif name == "Maxi Kleber":
                # this is also just wrong...
                player_link = "k/klebima"
            elif name == "Cedi Osman":
                # also WRONG!!!!
                player_link = "o/osmande"
            elif name == "David Duke Jr.":
                # randomly 4 length last name
                player_link = "d/dukeda"
            elif name == "Jarod Lucas":
                # this guy is not important
                player_link = ""

            # get player birth date and location (from bball ref)
            soup = BeautifulSoup(requests.get(birth_link + player_link + "01.html").content, "html.parser")

            # this one actually kind of makes sense but they should be 01 and not 02
            if name == "Bronny James" or name == "Devin Carter":
                soup = BeautifulSoup(requests.get(birth_link + player_link + "02.html").content, "html.parser")

            # DONT CONTINUE IF PLAYER IS NOT BBALL REF'D
            if soup.find("div", id="meta") is None:
                print("      --- " + player_arr[1] + " not listed on bball ref!")
                continue

            # have to check correct player because some players have duplicate ids (smh)
                # eg. Mikal Bridges and Miles Bridges are both m/bridgmi
                # unidecode since ESPN holds unicode, but Bball Ref holds accented names
                    # eg. "Luka Doncic" vs "Luka Dončić" should be considered equal
            name_check = str(unidecode(soup.find("div", id="meta").find("h1").find("span").get_text())).replace(".", "").replace("'", "").strip()
            name = str(name).replace(".", "").replace("'", "").strip()
            # one website shortens and the other doesn't so...
            if fname == "cameron":
                alt_name = name.split(" ")[0][:3].capitalize() + " " + lname.capitalize()
            elif fname == "osasere":
                alt_name = "Oso Ighodaro"
            else:
                alt_name = ""
            i = 2
            while name.lower() != name_check.lower() and name != name_check[:-4] and name[:-4] != name_check and name != name_check[:-3] and name[:-3] != name_check and alt_name != name_check:
                print("         --- " + str(name) + " != " + str(name_check) + " /// i = " + str(i))
                # keep checking indexes until match is found (need delay since requesting new pages)
                time.sleep(3)
                if i < 10:
                    soup = BeautifulSoup(requests.get(birth_link + player_link + "0" + str(i) + ".html").content, "html.parser")
                else:
                    soup = BeautifulSoup(requests.get(birth_link + player_link + str(i) + ".html").content, "html.parser")

                if soup.find("div", id="meta") is not None:
                    name_check = str(unidecode(soup.find("div", id="meta").find("h1").find("span").text)).replace(".", "").replace("'", "").strip()
                i += 1

                if i > 20:
                    print("Stuck in loop")
                    break

            birth = soup.find("div", id="meta").find("span", id="necro-birth")
            birthday = birth["data-birth"]
            player_arr.append(calculateAge(datetime.strptime(birthday, "%Y-%m-%d").date()))
            player_arr.append(birthday) # birthday
            if birth.find_next_sibling("span") is not None and "in" in birth.find_next_sibling("span").text:
                player_arr.append(unidecode(birth.find_next_sibling("span").text).split("in ")[1]) # birth location
            else: 
                player_arr.append("--")
            print("      --- Player: " + player_arr[1])

            if not isinstance(data, pd.DataFrame):
                data.append(player_arr)
            else:
                data = pd.concat([pd.DataFrame([player_arr], columns=data.columns), data], ignore_index=True)

            # add delay to comply w/ bball ref scraping rules (>20 requests per min)
            time.sleep(3)

        # when team is completed, add to temp file
        print("   --- Saving to temporary file")
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data)
            cols = ["Team", "Name", "Jersey", "Position", "Height (ft)", "Weight (lb)", "Salary", "Age", "Birth Date", "Birth Location"]
            df.columns = cols
            df.to_csv("temp.csv", index=False)
        else:
            data.to_csv("temp.csv", index=False)

    # compile data in CSV file (with current team shown)
    df = pd.DataFrame(data)
    cols = ["Team", "Name", "Jersey", "Position", "Height (ft)", "Weight (lb)", "Salary", "Age", "Birth Date", "Birth Location"]
    df.columns = cols
    if not os.path.exists("data"):
        os.mkdir("data")
    df.to_csv("data/rostered-players.csv")

    os.remove("temp.csv")

def getFreeAgents():
    if os.path.isfile("temp.csv"):
        data = pd.read_csv("temp.csv")
    else:
        data = []

    # get list of players
    headers = { "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0" }
    soup = BeautifulSoup(requests.get(free_agent_list, headers=headers).content, "html.parser")

    fa_list = soup.find_all("table")[1].find("tbody").find_all("tr")

    if os.path.exists("data/player-data.csv"):
        player_df = pd.read_csv("data/player-data.csv")

    for player in fa_list:
        # table breaks
        if "ad" in player["class"]:
            continue

        player_arr = []
        player_data = player.find_all("td")

        player_arr.append("FA") # team (free agent)
        name = player_data[0].find("a").text

        # random shortenings...
        if name == "Mohamed Bamba":
            name = "Mo Bamba"
        elif name == "Sviatoslav Mykhailiuk":
            name = "Svi Mykhailiuk"
        elif name == "Ishmail Wainright":
            name = "Ish Wainright"

        if isinstance(data, pd.DataFrame) and not data.loc[data['Name'] == name].empty:
            print("      --- Found " + str(data.loc[data['Name'] == name]["Name"].item()))
            continue

        player_arr.append(name)
        player_arr.append("--") # jersey none
        player_arr.append(player_data[1].text) # position

        # now we get our data from bball ref
        names = str(name).lower().split(" ")
        # for last names with spaces in them
        names = str(name).lower().split(" ")
        fname = names[0]
        lname = names[1]
        if len(names) > 2:
            lname += names[2]

        # if we already have this data, don't re-request it
        if player_df is not None and not player_df.loc[player_df["Name"] == name].empty:
            entry = player_df.loc[player_df["Name"] == name].iloc[0]
            player_arr.append(entry["Height (ft)"])
            player_arr.append(entry["Weight (lb)"])
            player_arr.append("--")
            player_arr.append(entry["Age"])
            player_arr.append(entry["Birth Date"])
            player_arr.append(entry["Birth Location"])

            if not isinstance(data, pd.DataFrame):
                data.append(player_arr)
                df = pd.DataFrame(data)
                cols = ["Team", "Name", "Jersey", "Position", "Height (ft)", "Weight (lb)", "Salary", "Age", "Birth Date", "Birth Location"]
                df.columns = cols
                df.to_csv("temp.csv", index=False)
            else:
                data = pd.concat([pd.DataFrame([player_arr], columns=data.columns), data], ignore_index=True)
                data.to_csv("temp.csv", index=False)

            continue

        player_link = str(lname)[:1] + "/" + str(lname)[:5] + str(fname.replace(".", "").replace("'", ""))[:2]
        
        # fixing random discrepancies
        if name == "Cedi Osman":
            # WRONG!!!!
            player_link = "o/osmande"
        elif name == "David Duke Jr.":
            # randomly 4 length last name
            player_link = "d/dukeda"

        soup = BeautifulSoup(requests.get(birth_link + player_link + "01.html").content, "html.parser")

        # DONT CONTINUE IF PLAYER IS NOT BBALL REF'D
        if soup.find("div", id="meta") is None:
            print("   --- " + player_arr[1] + " not listed on bball ref!")
            continue

        # still have to check duplicate ids
        name_check = str(unidecode(soup.find("div", id="meta").find("h1").find("span").get_text())).replace(".", "").replace("'", "").strip()
        name = str(name).replace(".", "").replace("'", "").strip()
        i = 2
        # also accounting for "jr."s and "sr."s which are arbitrarily included/left off
        while name != name_check and name != name_check[:-4] and name[:-4] != name_check and name != name_check[:-3] and name[:-3] != name_check:
            print("         --- " + str(name) + " != " + str(name_check) + " /// i = " + str(i))
            # keep checking indexes until match is found (need delay since requesting new pages)
            time.sleep(3)
            if i < 10:
                soup = BeautifulSoup(requests.get(birth_link + player_link + "0" + str(i) + ".html").content, "html.parser")
            else:
                soup = BeautifulSoup(requests.get(birth_link + player_link + str(i) + ".html").content, "html.parser")

            if soup.find("div", id="meta") is not None:
                name_check = str(unidecode(soup.find("div", id="meta").find("h1").find("span").text)).replace(".", "").replace("'", "").strip()
            i += 1

            if i > 20:
                print("Stuck in loop")
                break

        meta = soup.find("div", id="meta").text.split("Shoots")[1].split("Team")[0]
        player_arr.append(meta.split("-")[0][-1:] + "' " + meta.split("-")[1].split(",")[0] + "\"") # height
        player_arr.append(meta.split("lb")[0][-3:]) # weight

        player_arr.append("--") # salary
        player_arr.append(str(player_data[2].text).split(".")[0]) # age

        birth = soup.find("div", id="meta").find("span", id="necro-birth")
        birthday = birth["data-birth"]
        player_arr.append(birthday) # birthday
        if birth.find_next_sibling("span") is not None and "in" in birth.find_next_sibling("span").text:
            player_arr.append(unidecode(birth.find_next_sibling("span").text).split("in ")[1]) # birth location
        else: 
            player_arr.append("--")

        if not isinstance(data, pd.DataFrame):
            data.append(player_arr)
            df = pd.DataFrame(data)
            cols = ["Team", "Name", "Jersey", "Position", "Height (ft)", "Weight (lb)", "Salary", "Age", "Birth Date", "Birth Location"]
            df.columns = cols
            df.to_csv("temp.csv", index=False)
        else:
            data = pd.concat([pd.DataFrame([player_arr], columns=data.columns), data], ignore_index=True)
            data.to_csv("temp.csv", index=False)
        print("      --- Player: " + player_arr[1])

        # add delay to comply w/ bball ref scraping rules (>20 requests per min)
        time.sleep(3)

    # compile data in CSV file (with free agent status shown)
    df = pd.DataFrame(data)
    cols = ["Team", "Name", "Jersey", "Position", "Height (ft)", "Weight (lb)", "Salary", "Age", "Birth Date", "Birth Location"]

    df.columns = cols
    if not os.path.exists("data"):
        os.mkdir("data")
    df.to_csv("data/free-agents.csv")
    os.remove("temp.csv")

def getCoaches():
    headers = { "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0" }
    soup = BeautifulSoup(requests.get(coach_link, headers=headers).content, "html.parser")

    # get full table
    rows = soup.find("table", id="coaches").find("tbody").find_all("tr")
    data = []
    for row in rows:
        coach = []
        # only get data for modern coaches
        test = row.find("td", {"data-stat": "season_max"})
        if test is not None and int(test.text) >= 2023:
            coach.append("FA") # team (will fill in manually ig)
            coach.append(row.find("th").find("a").text) # name
            print("   --- " + coach[1])

            new_link = row.find("th").find("a", href=True)["href"]
            soup = BeautifulSoup(requests.get(coach_link_base + new_link, headers=headers).content, "html.parser")
            if soup.find("span", id="necro-birth") is None:
                print("   --- Cannot find coach page...")
                continue
            
            birth = soup.find("span", id="necro-birth").find_parent()
            birthday = birth.find("span", id="necro-birth")["data-birth"]
            coach.append(calculateAge(datetime.strptime(birthday, "%Y-%m-%d").date())) # age
            coach.append(birthday)
            coach.append(str(birth.text).split("in ")[1]) # place of birth

            data.append(coach)
            time.sleep(3)

    df = pd.DataFrame(data)
    print(df)
    cols = ["Team", "Name", "Age", "Birth Date", "Birth Location"]

    df.columns = cols
    if not os.path.exists("data"):
        os.mkdir("data")
    df.to_csv("data/coaches.csv")

def combinePlayerData():
    if not os.path.exists("data"):
        os.mkdir("data")
    rostered_df = pd.read_csv("data/rostered-players.csv", index_col=0)
    fa_df = pd.read_csv("data/free-agents.csv", index_col=0)

    free_agents = fa_df["Name"].tolist()
    players = rostered_df[~rostered_df["Name"].isin(free_agents)]
    players = pd.concat([players, fa_df])
    players.to_csv("data/all_players.csv")

    df = players[["Name", "Height (ft)", "Weight (lb)", "Age", "Birth Date", "Birth Location"]]
    df.to_csv("data/player-data.csv")

def getRotations():
    # check that roster data exists first
    if not os.path.isfile("data/rostered-players.csv"):
        print("   --- Could not find rostered player data, aborting process")
        return
    
    # first create dataframe holding whether player is starting or bench
        # neither means deeper in rotation
    headers = { "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0" }
    soup = BeautifulSoup(requests.get(rotation_link, headers=headers).content, "html.parser")
    rotation = pd.read_csv("data/all_players.csv", index_col=0)
    rotation["Role"] = "--"

    team_abbrvs = ["ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GS", 
                   "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NO", "NY", 
                   "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SA", "TOR", "UTAH", "WSH"]

    # get array of all teams' projected rotations
    teams = soup.find("div", id="listicle-0").parent.find_all("div", class_="listicle")
    i = 0
    for team in teams:
        team_name = str(team.find("h3", class_="listicle-header").text).strip()
        print("   --- " + team_name)
        team_link = team.find("iframe")["src"]
        soup = BeautifulSoup(requests.get(team_link, headers=headers).content, "html.parser")
        rows = soup.find("table", class_="waffle").find("tbody").find_all("tr")
        lnames = rotation["Name"].str.split(" ").str[1]

        # third row is name of starters
        for name in rows[2].find_all("td"):
            # search for player in roster_df and mark if found
            txt = str(name.text)
            search = [txt, txt + " Jr.", txt + " II"] # might have something at end too

            # there is a defined order of teams, so search by last name in team
            if not rotation.loc[(rotation["Team"] == team_abbrvs[i]) & (rotation["Name"].isin(search))].empty:
                rotation.loc[(rotation["Team"] == team_abbrvs[i]) & (rotation["Name"].isin(search)), "Role"] = "Starter"
            elif not rotation.loc[(rotation["Team"] == team_abbrvs[i]) & (lnames == txt.split(" ")[1])].empty:
                rotation.loc[(rotation["Team"] == team_abbrvs[i]) & (lnames == txt.split(" ")[1]), "Role"] = "Starter" 
            else:
                print("      --- Could not find player " + name.text + " in df [starter]")

        # sixth row is name of bench guys
        for name in rows[5].find_all("td"):
            # search for player in roster_df and mark if found
            txt = str(name.text)
            search = [txt, txt + " Jr.", txt + " II"] # might have something at end too

            if not rotation.loc[(rotation["Team"] == team_abbrvs[i]) & (rotation["Name"].isin(search))].empty:
                rotation.loc[(rotation["Team"] == team_abbrvs[i]) & (rotation["Name"].isin(search)), "Role"] = "Bench"
            elif not rotation.loc[(rotation["Team"] == team_abbrvs[i]) & (lnames == txt.split(" ")[1])].empty:
                rotation.loc[(rotation["Team"] == team_abbrvs[i]) & (lnames == txt.split(" ")[1]), "Role"] = "Bench"
            else:
                print("      --- Could not find player " + name.text + " in df [bench]")

        i += 1
    
    # save data
    rotation.to_csv("data/player-roles.csv")

# main function that allows users to scrape new data
def refreshData():
    print("Loading player roster/birthday data")
    print("--- Getting all Current Roster data")
    if not os.path.isfile("data/rostered-players.csv"):
        getRosteredPlayers()
    else:
        # allow overwrite to update data
        print("   --- Found existing rostered player data file.")
        response = input("   --- Would you like to overwrite this? (y/n)\n   ")
        while response not in ["y", "n"]:
            response = input("   --- Would you like to overwrite this? (y/n)\n   ")

        if response == "y":
            getRosteredPlayers()

    print("--- Getting all Free Agent data")
    if not os.path.isfile("data/free-agents.csv"):
        getFreeAgents()
    else:
        # allow overwrite to update data
        print("   --- Found existing free agent data file.")
        response = input("   --- Would you like to overwrite this? (y/n)\n   ")
        while response not in ["y", "n"]:
            response = input("   --- Would you like to overwrite this? (y/n)\n   ")

        if response == "y":
            getFreeAgents()

    print("--- Getting coach data")
    if not os.path.isfile("data/coaches.csv"):
        getCoaches()
    else:
        # allow overwrite to update data
        print("   --- Found existing coach data file.")
        response = input("   --- Would you like to overwrite this? (y/n)\n   ")
        while response not in ["y", "n"]:
            response = input("   --- Would you like to overwrite this? (y/n)\n   ")

        if response == "y":
            getCoaches()

    choice = input("--- Would you like to combine the free agent and rostered player data? [y/n]\n   ")
    while choice not in ["y", "n"]:
        choice = input("--- Would you like to combine the free agent and rostered player data? [y/n]\n   ")
    if choice == "y":
        combinePlayerData()

        if not os.path.isfile("data/player-roles.csv"):
            getRotations()
        else:
            # allow overwrite to update data
            print("   --- Found existing rotation data file.")
            response = input("   --- Would you like to overwrite this? (y/n)\n   ")
            while response not in ["y", "n"]:
                response = input("   --- Would you like to overwrite this? (y/n)\n   ")
            if response == "y":
                getRotations()

    print("Completed!")


print("Refresh player data? (yes or no)")
if input("   ") == "yes":
    refreshData()

print("Refresh rotation data? (yes or no)")
if input("   ") == "yes":
    getRotations()