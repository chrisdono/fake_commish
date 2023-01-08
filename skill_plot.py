import os
from dotenv import load_dotenv
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from espn_api.football import League

plt.rcParams.update({'font.size': 18})

load_dotenv()

fantasy_league_id = int(os.getenv("LEAGUE_ID"))
cookie_espn_s2 = os.getenv("ESPN_S2")
cookie_swid = os.getenv("SWID")

league_id = fantasy_league_id
espn = cookie_espn_s2
swid = cookie_swid

season = 2022
posns = ['QB', 'RB', 'WR', 'RB/WR', 'TE', 'D/ST', 'K']
struc = [1,2,2,1,1,1,1]

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


def get_matchups(league_id, season, week, swid='', espn=''):
    ''' 
    Pull full JSON of matchup data from ESPN API for a particular week.
    '''
    
    url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + \
      str(season) + '/segments/0/leagues/' + str(league_id)

    r = requests.get(url + '?view=mMatchup&view=mMatchupScore',
                     params={'scoringPeriodId': week, 'matchupPeriodId': week},
                     cookies={"SWID": swid, "espn_s2": espn})
    return r.json()

def get_slates(json):
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
    
    return tm_names


data = {}
slates = {}
ds = {}
print('Week:', end=' ')

for week in range(1,14):
    # print(week, end=' ')
    d      = get_matchups(league_id, season, week, swid=swid, espn=espn)
    wslate = get_slates(d)
    wdata  = compute_pts(wslate, posns, struc)
    data[week] = wdata
    slates[week] = wslate
    ds[week] = d
    if week == 1:
        print('week ', week)
        # print('wslate')
        # print(wslate)
        print('wdata')
        print(wdata)
        print('data[week]')
        print(data[week])

tm_names = get_teamnames(league_id, season, 1, swid=swid, espn=espn)

wks = range(1,14)

# get league average diff
adiffs = []
for wk in wks:
    for tmid, pts in data[wk].items():
        adiffs.append(pts['apts']-pts['opts'])
avgdiffs = sum(adiffs) / len(adiffs)
print('avgdiffs: ', avgdiffs)

# get league average optimal points
allopts = []
for wk in wks:
    for tmid, pts in data[wk].items():
        allopts.append(pts['opts'])
avgopts = sum(allopts) / len(allopts)
print('avgopts: ', avgopts)

z = []

print('tmid: ', tmid)
print('tm_names: ', tm_names)

for tmid, tmname in tm_names.items():
    opts  = [data[wk][tmid]['opts'] for wk in wks]
    print('opts: ', opts)
    diffs = [data[wk][tmid]['apts']-data[wk][tmid]['opts'] for wk in wks]
    print('diffs: ', diffs)
    opts = sum(opts) / len(opts)
    diffs = sum(diffs) / len(diffs)
    z.append({'id': tmid, 'name': tmname, 'opt': opts, 'diff': diffs})
    print('id: ', tmid, 'name: ', tmname, 'opt: ', opts, 'diff: ', diffs)


fig, ax = plt.subplots(1,1, figsize=(9,8))

playoffs = [5, 11, 13, 14]

clist = sns.color_palette('deep', len(tm_names))

# minx, maxx = min([zz['diff'] for zz in z])-10, 5
# miny, maxy = min([zz['opt'] for zz in z])-10, max([zz['opt'] for zz in z])+20
minx, maxx = min([zz['diff'] for zz in z])-5, 0
miny, maxy = min([zz['opt'] for zz in z])-5, max([zz['opt'] for zz in z])+10

# ax.plot([0,0], [miny+5, maxy-10], 'k-', alpha=0.2)
ax.plot([avgdiffs, avgdiffs], [miny+5, 148], 'k--', alpha=0.2)
ax.plot([-25, -5], [avgopts, avgopts], 'k--', alpha=0.2)
ax.text(maxx-15, avgopts-1.5, 'LEAGUE AVERAGES', {'color': 'black', 'fontstyle': 'italic'},
        alpha=0.5)

for i, zz in enumerate(z):
    ax.scatter(zz['diff'], zz['opt'], 
               marker='o' if zz['id'] in playoffs else 'x',
               s=200, c=clist[i], edgecolors='k',
               label=zz['name'])
    
ax.legend(bbox_to_anchor=(1.05, 0.8), frameon=False)

# this is really hacky
ax.arrow(-22,maxy-5, 14,0,
         head_width=1.5, head_length=2, facecolor='k', edgecolor='k', alpha=0.2)
ax.text(-20,maxy-4, 'Better Starter Selection', {'color': 'black', 'fontstyle': 'italic'}, alpha=0.5)
ax.arrow(-27,miny+10, 0, (maxy-miny) / 2,
         head_width=1, head_length=3, facecolor='k', edgecolor='k', alpha=0.2)
ax.text(-28,miny+20, 'Better Roster', {'color': 'black', 'fontstyle': 'italic'},
        rotation=90, alpha=0.5)

ax.set(xlim=[minx,maxx], ylim=[miny,maxy],
       xticks=range(int(minx/10)*10-10,9,10),
       xlabel='Actual Points Back from Best Possible (Season Average)',
       ylabel='Best Possible Points (Season Average)',
       title='%d Rebel Tiger FFL Season' % season)

fig.savefig('roster_skill_final_2022.png', bbox_inches='tight')
