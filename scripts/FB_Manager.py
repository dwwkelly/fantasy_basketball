#!/usr/bin/env python
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

__author__ = "Devin Kelly"

import os
import time
import click
import SimpleHTTPServer
import SocketServer

from Fantasy_Basketball import download_data
from Fantasy_Basketball import get_player_stats
from Fantasy_Basketball import default_dir
from Fantasy_Basketball import Plotter
from Fantasy_Basketball import Web
from Fantasy_Basketball import ESPN_League
from Fantasy_Basketball import get_fantasy_teams


@click.group()
def cli():
    pass


@cli.command()
@click.option('--data_dir',
              default=default_dir,
              help='Download Fantasy Basketball Data')
@click.option('--teams', is_flag=True, default=False,
              help="Download NBA Team Data Only")
@click.option('--draft', is_flag=True, default=False,
              help="Download Draft Data Only")
@click.option('--league', is_flag=True, default=False,
              help="Download Fantasy League Data Only")
@click.option('--year', default=time.strftime('%Y', time.localtime()),
              help="The year to use downloading stats")
@click.option('--league_id', default=None,
              help="The ESPN League ID to use downloading stats")
def download(data_dir, teams, draft, league, year, league_id):
    click.echo('Downloading to {0}'.format(data_dir))
    download_data(data_dir, teams, draft, league, year, league_id)


@cli.command()
@click.option('--data_dir',
              default=default_dir,
              help='Process Fantasy Basketball Data')
@click.option('--teams', is_flag=True, default=False,
              help="Process NBA Team Data Only")
@click.option('--league', is_flag=True, default=False,
              help="Process Fantasy League Data Only")
@click.option('--year', default=time.strftime('%Y', time.localtime()),
              help="The year to use downloading stats")
def process(data_dir, teams, league, year):
    click.echo('Processing to {0}'.format(data_dir))
    if league:
        ESPN_League(data_dir, year, league)

    if teams:
        get_player_stats(data_dir, year)

    get_fantasy_teams(data_dir, year)


@cli.command()
@click.option('--data_dir',
              default=default_dir,
              help='Process Fantasy Basketball Data')
def write_html(data_dir):
    click.echo('Writing HTML Data to {0}'.format(data_dir))
    web = Web(data_dir)
    web.gen_html()


@cli.command()
@click.option('--data_dir',
              default=default_dir,
              help='Process Fantasy Basketball Data')
@click.option('--year', default=time.strftime('%Y', time.localtime()),
              help="The year to use downloading stats")
@click.option('--img_format', default='eps',
              help='Image format, EPS or PNG')
def plot(data_dir, year, img_format):
    if not(img_format is not 'eps' and img_format is not 'png'):
        print "Invalid img_format, must be either 'png' or 'eps'"
        return
    print 'Plotting to {0}'.format(data_dir)
    plotter = Plotter(data_dir, year)
    plotter.make_all_plots(img_format)


@cli.command()
@click.option('--data_dir',
              default=default_dir,
              help='Process Fantasy Basketball Data')
@click.option('--port', default=8080,
              help='Serve the generated HTML statistics on the given port')
def serve(data_dir, port):
    html_dir = os.path.join(data_dir, 'html')
    orig_dir = os.getcwd()
    os.chdir(html_dir)
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", port), Handler)

    print "serving at port {0}".format(port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    os.chdir(orig_dir)


def main():
    cli()

    return

if __name__ == "__main__":
    main()
