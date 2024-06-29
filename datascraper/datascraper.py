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

data = []

def calculateAge(birthDate):
    age = today.year - birthDate.year - ((today.month, today.day) < (birthDate.month, birthDate.day))
    return age

def getRosteredPlayers():
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
            player_arr.append(name)
            player_arr.append(player.find("span", class_="pl2").text if player.find("span", class_="pl2") is not None else "--") # jersey number
            player_arr.append(player_data[2].find("div").text) # position
            player_arr.append(player_data[4].find("div").text) # height (ft)
            player_arr.append(player_data[5].find("div").text.split(" ")[0]) # weight (lbs)
            player_arr.append(player_data[7].find("div").text) # salary

            names = str(name).lower().split(" ")
            # link is first letter of last name / first 5 of last + first 2 of first + 01 (or other index maybe)
            player_link = str(names[1])[:1] + "/" + str(names[1])[:5] + str(names[0])[:2]
            # get player birth date and location (from bball ref)
            soup = BeautifulSoup(requests.get(birth_link + player_link + "01.html").content, "html.parser")

            # have to check correct player because some players have duplicate ids (smh)
                # eg. Mikal Bridges and Miles Bridges are both m/bridgmi
                # unidecode since ESPN holds unicode, but Bball Ref holds accented names
                    # eg. "Luka Doncic" vs "Luka Dončić" should be considered equal
            name_check = unidecode(soup.find("div", id="meta").find("h1").find("span").get_text())
            i = 2
            while str(name) != str(name_check):
                print("         --- " + str(name) + " != " + str(name_check) + " /// Checking i = " + str(i))
                # keep checking indexes until match is found (need delay since requesting new pages)
                time.sleep(3)
                soup = BeautifulSoup(requests.get(birth_link + player_link + "0" + str(i) + ".html").content, "html.parser")
                name_check = unidecode(soup.find("div", id="meta").find("h1").find("span").get_text())
                i += 1
                # technically should check that i < 10, but I don't think there's any
                # group of 10 NBA players who this would apply to...
            
            birth = soup.find("div", id="meta").find("span", id="necro-birth")
            birthday = birth["data-birth"]
            player_arr.append(calculateAge(datetime.strptime(birthday, "%Y-%m-%d").date()))
            player_arr.append(birthday) # birthday
            player_arr.append(unidecode(birth.find_next_sibling("span").text).split("in ")[1]) # birth location
            print("      --- Player: " + player_arr[1])
            data.append(player_arr)

            # add delay to comply w/ bball ref scraping rules (>20 requests per min)
            time.sleep(3)

    # compile data in CSV file (with current team shown)
    df = pd.DataFrame(data)
    cols = ["Team", "Name", "Jersey", "Position", "Height (ft)", "Weight (lb)", "Salary", "Age", "Birth Date", "Birth Location"]

    df.columns = cols
    df.to_csv("rostered-players.csv")

def getFreeAgents():
    # get list of players
    headers = { "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0" }
    soup = BeautifulSoup(requests.get(free_agent_list, headers=headers).content, "html.parser")
    data = []

    fa_list = soup.find_all("table")[1].find("tbody").find_all("tr")
    for player in fa_list:
        player_arr = []
        player_data = player.find_all("td")

        player_arr.append("FA") # team (free agent)
        name = player_data[0].find("a").text
        player_arr.append(name)
        player_arr.append("--") # jersey none
        player_arr.append(player_data[1].text) # position

        # now we get our data from bball ref
        names = str(name).lower().split(" ")
        player_link = str(names[1])[:1] + "/" + str(names[1])[:5] + str(names[0])[:2]
        soup = BeautifulSoup(requests.get(birth_link + player_link + "01.html").content, "html.parser")

        # still have to check duplicate ids
        name_check = unidecode(soup.find("div", id="meta").find("h1").find("span").get_text())
        i = 2
        while str(name) != str(name_check):
            print("         --- " + str(name) + " != " + str(name_check) + " /// Checking i = " + str(i))
            # keep checking indexes until match is found (need delay since requesting new pages)
            time.sleep(3)
            soup = BeautifulSoup(requests.get(birth_link + player_link + "0" + str(i) + ".html").content, "html.parser")
            name_check = unidecode(soup.find("div", id="meta").find("h1").find("span").get_text())
            i += 1
            # technically should check that i < 10

        meta = soup.find("div", id="meta").text.split("Shoots")[1].split("Team")[0]
        player_arr.append(meta.split(",")[0][-3:].replace("-", "' ") + "\"") # height
        player_arr.append(meta.split("lb")[0][-3:]) # weight

        player_arr.append("--") # salary
        player_arr.append(str(player_data[2].text).split(".")[0]) # age

        birth = soup.find("div", id="meta").find("span", id="necro-birth")
        birthday = birth["data-birth"]
        player_arr.append(calculateAge(datetime.strptime(birthday, "%Y-%m-%d").date()))
        player_arr.append(birthday) # birthday
        player_arr.append(unidecode(birth.find_next_sibling("span").text).split("in ")[1]) # birth location
        print("      --- Player: " + player_arr[1])
        data.append(player_arr)

        # add delay to comply w/ bball ref scraping rules (>20 requests per min)
        time.sleep(3)

    # compile data in CSV file (with free agent status shown)
    df = pd.DataFrame(data)
    cols = ["Team", "Name", "Jersey", "Position", "Height (ft)", "Weight (lb)", "Salary", "Age", "Birth Date", "Birth Location"]

    df.columns = cols
    df.to_csv("free-agents.csv")

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