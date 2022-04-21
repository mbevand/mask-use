#!/usr/bin/python

import math, datetime
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from matplotlib import rcParams
import matplotlib.pyplot as plt

time_period = ('7/1/20', '12/31/20')

def cd(d):
    return datetime.datetime.strptime(d, '%m/%d/%y').strftime('%Y-%m-%d')

def chart(counties):
    rcParams['font.family'] = 'serif'
    rcParams['font.serif'] = 'Latin Modern Roman'
    rcParams['font.weight'] = 'bold'
    rcParams['axes.labelweight'] = 'bold'
    rcParams['axes.labelsize'] = 'x-large'
    plt.style.use('dark_background')
    (fig, ax) = plt.subplots(dpi=700, figsize=(7, 3))
    ax.text(.45, 1, 'Mask Usage & COVID-19 Cases\nin United States Counties',
            transform=ax.transAxes, ha='center', fontsize='x-large')
    ax.text(1, .95, 'Marc Bevand\n@zorinaq',
            transform=ax.transAxes, ha='right', fontsize='x-small')
    ax.text(.5, -.21, 'Source: https://github.com/mbevand/mask-use',
            transform=ax.transAxes, ha='center', va='top', fontsize='x-small')
    ax.semilogy()
    #ax.tick_params(axis='x', bottom=False, labelbottom=False)
    for sp in ax.spines:
        ax.spines[sp].set_visible(False)
    ax.set_ylabel('Cases per million people')
    ax.set_xlabel(f'← Less{" "*14}Mask usage{" "*14}More →')
    x = [_['score'] for _ in counties.values()]
    y = [_['rate'] for _ in counties.values()]
    ax.scatter(x, y, color=(1,1,1,.7), marker='o', s=5)
    # regression
    reg = LinearRegression().fit(np.reshape(x, (-1, 1)), np.reshape(np.log(y), (-1, 1)))
    preds = np.reshape(reg.predict(np.reshape(x, (len(x), -1))), (len(x),))
    r2 = r2_score(np.log(y), preds)
    print(f'R²={r2:.3f}')
    x1, x2 = ax.get_xlim()
    x = np.linspace(x1, x2)
    y = np.exp(np.reshape(reg.predict(np.reshape(x, (len(x), -1))), (len(x),)))
    ax.plot(x, y, c='red', lw=3)
    ax.set_xlim(left=x1, right=x2)
    ax.text(.05, .05, f'Linear reg: R²={r2:.3f}', transform=ax.transAxes,
            ha='left', va='bottom', color='red')
    fig.savefig('chart.png', bbox_inches='tight')
    return

def init():
    # survey mask use data from
    # https://github.com/nytimes/covid-19-data/blob/master/mask-use/mask-use-by-county.csv
    df = pd.read_csv('mask-use-by-county.csv')
    # Calculate masking score
    df['score'] = \
        0 * df['NEVER'] + \
        25 * df['RARELY'] + \
        50 * df['SOMETIMES'] + \
        75 * df['FREQUENTLY'] + \
        100 * df['ALWAYS']
    counties = {}
    for _, row in df.iterrows():
        counties[int(row['COUNTYFP'])] = { 'score': float(row['score']) }
    # population data
    # download this from https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv
    population = {}
    df = pd.read_csv('time_series_covid19_deaths_US.csv')
    for _, row in df.iterrows():
        fips = row['FIPS']
        if math.isnan(fips):
            continue
        population[int(fips)] = int(row['Population'])
    # JHU data
    # download this from https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv
    df = pd.read_csv('time_series_covid19_confirmed_US.csv')
    for _, row in df.iterrows():
        fips = row['FIPS']
        if math.isnan(fips):
            # skip rows without a FIPS code (affects just a handful of counties)
            #print(f'skipping {row["Admin2"]}, {row["Province_State"]}')
            continue
        fips = int(fips)
        pop = population[fips]
        if not pop:
            # skip rows lacking population data (typically "out of state",
            # or not assigned to a county)
            #print(f'skipping {row["Admin2"]}, {row["Province_State"]}')
            continue
        cases = int(row[time_period[1]]) - int(row[time_period[0]])
        rate = 1e6 * cases / pop
        if fips not in counties:
            # skip counties for which we have no mask use data (mostly Puerto Rico)
            #print(f'{fips}: unknown fips for {row["Admin2"]}, {row["Province_State"]}')
            continue
        counties[fips]['pop'] = pop
        counties[fips]['cases'] = cases
        counties[fips]['rate'] = rate
    print(f'{len(counties)} counties loaded')
    delete = set()
    for (fips, h) in counties.items():
        if h['cases'] < 1:
            delete.add(fips)
    for d in delete:
        del(counties[d])
    print(f'{len(counties)} counties kept')
    return counties

def main():
    counties = init()
    chart(counties)

main()
