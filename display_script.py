from dash import Dash, html, dcc
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from pycoingecko import CoinGeckoAPI
import pytz
from datetime import datetime
import time
import requests

def get_time_string(dt):
    
    days = ["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"]
    dow = days[dt.weekday()]
    year = dt.year
    day = dt.day
    hour = dt.hour
    minute = dt.minute
    if minute < 10:
        minute = f"0{minute}"
    string = f"""{dow} {day}, {year} {hour}:{minute}"""
    return string  

def query_cg():
    return CoinGeckoAPI().get_price(
        ids='bitcoin', vs_currencies='usd', 
        include_24hr_change='true', 
        include_last_updated_at='true'
    )

def get_start_data(init_dict, init_cg):
    last_ts = init_cg["bitcoin"]["last_updated_at"]
    x = [
    i[0] for i in init_dict['result']['300'][-289:] if i[0] < last_ts
    ] + [last_ts]
    
    y = [i[1] for i in init_dict['result']['300'][-289:]]
    y = y[:len(x)-1] + [init_cg['bitcoin']["usd"]]

    return x, y

def get_color(p1, p2):
    green = 'rgba(30, 130, 76, 1)'
    red = 'rgba(217, 30, 24, 1)'
    if p1 > p2:
        return red
    else:
        return green

def get_percent_change(p1, p2):
    return round((abs(p2-p1)  / p1 ) * 100, 2)
    
r = requests.get("https://api.cryptowat.ch/markets/binance/btcusdt/ohlc")
init_data = eval(r.text)
tz = pytz.timezone('America/Denver')

dt = datetime.now(tz=tz)

beginning_data = query_cg()
x, y = get_start_data(init_data, beginning_data)
last_price = y[-1]
delta = get_percent_change(y[0],y[-1])
if delta > 0:
    sign = "+"
else:
    sign = "-"
title =  f"${last_price} ({sign}{delta}%)"

fig = go.FigureWidget(
    go.Scatter(
    x=[datetime.fromtimestamp(t) for t in x],
    y=y,
    line={'color':get_color(y[0], y[-1])},
    mode='lines'
    )
)
fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0), 
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    width=1280*0.5,
    height=350*0.5,
    xaxis={
    'showgrid': False, # thin lines in the background
    'zeroline': False, # thick line at x=0
    'visible': False, 
    },
    yaxis={
    'showgrid': False, # thin lines in the background
    'zeroline': False, # thick line at x=0
    'visible': False, 
    }
)

app = Dash()
app.layout = html.Div([
    html.H1(
        title,
        id="title",
        style={"color":'rgba(255,255,255,1)'}
        ),
    dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        id='update-graph'),
    dcc.Interval(
        id='interval-update',
        interval=60*1000,
        n_intervals=0
        )
    ],
    style={
        'backgroundColor': '#000000',
        'font-family':'monospace',
        'font-color' : 'rgba(255,255,255,1)'
        }
    )

@app.callback(Output('title', 'children'),
              Input('interval-update', 'n_intervals'),
              State('update-graph', 'figure'))
def update_title(n, fig):
    delta = get_percent_change(fig["data"][0]['y'][0],fig["data"][0]['y'][-1])
    if fig["data"][0]['y'][0] < fig["data"][0]['y'][-1]:
        sign = "+"
    else:
        sign = "-"
    last_price = fig["data"][0]['y'][-1]
    title =  f"${last_price} ({sign}{delta}%)"
    return title

@app.callback(Output('update-graph', 'figure'),
              Input('interval-update', 'n_intervals'),
              State('update-graph', 'figure'))
def plot(n, fig):
    dt = datetime.now(tz=tz)
    dt_unix = dt.timestamp()

    dates = [datetime.strptime(i, "%Y-%m-%dT%H:%M:%S") for i in fig["data"][0]['x']]
    unix_times = [i.timestamp() for i in dates]
    last_ts = unix_times[-1]

    if dt_unix - last_ts > 240:
        time.sleep(8)
        resp = query_cg()
        gc_ts = resp['bitcoin']['last_updated_at']

        if gc_ts > last_ts:
            fig["data"][0]['y'] += [resp['bitcoin']['usd']]
            fig["data"][0]['x'] += [datetime.fromtimestamp(gc_ts)]
            while (datetime.fromtimestamp(gc_ts) - datetime.strptime(fig["data"][0]['x'][0], "%Y-%m-%dT%H:%M:%S")).total_seconds() > 86400:
                fig["data"][0]['x'].pop(0)
                fig["data"][0]['y'].pop(0)

    new_color = get_color(fig["data"][0]['y'][0], fig["data"][0]['y'][-1])    
    if fig["data"][0]['line']['color'] != new_color:
        fig_new = go.FigureWidget(
            go.Scatter(
                x=fig["data"][0]['x'],
                y=fig["data"][0]['y'],
                mode='lines',
                line={'color':new_color}
            )
        )
        return fig_new.update_layout(
            margin=dict(l=0, r=0, t=0, b=0), 
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            width=1280*0.5,
            height=350*0.5,
            xaxis={
            'showgrid': False, # thin lines in the background
            'zeroline': False, # thick line at x=0
            'visible': False, 
            },
            yaxis={
            'showgrid': False, # thin lines in the background
            'zeroline': False, # thick line at x=0
            'visible': False, 
            }
        )

    return fig

app.run_server()