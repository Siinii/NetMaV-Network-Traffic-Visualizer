import dash
from dash import dcc

from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import base64
import io
from figBuilder import *
from flask import request

app = dash.Dash(__name__)

# Define the layout of your app
app.layout = html.Div([
    html.Link(
        rel='stylesheet',
        href='https://fonts.googleapis.com/css?family=Roboto'
    ),
  
    html.Link(
        rel='stylesheet',
        href='/assets/styles.css'  # Path to your CSS file
    ),
    html.Link(rel='icon', href='/assets/favicon.ico'),


    # html.Div([
    #     html.H1("Upload a CSV File"),
    # ], className='header'),

    html.Div([
        html.Img(
            src='/assets/NetMaV_Logo.png',  # Path to your logo image
            style={
                'width' : '20%',
                'height': '20%',  # Adjust the height as needed
            },
        ),
    ], id= "mapLogo", className='logo'),
    html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or Select a CSV File'
        ], style = {
            'font-size': '22px',
            'font-weight': 'bold'
        }),
        className='upload-button large',
        multiple=False  # Allow only one file to be uploaded at a time
    ),
    ]),

     html.Div([
        html.Div([
            html.H2("Welcome to NetMaV, the network traffic visualizer!"),
            html.P(["To get started, either upload an existing network capture in the form of a CSV file, or start a new capture using your preferred tool (WireShark, Microsoft Network Monitor, tshark, etc) and export it to CSV.", html.Br(), "NetMaV will process your network capture file, and plot your traffic on an easy-to-understand map."]),
            html.P("With NetMaV, you can:"),
            html.Ul([
                html.Li("Easily see where your traffic is coming from and going to"),
                html.Li("Visualize the volume of your traffic"),
                html.Li("Catch any suspicious or unexpected connections"),
            ]),
            html.P("Map Legend:"),
            html.Ul([
                html.Li("lines connect traffic sources and destinations. The thicker the line, the more total traffic there was."),
                html.Li("line colors represent the ratio of packets sent to location vs received from location. The greener the line, the higher the ratio of packets sent to received."),
                html.Li("Hovering over a marker will display the marker's location, as well as the volume of packets sent and received"),
            ]),
        ], id='intro-text', className='introduction-text'),
    ]),

    
    dcc.Loading(
        id="loading-map",
        type="default",  # You can change the loading spinner style here
        children=[html.Div([dcc.Graph(id='map', className='invis map-container', responsive=True) ]
        #, className='invisible-button', id= 'map-box'
        # ,style = {'display': 'none'}
        )],
        fullscreen=True,  # Show the loading spinner over the whole page
    ),
],)

# Define callback to update the map
@app.callback(
    [Output('map', 'figure'),
    Output('map', 'className'),
    Output('intro-text', 'className'),
    Output('upload-data', 'className'),
    Output('mapLogo', 'className')],
    Input('upload-data', 'contents'),
    prevent_initial_call=True
)
def update_map(contents):
    if contents is None:
        return {}
    else:
        # Read the uploaded CSV file

        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        #validate this later
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        user_ip = request.remote_addr
        print("user ip is: ", user_ip)

        # Create the Plotly map
        fig = buildFigure(df, str(user_ip))
        return fig, 'vis map-container', 'invis intro-text', 'invis upload-button large', 'invis logo'

# @app.callback(
#     Output('map', 'style'),
#     Input('upload-data', 'contents')
# )
# def update_style(contents):
#     # ...
#     print("entered update_style")
#     return {'display': 'flex', 'width':'100%', 'height': '100%'}

if __name__ == '__main__':
    app.run_server(debug=True)
