import datetime
import sys
import os
from espn_api.football import League
from dotenv import load_dotenv
import util_functions
from tabulate import tabulate as table
import matplotlib.pyplot as plt
# from mdutils.mdutils import MdUtils

load_dotenv()
fantasy_league_id = int(os.getenv("LEAGUE_ID"))
cookie_espn_s2 = os.getenv("ESPN_S2")
cookie_swid = os.getenv("SWID")


if __name__ == "__main__":
    week = int(sys.argv[1])
    year = 2023
    # filename = "power_rankings"
    filename = f"power_rankings_w{week+1}"
    # don't need a title
    filetitle = f"Power Rankings Week {week+1}"
    current_date = datetime.datetime.now()
    date_formatted = current_date.strftime("%Y-%m-%d")

    # f = open("../rebeltigerffl/"+filename+".md", "w")
    f = open("../rebeltigerffl/_posts/2023_power_rankings/"+date_formatted+"-"+filename+".md", "w")

    # add front matter
    f.write("---\n")
    f.write("layout: post\n")
    f.write(f"title: {filetitle}\n")
    f.write(f"tags: {year} ranking\n")
    f.write("---\n")
    f.write("\n")

    start_week = 1
    pow_rank_history = {}
    for wk in range(start_week, week+1):
        print("WEEEEEEEEEEEEEEEEEEEKKKK ", wk)
        leag = util_functions.fetch_league(league_id=fantasy_league_id, year=year, week = wk,
                      espn_s2=cookie_espn_s2, swid = cookie_swid)
        pow_rank = util_functions.print_power_rankings(leag, wk)
        if wk == start_week:
            for team in pow_rank:
                pow_rank_history[team[1]] = [team[0],]
        else:
            for team in pow_rank:
                pow_rank_history[team[1]].append(team[0])
    fig1, ax1 = plt.subplots(figsize=(8,5))
    for key, item in pow_rank_history.items():
        ax1.plot(list(range(start_week+1,week+2)), item, "o-", lw=3, markerfacecolor="white", label=key)
        ax1.annotate(key, xy=(week+1, item[-1]), xytext=(week+1.2,item[-1]), va="center")

    plt.gca().invert_yaxis()
    # plt.yticks(np.arange(1, 11, 1))
    plt.yticks(list(range(1,11)))
    plt.xticks(list(range(start_week+1,week+2)))
    plt.ylabel("Rank") #, fontsize=18)
    plt.xlabel("Week") #, fontsize=18)

    for spine in ax1.spines.values():
        spine.set_visible(False)

    # fig1.suptitle("Power Rankings - 2022 Regular Season", fontsize=20)
    fig1.savefig(f"../rebeltigerffl/assets/img/pr{year}-{week}.png", bbox_inches="tight")


    leag = util_functions.fetch_league(league_id=fantasy_league_id, year=year, week = week,
                  espn_s2=cookie_espn_s2, swid = cookie_swid)
    pow_rank = util_functions.print_power_rankings(leag, week)
    div_rank = util_functions.print_current_standings(leag)

    print("power rankings debug")
    print(pow_rank_history)
    # print(type(pow_rank))
    # print(pow_rank)
    f.write(f"![](../assets/img/pr{year}-{week}.png)\n")
    f.write("\n")
    f.write("\n")
    f.write(f"### Power Rankings Week {week+1}\n")
    f.write("\n")

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


