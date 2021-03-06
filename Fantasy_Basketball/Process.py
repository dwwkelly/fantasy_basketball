#  Copyright (C) 2014 Devin Kelly
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import sys
import numpy as np
from bs4 import BeautifulSoup
import pandas as pd

from Dataframe_Augmenter import augment_minutes
from Dataframe_Augmenter import augment_price
from Dataframe_Augmenter import augment_value
from Dataframe_Augmenter import augment_draft_data
from Dataframe_Augmenter import augment_fantasy_teams
from Util import mkdir_p
from TeamData import teams


def get_player_stats(data_dir, year):
    d = os.path.join(data_dir, 'raw_data', 'teams', str(year))
    pkl = os.path.join(data_dir, 'processed_data', str(year))
    draft_dir = os.path.join(data_dir, 'raw_data', 'draft')

    df = get_players(d, year)
    if os.path.isdir(draft_dir):
        draft_df = get_draft(draft_dir)
        df = augment_draft_data(df, draft_df)

    df = augment_fantasy_teams(df, data_dir)
    df = augment_minutes(df)
    df = augment_value(df)
    df = augment_price(df)

    mkdir_p(pkl)
    pkl = os.path.join(pkl, 'team_data.pkl')
    df.to_pickle(pkl)


def get_dataframe(filename, table_id):
    if not os.path.isfile(filename):
        print "Cannot open file, try downloading data\n{0}".format(filename)
        sys.exit(1)

    with open(filename, 'r') as fd:
        soup = BeautifulSoup(fd.read())

    try:
        table = soup.find('table', {'id': table_id})
        body = table.find('tbody')
        rows = body.find_all('tr', {'class': ''})
    except AttributeError:
        print "Parsing {0} failed".format(filename)
        return pd.DataFrame()

    rows = [str(r.encode('utf-8')) for r in rows if r['class'] == ['']]

    html = '<table>' + ''.join(rows) + '</table>'

    df = pd.io.html.read_html(html, infer_types=False)[0]

    return df


def get_draft(data_dir):

    df = pd.DataFrame()
    cols = ['Rk', 'Pk', 'Tm', 'Player', 'College', 'G', 'MP', 'PTS', 'TRB',
            'AST', 'FG%', '3P%', 'FT%', 'MP_PG', 'PTS_PG', 'TRB_PG',
            'AST_PG', 'WS', 'WS/48']
    delete_cols = ['Rk', 'Tm', 'College', 'G', 'MP', 'PTS', 'TRB', 'AST',
                   'FG%', '3P%', 'FT%', 'MP_PG', 'PTS_PG', 'TRB_PG', 'AST_PG',
                   'WS', 'WS/48']

    for root, _, _ in os.walk(data_dir, topdown=False):
        try:
            year = re.search(r'[0-9]{4}', root).group(0)
        except AttributeError:
            continue
        d = os.path.join(data_dir, root, 'draft.html')
        tmp = get_dataframe(d, 'stats')
        tmp.columns = cols
        tmp['draft_team'] = tmp['Tm']
        for dc in delete_cols:
            del tmp[dc]
        tmp['draft_year'] = int(year)
        tmp['Pk'] = tmp['Pk'].astype(int)
        df = df.append(tmp)

    return df


def get_advanced(data_dir, year):

    df = pd.DataFrame()

    cols_24 = ['Rk', 'Player', 'Age', 'G', 'MP', 'PER', 'TS%', 'eFG%', 'FTr',
               '3PAr', 'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%',
               'USG%', 'ORtg', 'DRtg', 'OWS', 'DWS', 'WS', 'WS/48']
    types = [int, unicode, int, int, int, float, float, float, float, float,
             float, float, float, float, float, float, float, float, float,
             float, float, float, float, float]
    cols_24_types = dict(zip(cols_24, types))

    cols_25 = ['Rk', 'Player', 'Age', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr',
               'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%',
               'OWS', 'DWS', 'WS', 'WS/48', 'OBPM', 'DBPM', 'BPM', 'VORP']
    types = [int, unicode, int, int, int, float, float, float, float, float,
             float, float, float, float, float, float, float, float, float,
             float, float, float, float, float, float]
    cols_25_types = dict(zip(cols_25, types))

    for t in teams[int(year)]:
        filename = os.path.join(data_dir, "{0}.html".format(t))
        if os.path.isfile(filename):
            tmp = get_dataframe(filename, 'advanced')
            tmp.dropna(axis=1, inplace=True, how='all')
            tmp.fillna(0)
            if tmp.shape[1] == 24:
                tmp.columns = cols_24
                for k in cols_24_types:
                    tmp[k] = tmp[k].astype(cols_24_types[k])
            else:
                tmp.columns = cols_25
                for k in cols_25_types:
                    tmp[k] = tmp[k].astype(cols_25_types[k])
            tmp['year'] = int(year)
            df = df.append(tmp)

    del df['Rk']
    del df['Age']
    del df['G']

    return df


def get_pergame(data_dir, year):

    df = pd.DataFrame()

    cols = ['ind', 'Player', 'Age', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P',
            '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB',
            'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']

    for t in teams[int(year)]:
        filename = os.path.join(data_dir, "{0}.html".format(t))
        if os.path.isfile(filename):
            tmp = get_dataframe(filename, 'per_game')
            tmp.columns = cols
            tmp['year'] = int(year)
            df = df.append(tmp)

    del df['MP']
    df['Age'] = df['Age'].astype(int)
    df['G'] = df['G'].astype(int)
    df['GS'] = df['GS'].astype(int)
    df['FG'] = df['FG'].astype(float)
    df['FGA'] = df['FGA'].astype(float)
    df['FG%'] = df['FG%'].astype(float)
    df['3P'] = df['3P'].astype(float)
    df['3PA'] = df['3PA'].astype(float)
    df['3P%'] = df['3P%'].astype(float)
    df['2P'] = df['2P'].astype(float)
    df['2PA'] = df['2PA'].astype(float)
    df['2P%'] = df['2P%'].astype(float)
    df['FT'] = df['FT'].astype(float)
    df['FTA'] = df['FTA'].astype(float)
    df['FT%'] = df['FT%'].astype(float)
    df['ORB'] = df['ORB'].astype(float)
    df['DRB'] = df['DRB'].astype(float)
    df['TRB'] = df['TRB'].astype(float)
    df['AST'] = df['AST'].astype(float)
    df['STL'] = df['STL'].astype(float)
    df['BLK'] = df['BLK'].astype(float)
    df['TOV'] = df['TOV'].astype(float)
    df['PF'] = df['PF'].astype(float)
    df['PTS'] = df['PTS'].astype(float)

    del df['ind']

    set_types = {'Age': int, 'G': int, 'GS': int, 'FG': float, 'FGA': float,
                 'FG%': float, '3P': float, '3PA': float, '3P%': float,
                 '2P': float, '2PA': float, '2P%': float, 'FT': float,
                 'FTA': float, 'FT%': float, 'ORB': float, 'DRB': float,
                 'TRB': float, 'AST': float, 'STL': float, 'BLK': float,
                 'TOV': float, 'PF': float, 'PTS': float}

    for ii in set_types:
        df[ii] = df[ii].astype(set_types[ii])
        df[ii].fillna(0, inplace=True)

    return df


def get_salaries(data_dir, year):
    df = pd.DataFrame()

    cols = ['ind', 'Player', 'Salary']

    for t in teams[int(year)]:
        filename = os.path.join(data_dir, "{0}.html".format(t))
        if os.path.isfile(filename):
            tmp = get_dataframe(filename, 'salaries')
            tmp.columns = cols
            tmp['year'] = int(year)
            df = df.append(tmp, ignore_index=True)

    df['Salary'] = df['Salary'].str.replace(r'[$,]', '').astype('float')
    df['Salary'] = df['Salary'] / 1e6
    df['Salary'] = np.round(df['Salary'], 3)
    del df['ind']

    return df


def get_roster(data_dir, year):
    df = pd.DataFrame()

    cols = ['No.', 'Player', 'Pos', 'Ht', 'Wt',
            'Birth Date', 'Experience', 'College']

    none_opened = True
    for t in teams[int(year)]:
        filename = os.path.join(data_dir, "{0}.html".format(t))
        if os.path.isfile(filename):
            tmp = get_dataframe(filename, 'roster')
            tmp.columns = cols
            tmp['year'] = year
            df = df.append(tmp)
            none_opened = False

    if none_opened:
        print "Could not find raw data in {0}".format(data_dir)
        sys.exit(1)

    del df['No.']

    # replace positions so that only C-PF-SF-SG-PG exist
    replacement = {"Pos": {'PF-SF': 'PF', 'PG-SG': 'PG',
                           'SF-PF': 'SF', 'SF-SG': 'SF', '^G$': 'SG',
                           'G-F': 'SG', 'F': 'PF', 'G-PF': 'SG', 'G': 'SG'}}
    df.replace(to_replace=replacement, inplace=True)

    # set height to be in inches for all players
    def heigh_to_inches(s):
        if type(s) != type(str):  # FIXME this is dumb
            return 0
        t = s.split('-')
        return int(t[0]) * 12 + int(t[1])

    df['Experience'].replace('R', 0, inplace=True)
    df['Ht'] = df['Ht'].apply(heigh_to_inches)

    df['Wt'].fillna(0, inplace=True)
    df['Wt'] = df['Wt'].astype(int)

    return df


def get_players(data_dir, year):
    df1 = get_roster(data_dir, year)
    df2 = get_pergame(data_dir, year)
    df3 = get_salaries(data_dir, year)
    df4 = get_advanced(data_dir, year)
    del df2['year']
    del df3['year']
    del df4['year']

    # FIXME -- players who get traded wind up as dupes.  here I just drop
    # drop their first team, which isn't optimal, their stats should be
    # averaged or something.
    df1.drop_duplicates('Player', inplace=True, take_last=True)
    df2.drop_duplicates('Player', inplace=True, take_last=True)
    df3.drop_duplicates('Player', inplace=True, take_last=True)
    df4.drop_duplicates('Player', inplace=True, take_last=True)
    df5 = pd.merge(df1, df2, left_on="Player", right_on="Player", how="outer")
    df6 = pd.merge(df5, df3, left_on="Player", right_on="Player", how="outer")
    df7 = pd.merge(df6, df4, left_on="Player", right_on="Player", how="outer")

    return df7


def htmlToPandas(filename, name):

    cols = ['Season', 'Lg', 'Team', 'W', 'L', 'W/L%', 'Finish', 'SRS', 'Pace',
            'Rel_Pace', 'ORtg', 'Rel_ORtg', 'DRtg', 'Rel_DRtg', 'Playoffs',
            'Coaches', 'WS']

    df = get_dataframe(filename, name)

    df.columns = cols

    df['WS'].replace(r'\xc2\xa0',
                     value=' ',
                     inplace=True,
                     regex=True)
    df['Team'] = name
    df['Season'].replace(r'-\d\d$',
                         value='',
                         inplace=True,
                         regex=True)
    df['Season'] = df['Season'].astype(int)
    df['W'] = df['W'].astype(int)
    df['L'] = df['L'].astype(int)
    df['W/L%'] = df['W/L%'].astype(float)
    df['Finish'] = df['Finish'].astype(float)
    df['SRS'] = df['SRS'].astype(float)
    df['Pace'] = df['Pace'].astype(float)
    df['Rel_Pace'] = df['Rel_Pace'].astype(float)
    df['ORtg'] = df['ORtg'].astype(float)
    df['Rel_ORtg'] = df['Rel_ORtg'].astype(float)
    df['DRtg'] = df['DRtg'].astype(float)
    df['Rel_DRtg'] = df['Rel_DRtg'].astype(float)

    with open('tmp.html', 'w') as fd:
        fd.write(df.to_html().encode('utf-8'))

    return df


def get_fantasy_teams(data_dir, year):
    processed_dir = os.path.join(data_dir, 'processed_data', str(year))
    team_data_file = os.path.join(processed_dir, 'team_data.pkl')
    fantasy_team_file = os.path.join(processed_dir, 'fantasy_team_data.pkl')

    if os.path.isfile(fantasy_team_file):

        df = pd.read_pickle(team_data_file)
        df = df[df['Fantasy Team'] != 'FA']

        grouped = df.groupby('Fantasy Team')
        grouped = grouped.mean()
        grouped['Fantasy Team'] = grouped.index
        grouped.index = range(grouped.shape[0])

        cols_to_round = {'Age': 2, 'G': 2, 'GS': 2, 'MP': 2, 'FG%': 3,
                         'FT%': 3, '3P': 2, 'TRB': 2, 'AST': 2, 'STL': 2,
                         'BLK': 2, 'PTS': 2, 'Salary': 3, 'value': 2,
                         'price': 2, 'PER': 3, 'WS': 3}

        for ii in cols_to_round:
            grouped[ii] = np.round(grouped[ii], cols_to_round[ii])

        grouped.to_pickle(fantasy_team_file)

    return
