import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# load dataframe from pickle file (saves by "df.to_pickle('SOME_PATH')")
df = pd.read_pickle('frame_rec_analysis_site_id_28_app_Geschenkefinder_2020-08-15_2020-11-24.pkl')

# collect the set of questions from the given profile-strings
questions = set()

for prof_str in df.profile_str.unique():
    questions.update([quest_option.split('~')[0] for quest_option in prof_str.split()])


# extract the selected option(s) for a given question (from the profile)
def extract(prof_str, question):
    selctions = [q_a.split('~')[1] for q_a in prof_str.split() if q_a.startswith(question)]

    if len(selctions) > 0:
        return ' '.join(sorted(selctions))
    else:
        return None


for q in questions:
    # create new empty column for current question
    df['Q_' + q] = df.profile_str.apply(extract, args=(q,))

data = df.drop(columns='profile_str')

data.clicked = data.clicked.astype(int)

# Extract the month from the datetime and insert it into a new column called Monat
data['Monat'] = data.timestamp.dt.month


new_data = data.copy()
# Investigate the top 10 clicked products
_data=new_data.query('clicked == 1')

d=_data.groupby('product_id',as_index=False).clicked.sum().sort_values(by=['clicked'],ascending=False)
# The 10 top products
dd=d.iloc[0:10,:]
p=dd.product_id.to_list()
new_df=_data.loc[_data['product_id'].isin(p)]
m=new_df.loc[:,['product_id','Q_anlass','Monat']]
# Get one hot encoding of columns B
one_hot = pd.get_dummies(m['Q_anlass'])
# Drop column B as it is now encoded
nn = m.drop('Q_anlass',axis = 1)
# Join the encoded df
nn = nn.join(one_hot)

yy=nn.groupby(['product_id', 'Monat'], as_index=False).sum()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.layout = html.Div([
    html.Div(children='''
         Occasions Distribution for the top 10 products 
    ''', style={
        'textAlign': 'center',
        'font-weight': 'bold'
    }),

    html.Div([dcc.Graph(id='graph-with-slider')]),
    html.Div([html.Label(['Please choose a month']
                         )]),
    dcc.RangeSlider(
        id='year-slider',
        min=new_data['Monat'].min(),
        max=new_data['Monat'].max(),
        value=[8, 9],
        # marks={str(Month): str(Month) for Month in new_data['Monat'].unique()},
        marks={
            8: {'label': 'August', 'style': {'color': '#f50'}},
            9: {'label': 'September', 'style': {'color': '#f50'}},
            10: {'label': 'October', 'style': {'color': '#f50'}},
            11: {'label': 'November', 'style': {'color': '#f50'}}
        },
        step=1,

        updatemode='drag'

    )
])


@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('year-slider', 'value'))
def update_figure(selected_month):
    # filtered_df = fg[fg.Month == selected_year]
    filtered_df = yy[(yy['Monat'] >= selected_month[0]) & (yy['Monat'] <= selected_month[1])]

    # plotly setup
    fig = go.Figure()
    l = filtered_df.columns.drop(['product_id','Monat'])
    # add trace
    for col in l:
        # print(col)
        fig.add_trace(go.Bar(x=filtered_df['product_id'], y=filtered_df[col], name=col))

    # Change the bar mode
    fig.update_layout(barmode='group')

    fig.update_layout(transition_duration=1000)
    fig.update_layout(
        xaxis_tickfont_size=14,
        yaxis=dict(
            title='Number of users',
            titlefont_size=16,
            tickfont_size=14,
        ))

    return fig


if __name__ == '__main__':
    app.run_server(port=8072)