import sys
import os
import openai
from espn_api.football import League
from dotenv import load_dotenv
import wrapup_gifs
import util_functions
import matchup_plot
from tabulate import tabulate as table
# from mdutils.mdutils import MdUtils

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
fantasy_league_id = int(os.getenv("LEAGUE_ID"))
cookie_espn_s2 = os.getenv("ESPN_S2")
cookie_swid = os.getenv("SWID")

class wrapup:
    def __init__(self, week, _year):
        self.scores = {}
        self.week = week
        league_id = fantasy_league_id
        # year = 2022
        year = _year
        self.league = League(league_id=league_id, year=year, 
                        espn_s2=cookie_espn_s2, swid = cookie_swid)

    def create_prompt(self):
        i = 1
        output = []
        home_result = 'w'
        away_result = 'l'
        self.scores = {}
        output.append(f'WEEK {self.week} MATCHUPS\n')
        for m in self.league.scoreboard(week=self.week):
            output.append('- ')
            output.append(m.home_team.owner.replace('  ', ' '))
            output.append(' (')
            output.append(m.home_team.team_name.strip().replace('-', '').replace('  ', ' '))
            output.append(') scored ')
            output.append(str(m.home_score))
            if m.home_score > m.away_score:
                output.append(' to beat ')
            else:
                output.append(' to lose to ')
            output.append(m.away_team.owner.replace('  ', ' '))
            output.append(' (')
            output.append(m.away_team.team_name.strip().replace('-', '').replace('  ', ' '))
            output.append(') who scored ')
            output.append(str(m.away_score))
            output.append('.\n')
            if m.home_score > m.away_score:
                home_result = 'w'
                away_result = 'l'
            else:
                home_result = 'l'
                away_result = 'w'
            self.scores[m.home_team.owner.replace('  ', ' ')] = [m.home_score, home_result] 
            self.scores[m.away_team.owner.replace('  ', ' ')] = [m.away_score, away_result] 
            i += 1

        i = 1
        output.append('\n')
        output.append(f'WEEK {self.week} STANDINGS\n')
        output.append(f'place. owner. wins-losses. playoff chance.\n')
        for t in self.league.standings():
            output.append(str(i))
            output.append('. ')
            output.append(t.owner.strip().replace('-', '').replace('  ', ' '))
            output.append('. ')
            output.append(str(t.wins))
            output.append('-')
            output.append(str(t.losses))
            output.append('. ')
            output.append(str(t.playoff_pct))
            output.append('%.\n')
            i += 1

        # print(''.join(output))
        return ''.join(output)

    def create_stats(self):
        average = 0
        total = 0
        for key, item in self.scores.items():
            total += item[0]
        average = total / len(self.scores)

        output = []
        # print(f'total: {total}')
        # print(f'len: {len(self.scores)}')
        # print(f'average: {average}')

        lucky_winners = []
        unlucky_losers = []
        highest_score = ['No-one', 0]
        lowest_score = ['No-one', 1000]
        for key, item in self.scores.items():
            if (item[0] > average) and (item[1] == 'l'):
                unlucky_losers.append([key, item[0]])
            if (item[0] < average) and (item[1] == 'w'):
                lucky_winners.append([key, item[0]])
            if item[0] > highest_score[1]:
                highest_score = [key, item[0]]
            if item[0] < lowest_score[1]:
                lowest_score = [key, item[0]]

        # output.append('Big Dick:  ')
        output.append(f'{highest_score[0]} {str(highest_score[1])} \n')
        # output.append('Little Bitch:  ')
        output.append(f'{lowest_score[0]} {str(lowest_score[1])} \n')

        # output.append('\n')
        # output.append('Lucky Winners:\n')
        # if not lucky_winners:
        #     lucky_winners.append('none\n')
        # else:
        #     for lucky in lucky_winners:
        #         output.append(f'{lucky[0]} {str(lucky[1])} \n')
        # output.append('\n')
        output.append(lucky_winners)
        # output.append('Unlucky Losers:\n')
        # if not unlucky_losers:
        #     unlucky_losers.append('none\n')
        # else:
        #     for unlucky in unlucky_losers:
        #         output.append(f'{unlucky[0]} {str(unlucky[1])} \n')
        output.append(unlucky_losers)

        # return ''.join(output)
        return output

def get_summary(new_prompt):
    response = openai.Completion.create(
            model="text-davinci-002",
            # model="text-curie-001",
            # max_tokens=500,
            # temperature=0.92,
            max_tokens=1600,
            presence_penalty=0.1,
            frequency_penalty=0.4,
            temperature=0.90,
            prompt=new_prompt
        )
    print(response)
    # print(response.choices[0].text)
    return response.choices[0].text


def generate_prompt(new_wrapup):
    return open('ai_prompt.txt', 'r').read().format(new_wrapup)

if __name__ == "__main__":
    week = int(sys.argv[1])
    year = int(sys.argv[2])
    filename = "week_" + str(week)
    # don't need a title
    filetitle = "Week " + str(week)
    f = open("../rebeltigerffl/"+filename+".md", "w")

    # add front matter
    f.write("---\n")
    f.write("layout: page\n")
    f.write(f"title: {filetitle} Wrapup\n")
    f.write(f"subtitle: October 12, 2022\n")
    f.write("---\n")
    f.write("\n")

    # get data for the week
    w = wrapup(week, year)
    week_info = w.create_prompt()
    # print('FULL INFO')
    print(week_info)

    # add summary
    f.write("### Summary\n")
    prompt = generate_prompt(week_info)

    summary = get_summary(prompt)
    # summary = "test summary"

    f.write(summary)
    f.write("  *- Fake Commish*")
    f.write("\n")
    f.write("\n")
    f.write("___\n")
    f.write("\n")

    # add weekly awards
    f.write("### Weekly Awards\n")
    f.write("\n")
    stats = w.create_stats()
    f.write("#### Big Dick Award (Most Total Points) $$\n")
    f.write(stats[0])
    f.write("\n")
    f.write("![]("+wrapup_gifs.get_winner_gif()+")\n")
    f.write("\n")

    f.write("#### Little Bitch Award (Fewest Total Points)\n")
    f.write(stats[1])
    f.write("\n")
    f.write("![]("+wrapup_gifs.get_loser_gif()+")\n")
    f.write("\n")

    f.write("\n")
    f.write("___\n")
    f.write("\n")

    # add Matchup section
    f.write("### Matchups Overview\n")
    f.write("\n")
    matchup_plot.generate_matchup_plot(week, year)
    f.write("![](../assets/img/week"+str(week)+"_matchups.png)\n")

    f.write("\n")
    
    lw = []
    ul = []
    if stats[2]:
        # f.write("Lucky Winners:\n")
        for lucky in stats[2]:
            lw.append(lucky[0])
        #     f.write("* "+lucky[0])
        #     f.write("\n")
        # f.write("\n")
    else:
        lw.append(' -- ')

    if stats[3]:
        # f.write("Unlucky Losers:\n")
        for unlucky in stats[3]:
            ul.append(unlucky[0])
        #     f.write("* "+unlucky[0])
        #     f.write("\n")
        #     # f.write("  "+unlucky[0]+" - "+str(unlucky[1])+"\n")
        # f.write("\n")
    else:
        ul.append(' -- ')

    f.write("\n")
    f.write("**Best and Worst for the Week**\n")
    f.write("\n")

    leag = util_functions.fetch_league(league_id=fantasy_league_id, year=2022, week = week,
                  espn_s2 = cookie_espn_s2, swid = cookie_swid)

    stats_tables = util_functions.print_weekly_stats(leag, week, lw, ul)
    # f.write(util_functions.print_weekly_stats(leag, week, lw, ul))
    f.write("\n")
    f.write(table(stats_tables[0], headers = ['Category', 'Owner'], tablefmt='github'))
    f.write("\n")
    f.write("\n")

    # util_functions.print_power_rankings(leag, week)
    # util_functions.print_current_standings(leag)

    f.write("\n")
    f.write("**Best and Worst Positions for the Week**\n")
    f.write("\n")
    f.write("\n")
    f.write(table(stats_tables[1], headers = ['Category', 'Owner'], tablefmt='github'))
    f.write("\n")
    f.write("\n")

    # print(stats)
    # print(summary)

    f.close()


