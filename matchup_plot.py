import os
from dotenv import load_dotenv
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from espn_api.football import League

load_dotenv()

fantasy_league_id = int(os.getenv("LEAGUE_ID"))
cookie_espn_s2 = os.getenv("ESPN_S2")
cookie_swid = os.getenv("SWID")

slotcodes = {
    0 : 'QB', # 1 : 'QB',
    2 : 'RB', # 3 : 'RB',
    3 : 'RB/WR', # 3 : 'RB',
    4 : 'WR', # 5 : 'WR',
    6 : 'TE', # 7 : 'TE',
    16: 'D/ST',
    17: 'K',
    20: 'Bench',
    21: 'IR',
    23: 'Flex'
}

swid = "your swid"
espn = "your espn cookie"

def get_matchups(league_id, season, week, swid='', espn=''):
    ''' 
    Pull full JSON of matchup data from ESPN API for a particular week.
    '''
    
    url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + \
      str(season) + '/segments/0/leagues/' + str(league_id)

    r = requests.get(url + '?view=mMatchup&view=mMatchupScore',
                     params={'scoringPeriodId': week, 'matchupPeriodId': week},
                     cookies={"SWID": swid, "espn_s2": espn})
    # f = open('djson.json', 'w')
    # f.write(r.text)
    # f.close()
    return r.json()

# def get_slates(json):
def get_slates(d, week):
    '''
    Constructs week team slates with slotted position, 
    position, and points (actual and ESPN projected),
    given full matchup info (`get_matchups`)
    '''
    
    slates = {}

    for team in d['teams']:
        slate = []
        for p in team['roster']['entries']:
            # get name
            name  = p['playerPoolEntry']['player']['fullName']

            # get actual lineup slot
            slotid = p['lineupSlotId']
            slot = slotcodes[slotid]

            # get projected and actual scores
            act, proj = 0, 0
            for stat in p['playerPoolEntry']['player']['stats']:
                if stat['scoringPeriodId'] != week:
                    continue
                if stat['statSourceId'] == 0:
                    act = stat['appliedTotal']
                elif stat['statSourceId'] == 1:
                    proj = stat['appliedTotal']
                else:
                    print('Error')

            # get type of player
            pos = 'Unk'
            ess = p['playerPoolEntry']['player']['eligibleSlots']
            if 0 in ess: pos = 'QB'
            elif 2 in ess: pos = 'RB'
            elif 4 in ess: pos = 'WR'
            elif 6 in ess: pos = 'TE'
            elif 16 in ess: pos = 'D/ST'
            elif 17 in ess: pos = 'K'

            slate.append([name, slotid, slot, pos, act, proj])

        slate = pd.DataFrame(slate, columns=['Name', 'SlotID', 'Slot', 'Pos', 'Actual', 'Proj'])
        slates[team['id']] = slate

    return slates

def compute_pts(slates, posns, struc):
    '''
    Given slates (`get_slates`), compute total roster pts:
    actual, optimal, and using ESPN projections
    
    Parameters
    --------------
    slates : `dict` of `DataFrames`
        (from `get_slates`)
    posns : `list`
        roster positions, e.g. ['QB','RB', 'WR', 'TE']
    struc : `list`
        slots per position, e.g. [1,2,2,1]
        
    * This is not flexible enough to handle "weird" leagues
    like 6 Flex slots with constraints on # total RB/WR
    
    Returns
    --------------
    `dict` of `dict`s with actual, ESPN, optimal points
    '''
    
    data = {}
    for tmid, slate in slates.items():
        pts = {'opts': 0, 'epts': 0, 'apts': 0}

        # ACTUAL STARTERS
        pts['apts'] = slate.query('Slot not in ["Bench", "IR"]').filter(['Actual']).sum().values[0]

        # OPTIMAL and ESPNPROJ STARTERS
        for method, cat in [('Actual', 'opts'), ('Proj', 'epts')]:
            actflex = -100  # actual pts scored by flex
            proflex = -100  # "proj" pts scored by flex
            for pos, num in zip(posns, struc):
                # actual points, sorted by either actual or proj outcome
                t = slate.query('Pos == @pos').sort_values(by=method, ascending=False).filter(['Actual']).values[:,0]

                # projected points, sorted by either actual or proj outcome
                t2 = slate.query('Pos == @pos').sort_values(by=method, ascending=False).filter(['Proj']).values[:,0]

                # sum up points
                pts[cat] += t[:num].sum()

                # set the next best as flex
                # UPDATE TO HANDLE NO TE FLEX
                # if pos in ['RB', 'WR', 'TE'] and len(t) > num:
                if pos in ['RB', 'WR'] and len(t) > num:
                    fn = t[num] if method=='Actual' else t2[num]
                    if fn > proflex:
                        actflex = t[num]
                        proflex = fn

            pts[cat] += actflex
        
        data[tmid] = pts
        
    return data

def get_teamnames(league_id, season, week, swid='', espn=''):
    url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + \
      str(season) + '/segments/0/leagues/' + str(league_id)
    
    r = requests.get(url + '?view=mTeam',
                  params={'scoringPeriodId': week},
                  cookies={"SWID": swid, "espn_s2": espn})
    d = r.json()
    
    tm_names = {tm['id']: tm['location'].strip() + ' ' + tm['nickname'].strip() \
                for tm in d['teams']}
    
    print(tm_names)
    return tm_names

def plot_week(d, data, week, tm_names, _year, nummatchups=5,
              minx=70, maxx=200, legend=4):
    fig, ax = plt.subplots(1,1, figsize=(12,8))

    # hardcoded plot adjustments
    dif, offset = 5, 2
    
    # for y-axis tick labels
    tmlist, tmticks, tmbold = [], [], []

    cury = 0
    # print(data)
    start_match = nummatchups*(week-1)
    end_match = start_match + nummatchups
    # for g in d['schedule'][:nummatchups]:
    for g in d['schedule'][start_match:end_match]:
        aid, anm = -1, ''
        hid, hnm = -1, ''
        try:
            aid = g['away']['teamId']
            anm = tm_names[aid]
            hid = g['home']['teamId']
            hnm = tm_names[hid]
            print('aid: ' + str(aid) + ', ' + anm)
            print('hid: ' + str(hid) + ', ' + hnm)
        except:
            continue

        tmlist.append(anm)
        tmlist.append(hnm)

        if data[aid]['apts'] > data[hid]['apts']:
            tmbold.extend([1,0])
        else:
            tmbold.extend([0,1])

        for pts in [data[aid], data[hid]]:
            h = 1 if (pts['opts']-offset) > pts['apts'] else 0
            tmticks.append(cury)
            ax.plot([minx, maxx], [cury, cury], 'k--', linewidth=1, alpha=0.1)
            ax.plot([pts['apts'], pts['opts']-offset*h], [cury, cury], 'k-')
            ax.scatter(pts['epts'], cury, c='w', s=200, marker='o', edgecolor='g')
            ax.scatter(pts['apts'], cury, c='k', s=100)

            # if optimal==actual, need to put blue inside black
            if pts['opts'] == pts['apts']:
                ax.scatter(pts['opts'], cury, c='w', s=25)
                ax.scatter(pts['opts'], cury, c='b', s=25, alpha=0.2)
            else:
                ax.scatter(pts['opts'], cury, c='b', s=100, alpha=0.2)

            cury += dif

        cury += 2*dif
        
        # debugging
    print('team list')
    print(tmlist)
    print('team ticks')
    print(tmlist)
    print('team bold')
    print(tmbold)

    # setting y-axis
    ax.set(yticks=tmticks,
           yticklabels=tmlist)
    for k, tick in enumerate(ax.yaxis.get_major_ticks()):
        if tmbold[k] == 1:
            tick.label1.set_fontweight('bold')

    # legend stuff
    ax.scatter([],[], c='k', s=100, label='Actual')
    ax.scatter([],[], c='w', s=200, marker='o', edgecolor='g', label='ESPN')
    ax.scatter([],[], c='b', s=100, alpha=0.2, label='Best Possible')
    ax.legend(loc=legend, borderaxespad=2, borderpad=1, labelspacing=1.5, 
              shadow=True, fontsize=12)

    ax.set(title='Week %d' % week)

    # return ax
    plt.savefig('../rebeltigerffl/assets/img/matchup_'+str(_year)+'-'+str(week)+'.png', bbox_inches="tight")

def generate_matchup_plot(_week, _year):
    league_id = fantasy_league_id
    season = _year
    week = _week
    espn = cookie_espn_s2
    swid = cookie_swid

    posns = ['QB', 'RB', 'WR', 'RB/WR', 'TE', 'D/ST', 'K']
    struc = [1,2,2,1,1,1,1]

    d      = get_matchups(league_id, season, week, swid=swid, espn=espn)
    slates = get_slates(d, week)
    wdata  = compute_pts(slates, posns, struc)

    '''
    print("d\n")
    print(d)
    print("\n")
# print('slates')
# print(slates)
    print('data\n')
    print(wdata)
    print("\n")
    '''
    tms    = get_teamnames(league_id, season, week, swid=swid, espn=espn)
    '''
    print('tms')
    print("\n")
    print(tms)
    print("\n")
    '''

    '''
# override for blog
    tms = {
        1: 'His Excellency the Commissioner',
        2: 'Beat Navy',
        3: 'The Gus Bus',
        4: 'Turn Your Head and Goff',
        5: 'That B* Team 2 Married',
        9: 'a^2 + b^2 = c^hawks',
        12: 'the mustard',
        13: 'Master of the Sword',
        14: 'La Flama Blanca',
        15: 'Glitter Fairies'
    }
    '''

    # ax = plot_week(d, wdata, week, tms, nummatchups=5)
    plot_week(d, wdata, week, tms, season, nummatchups=5)
    # plt.show()
    # plt.savefig('../rebeltigerffl/assets/img/week'+str(week)+'_matchups.png', bbox_inches="tight")
