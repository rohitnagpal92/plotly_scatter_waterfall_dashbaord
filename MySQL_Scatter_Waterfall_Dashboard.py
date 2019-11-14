# -*- coding: utf-8 -*-
"""
Created on Sun Sep  1 20:34:01 2019

@author: rohti
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Apr 29 21:09:07 2018

@author: Rohit Nagpal
"""
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import numpy as np
import mysql.connector
from mysql.connector import Error

#checking if the DB exists 
strDBName="MyDB"
strTableName="demo_data"

try:
    connection = mysql.connector.connect(host='localhost',
                                         database=strDBName,
                                         user='root',
                                         password='password')
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("Your connected to database: ", record)
except Error as e:
    print("Error while connecting to MySQL", e)

df2 = pd.DataFrame()

app = dash.Dash()

df = pd.read_csv('../Waterfall/waterfall_config_mysql.csv')

measures = []
for fields in df['WF Measure']:
    measures.append({'label':fields,'value':fields})

group_by = []
dimensions = ['Customer','Customer Grouped','Channel','Product Line','Product Name','Region','Country']
for dim in dimensions:
    group_by.append({'label':dim,'value':dim})
    
wf_levels = []
for lvl in df['WF Level Min'].unique():
    wf_levels.append({'label':str(lvl),'value':lvl})


app.layout = html.Div([
                html.H1('Scatter and Waterfall Dashboard'),
                html.H2('Select Group By',style={'width':'20%','display':'inline-block'}),
                html.H2('Select Color By',style={'width':'20%','display':'inline-block'}),
                html.H2('X Axis Measure',style={'width':'20%','display':'inline-block'}),
                html.H2('Y Axis Measure',style={'width':'20%','display':'inline-block'}),
                html.H2('Waterfall Level',style={'width':'20%','display':'inline-block'}),
                
                html.Div([ dcc.Dropdown(id='group-by',options= group_by,value = 'Customer')
                        ],style={'width':'20%','display':'inline-block'}),
                html.Div([ dcc.Dropdown(id='group-by-color',options= group_by,value = 'Country')
                        ],style={'width':'20%','display':'inline-block'}),
                html.Div([ dcc.Dropdown(id='x-axis',options= measures,value = 'Gross Sales')
                        ],style={'width':'20%','display':'inline-block'}),
                html.Div([ dcc.Dropdown(id='y-axis',options= measures,value = 'Pocket Sales')
                        ],style={'width':'20%','display':'inline-block'}),
                html.Div([ dcc.Dropdown(id='wflevel',options= wf_levels,value = 0)
                        ],style={'width':'20%','display':'inline-block'}),        
        
                html.Div([dcc.Graph(id = 'Scatter-Graph')],
                          style={'width':'48%','display':'inline-block'}),
                
                html.Div([dcc.Graph(id = 'Waterfall-Graph')],
                          style={'width':'48%','float':'right','display':'inline-block'}) 
                
        ], style={'width':'100%','display':'inline-block'})

@app.callback(
                Output('Scatter-Graph','figure'),
                [Input('group-by','value'),Input('group-by-color','value'),Input('x-axis','value'),Input('y-axis','value')]
             )

def update_scatter(group_by_dim,group_by_color,x_axis,y_axis):
    
    traces = []
    df2 = pd.read_sql('SELECT `' + group_by_dim + '` ,`' + group_by_color +  '` ,SUM(`' + x_axis + '`) as `' + x_axis +'`, SUM(`'+ y_axis + '`) as `' + y_axis + '` FROM ' + strTableName + ' group by `' + group_by_dim + '`, `' + group_by_color + '`', con=connection)
    for country in df2[group_by_color].unique():
        traces.append( go.Scatter(
                                x = df2[df2[group_by_color]==country][x_axis], 
                                y = df2[df2[group_by_color]==country][y_axis],
                                text = country + "," + df2[df2[group_by_color]==country][group_by_dim],
                                mode = 'markers',
                                opacity = 0.7,
                                marker={'size': 10},
                                name = country
                                )
                     )
    return{
            'data' : traces,
            'layout' : go.Layout(title = 'Dynamic Scatter Chart',
                                 xaxis = {'title': x_axis},
                                 yaxis = {'title': y_axis},
                                 paper_bgcolor='rgba(245, 246, 249, 1)',
                                 plot_bgcolor='rgba(245, 246, 249, 1)',
                                 hovermode = 'closest'
                    )
            }
 
@app.callback(
                Output('Waterfall-Graph','figure'),
                [Input('group-by','value'),
                 Input('group-by-color','value'),
                 Input('Scatter-Graph','clickData'),
                 Input('wflevel','value')]
             )

def update_waterfall(group_by_dim, group_by_color, clickData, wf_level):
    v_index = clickData['points'][0]['text']
    
    y2 = []
    
    flg = []
    for n in df.index:
        if (wf_level <= df.loc[n]['WF Level Max'] or df.loc[n]['WF Level Max'] == -1) and wf_level >= df.loc[n]['WF Level Min'] :
            f = 1
        else:
            f = 0
        flg.append(f)
        
    df['flag'] = flg
    df_new = df[df['flag'] == 1]
    df_new = df_new.reset_index(drop=True)
            
    for wf_field in df_new['WF Measure']:
        strQuery= pd.read_sql('SELECT SUM(`' + wf_field + '`) as `' + wf_field +'` FROM ' + strDBName +'.' + strTableName + ' where `' + group_by_color + '` ' + '+'  + '\'' + ',' +  '\'' + '+'  + ' `'+ group_by_dim + '`  ='+  '\'' + v_index +'\'' , con=connection)
        
        
        print("Checking")
        print('SELECT SUM(`' + wf_field + '`) as `' + wf_field +'` FROM ' + strDBName +'.' + strTableName + ' where `' + group_by_color + '` ' + '+'  + '\'' + ',' +  '\'' + '+'  + ' `'+ group_by_dim + '`  ='+  '\'' + v_index +'\'')
        
        values = strQuery[wf_field][0]
        y2.append(values)
        
           
    df_new['values'] = y2
    print(y2)

    y1 = []
    val = 0
    for tic in df_new.index:
        for i in range(0,tic+1):
            if i == tic:
                if df_new.loc[i]['WF Bucket Type'] == "Total":
                    val = df_new.loc[i]['values']
                else:
                    val = val - df_new.loc[i]['values']
            else:
                if df_new.loc[i]['WF Bucket Type'] == "Total":
                    val = df_new.loc[i]['values']
                else:
                    val = val - df_new.loc[i]['values']
                    
        y1.append(val)
        val = 0
       
    df_new['values2'] = y1
    df_new['values3'] = np.where(df_new['WF Bucket Type']=="Total",0,df_new['values2'])
    
    ##Base
    trace0 = go.Bar(
                x = df_new['WF Measure'],
                y = df_new['values3'],
                marker=dict(color='rgba(1,1,1, 0.0)'),
                )
    #All Buckets
    trace1 = go.Bar(
                x = df_new['WF Measure'],
                y = df_new['values'],
                marker=dict(color='rgba(55, 128, 191, 1.0)'),
                )
    data = [trace0,trace1]
    
    return{
            'data' : data,
            'layout' : go.Layout(
                                    title= 'Waterfall',
                                    barmode='stack',
                                    paper_bgcolor='rgba(245, 246, 249, 1)',
                                    plot_bgcolor='rgba(245, 246, 249, 1)',
                                    showlegend=False
                                    )
            
            
            }
    
if __name__ == '__main__':
    app.run_server()
