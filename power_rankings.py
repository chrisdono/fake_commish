import sys
import os
from espn_api.football import League
from dotenv import load_dotenv
import util_functions
from tabulate import tabulate as table
# from mdutils.mdutils import MdUtils

load_dotenv()
fantasy_league_id = int(os.getenv("LEAGUE_ID"))
cookie_espn_s2 = os.getenv("ESPN_S2")
cookie_swid = os.getenv("SWID")


if __name__ == "__main__":
    week = int(sys.argv[1])
    filename = "power_rankings"
    # don't need a title
    filetitle = "Power Rankings"

    f = open("../rebeltigerffl/"+filename+".md", "w")

    # add front matter
    f.write("---\n")
    f.write("layout: page\n")
    f.write(f"title: {filetitle}\n")
    f.write("---\n")
    f.write("\n")

    f.write(f"### Power Rankings Week {week+1}\n")
    f.write("\n")

    leag = util_functions.fetch_league(league_id=fantasy_league_id, year=2022, week = week,
                  espn_s2=cookie_espn_s2, swid = cookie_swid)

    pow_rank = util_functions.print_power_rankings(leag, week)
    div_rank = util_functions.print_current_standings(leag)


    f.write(table(pow_rank, 
                headers = ['No.', 'Team', 'PowerRank Formula', 'Wins', 'Losses', 'Ties', 'Playoff Chance', 'Points Scored', 'Owner'], 
                floatfmt = '.2f', tablefmt = 'github'))

    f.write("\n")
    f.write("\n")
    f.write(f"### Standings\n")
    f.write("\n")
    f.write(f"#### BD Division Standings Week {week+1}\n")
    f.write("\n")
    f.write(table(div_rank[0], 
                headers = ['Team', 'Wins', 'Losses', 'Ties', 'Points Scored', 'Owner'], 
                floatfmt = '.2f', tablefmt = 'github'))     

    f.write("\n")
    f.write("\n")
    f.write(f"#### JT Division Standings Week {week+1}\n")
    f.write("\n")
    f.write(table(div_rank[1], 
                headers = ['Team', 'Wins', 'Losses', 'Ties', 'Points Scored', 'Owner'], 
                floatfmt = '.2f', tablefmt = 'github'))     
    f.write("\n")

    f.close()


