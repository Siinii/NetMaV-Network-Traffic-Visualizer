import pandas as pd
import requests
import ipaddress
import plotly.graph_objs as go
import os



def buildFigure(dataframe, user_ip):
    api_key = os.getenv("SECRET_KEY")
    ipMap = {}
    cityMap = {}
    countryMap = {}
    homeCoordinates =(0,0)
    homeCity="Unknown"
    homeCountry="Unknown"


    max_width=8
    min_width=1

    def buildHomeStats(user_ip):
        nonlocal homeCoordinates
        nonlocal homeCity
        nonlocal homeCountry
        print("User IP is: ", user_ip)
        try:
            response = requests.get('https://api.ipgeolocation.io/ipgeo?apiKey=' + api_key + '&ip=' + str(user_ip)+ '&fields=latitude,longitude,city,country_name').json()
            homeCoordinates = (round(float(response.get("latitude")), 1), round(float(response.get("longitude")), 1))
            homeCity = response.get("city")
            homeCountry = response.get("country_name")
        except:
            return



    def get_color(row):
        #might want to change the gradient color to blue/yellow at some point
        in_percentage = row['Count'] / (row['Count'] + row['CountOut'])
        if in_percentage < .5:
            red=255
            green = 255* ((in_percentage)*2)
        else:
            green=255
            red=255 * (1-in_percentage)
        
        return 'rgb(' + str(red) + ', ' + str(green) + ', 0)'

    def get_count_out(row):
        try:
            return pair_counts[(pair_counts['Source_Coord'] == row['Dest_Coord']) & (pair_counts['Dest_Coord'] == row['Source_Coord'])]['Count'].values[0]
        except:
            return 0

    def map_source_to_coordinate(row, isSource):
        kw = 'Source' if isSource else 'Destination'
        if row[kw] in ipMap:
            return ipMap[row[kw]]
        else:
            try:
                if ipaddress.ip_address(row[kw]) in ipaddress.ip_network('10.0.0.0/8'):
                    ipMap[row[kw]] = homeCoordinates
                    cityMap[homeCoordinates] = homeCity
                    countryMap[homeCoordinates] = homeCountry
                else:
                    response = requests.get('https://api.ipgeolocation.io/ipgeo?apiKey=' + api_key + '&ip=' + str(row['Source'])+ '&fields=latitude,longitude,city,country_name').json()
                    ipMap[row[kw]] = (round(float(response.get("latitude")), 1), round(float(response.get("longitude")), 1))
                    cityMap[ipMap[row[kw]]] = response.get("city")
                    countryMap[ipMap[row[kw]]] = response.get("country_name")
            except:
                ipMap[row[kw]] = pd.NA
            return ipMap[row[kw]]

    def map_coord_to_city(row, isSource):
        kw = 'Source_Coord' if isSource else 'Dest_Coord'
        return cityMap[row[kw]]

    def map_coord_to_country(row, isSource):
        kw = 'Source_Coord' if isSource else 'Dest_Coord'
        return countryMap[row[kw]]


    def build_trace(row, home_port, max_count):
        if row['Source_Coord'] != home_port or row['Dest_Coord'] == pd.NA or row['Dest_Coord'] ==pd.NA or (row['Source_Coord'] == row['Dest_Coord']):
            return
        else:
            print(max(max_width * ((row['Count']+row['CountOut']) / max_count), min_width))
            fig.add_trace(go.Scattermapbox(
        lon=[row['Source_Coord'][1], row['Dest_Coord'][1]],  # Longitude values
        lat=[row['Source_Coord'][0], row['Dest_Coord'][0]],  # Latitude values
        mode="lines+markers",

        hovertemplate = f"{row['Dest_City']}, {row['Dest_Country']}<br>Packets From: {row['CountOut']}<br>Packets To: {row['Count']}<extra></extra>",
        name=f"{row['Dest_City']}, {row['Dest_Country']}",
        line=dict(width=max(max_width * ((row['Count']+row['CountOut']) / max_count), min_width), color=get_color(row)),  # Line properties (e.g., width and color)
        marker=dict(size=8, color=["purple", "brown"]),  # Marker properties
    ))

    
        

    df2 = dataframe
    buildHomeStats(user_ip)


    df2['Source_Coord'] = df2.apply(map_source_to_coordinate, args=(True, ), axis=1)
    df2['Dest_Coord'] = df2.apply(map_source_to_coordinate, args=(False, ), axis=1)

    df2 = df2.replace(("Not found", "Not found"), pd.NA)


    pair_counts = df2.groupby(['Source_Coord', 'Dest_Coord']).size().reset_index(name='Count')
    pair_counts['Source_City'] = pair_counts.apply(map_coord_to_city, args=(True, ), axis=1)
    pair_counts['Source_Country'] = pair_counts.apply(map_coord_to_country, args=(True, ), axis=1)
    pair_counts['Dest_City'] = pair_counts.apply(map_coord_to_city, args=(False, ), axis=1)
    pair_counts['Dest_Country'] = pair_counts.apply(map_coord_to_country, args=(False, ), axis=1)
    pair_counts['CountOut'] = pair_counts.apply(get_count_out, axis=1)

    home_port = pair_counts['Source_Coord'].mode(dropna=True)[0]
    max_count = (pair_counts['Count'] + pair_counts['CountOut']).max()


    fig = go.Figure(go.Scattermapbox(
        mode = "markers+lines",
        ))

    pair_counts.apply(build_trace,args=(home_port, max_count), axis=1)

    fig.update_layout(
        margin ={'l':0,'t':0,'b':0,'r':0},
        legend = dict(
            x=0,
            bgcolor='rgba(0,0,0,0)'
        ),
        mapbox = {
            'center': {'lon': 10, 'lat': 10},
            'style': "stamen-terrain",
            'center': {'lon': -20, 'lat': -20},
            'zoom': 1
        }
    )

    fig.add_layout_image(
        dict(
            source="/assets/NetMaV_Logo.jpg",
            xref="paper", yref="paper",
            x=1, y=1,
            sizex=0.2, sizey=0.2,
            xanchor="right", yanchor="top"
        )
    )

    return fig

