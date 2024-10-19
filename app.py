from flask import Flask, render_template, redirect
import pandas as pd
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
coaches = os.path.join(basedir, 'static/coaches.csv')
all_players = os.path.join(basedir, 'static/player-roles.csv')

teams = ["ny", "bkn", "bos", "phi", "tor", "chi", "cle", "det", "ind", "mil",
         "den", "min", "okc", "por", "utah", "gs", "lac", "lal", "phx", "sac",
         "atl", "cha", "mia", "orl", "wsh", "dal", "hou", "mem", "no", "sa"]

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template("index.html")

@app.route('/team/<team>', methods=['GET', 'POST'])
def load_team(team):
    if team in teams:
        df = pd.read_csv(all_players)
        team_data = df.loc[df["Team"] == str(team).upper()]
        return render_template('team.html',  tables=[team_data.to_html(classes='data', header=True, index=False)])
    else:
        return redirect('/')

if __name__ == '__main__':  
   app.run()