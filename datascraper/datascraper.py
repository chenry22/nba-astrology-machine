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
            # link is first letter of last name / first 5 of last + first 2 of first + 01 (or other index maybe)
            player_link = str(lname)[:1] + "/" + str(lname.replace("'", ""))[:5] + str(fname.replace(".", "").replace("'", ""))[:2]
            if name == "KJ Martin":
                # for some reason they use Kenyon which messes all this up so I'm just manually casing for that
                player_link = "m/martike"
            # get player birth date and location (from bball ref)
            soup = BeautifulSoup(requests.get(birth_link + player_link + "01.html").content, "html.parser")

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
    df.to_csv("rostered-players.csv")
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
        player_link = str(lname)[:1] + "/" + str(lname)[:5] + str(fname.replace(".", "").replace("'", ""))[:2]
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

        # when team is completed, add to temp file
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
    df.to_csv("free-agents.csv")
    os.remove("temp.csv")

def refreshData():
    print("Loading player roster/birthday data")
    print("--- Getting all Current Roster data")
    if not os.path.isfile("rostered-players.csv"):
        getRosteredPlayers()
    else:
        # allow overwrite to update data
        print("   --- Found existing rostered player data file.")
        response = input("   --- Would you like to overwrite this? (y/n)")
        while response not in ["y", "n"]:
            response = input("   --- Would you like to overwrite this? (y/n)")

        if response == "y":
            getRosteredPlayers()

    print("--- Getting all Free Agent data")
    if not os.path.isfile("free-agents.csv"):
        getFreeAgents()
    else:
        # allow overwrite to update data
        print("   --- Found existing free agent data file.")
        response = input("   --- Would you like to overwrite this? (y/n)")
        while response not in ["y", "n"]:
            response = input("   --- Would you like to overwrite this? (y/n)")

        if response == "y":
            getFreeAgents()
    print("Completed!")

refreshData()