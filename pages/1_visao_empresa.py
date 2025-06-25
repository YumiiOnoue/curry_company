# ================================
# Importando Bibliotecas
# ================================

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import folium
import datetime
from streamlit_folium import folium_static
from haversine import haversine
from PIL import Image

st.set_page_config( page_title='Visão Empresa', layout='wide')

# ===============================
# Funções
# ===============================
def clean_code( df1 ):
    """
        Esta função tem a responsabilidade de limpar o dataframe
        
        Tipos de limpeza:
        1. Remoção dos NaN
        2. Mudança do tipo da coluna de dados
        3. Remoção dos espaços das variáveis texto
        4. Formatação da coluna de data
        5. Limpeza da coluna de tempo (remoção do texto da variável numérica)
        
        Input: Dataframe
        Output: Dataframe
    """
    
    # Removendo os espaços depois das strings. 
    df1.loc[ : , 'ID'] = df1.loc[ : , 'ID'].str.strip()
    df1.loc[ : , 'Road_traffic_density'] = df1.loc[ : , 'Road_traffic_density'].str.strip()
    df1.loc[ : , 'Type_of_order'] = df1.loc[ : , 'Type_of_order'].str.strip()
    df1.loc[ : , 'Type_of_vehicle'] = df1.loc[ : , 'Type_of_vehicle'].str.strip()
    df1.loc[ : , 'City'] = df1.loc[ : , 'City'].str.strip()
    df1.loc[ : , 'Festival'] = df1.loc[ : , 'Festival'].str.strip()

    # Excluindo as linhas vazias
    # 1. Delivery_person_Age
    linhas_selecionadas = df1['Delivery_person_Age'] != 'NaN '
    df1 = df1.loc[linhas_selecionadas, : ]

    # 2. Multiple_deliveries
    linhas_selecionadas = df1['multiple_deliveries'] != 'NaN '
    df1 = df1.loc[linhas_selecionadas, :]

    # 3. Road_traffic_density
    linhas_selecionadas = df1['Road_traffic_density'] != 'NaN'
    df1 = df1.loc[linhas_selecionadas, :]

    # 4. City
    linhas_selecionadas = df1['City'] != 'NaN'
    df1 = df1.loc[linhas_selecionadas, :]

    # 5. Festival
    linhas_selecionadas = df1['Festival'] != 'NaN'
    df1 = df1.loc[linhas_selecionadas, :]

    # 6. Time_taken(min)
    linhas_selecionadas = df1['Time_taken(min)'] != 'NaN'
    df1 = df1.loc[linhas_selecionadas, :]
    df1 = df1[df1['Time_taken(min)'].notnull()]

    # Comando para retirar o index como texto
    df1 = df1.reset_index( drop=True )

    # Convertendo string para números
    # 1. Delivery_person_Age
    df1['Delivery_person_Age'] = df1['Delivery_person_Age'].astype( int )

    # 2. Delivery_person_Ratings
    df1['Delivery_person_Ratings'] = df1['Delivery_person_Ratings'].astype( float )

    # 3. multiple_deliveries 
    df1['multiple_deliveries'] = df1['multiple_deliveries'].astype( int )

    # Conversao de texto para data
    df1['Order_Date'] = pd.to_datetime( df1['Order_Date'], format='%d-%m-%Y' )

    # Limpando a coluna de Time Taken
    df1['Time_taken(min)'] = df1['Time_taken(min)'].apply( lambda x: x.split( '(min) ')[1] )
    df1['Time_taken(min)'] = df1['Time_taken(min)'].astype( int )

    return df1

def order_metric( df1 ):
    df_aux = df1.loc[:, ['ID', 'Order_Date']].groupby('Order_Date').count().reset_index()
    fig = px.bar(df_aux, x='Order_Date', y='ID')
    return fig
                 
def traffic_order_share( df1 ):
    df_aux = ( df1.loc[:, ['ID','Road_traffic_density']]
                  .groupby('Road_traffic_density')
                  .count()
                  .reset_index() )
    df_aux[ 'perc_ID'] = 100* (df_aux['ID']/df_aux['ID'].sum())
    fig = px.pie(df_aux, values = 'perc_ID', names = 'Road_traffic_density')            
    return fig 

def traffic_order_city ( df1 ):
    df_aux = ( df1.loc[:, ['ID', 'City', 'Road_traffic_density']]
                  .groupby(['City', 'Road_traffic_density'])
                  .count()
                  .reset_index() )
    fig = px.scatter(df_aux, x = 'City', y = 'Road_traffic_density', size = 'ID')
    return fig

def order_by_week( df1 ):
    df1['week_of_year'] = df1['Order_Date'].dt.strftime('%U')
    df_aux = ( df1.loc[:, ['ID', 'week_of_year']]
                  .groupby('week_of_year')
                  .count()
                  .reset_index() )
    fig = px.line(df_aux, x = 'week_of_year', y = 'ID')
    return fig

def order_share_by_week( df1 ):
    df_aux1 = ( df1.loc[:, ['ID', 'week_of_year']]
                   .groupby( 'week_of_year' )
                   .count()
                   .reset_index() )
    df_aux2 = ( df1.loc[:, ['Delivery_person_ID', 'week_of_year']]
                   .groupby( 'week_of_year')
                   .nunique()
                   .reset_index() )
    df_aux = pd.merge( df_aux1, df_aux2, how = 'inner' )
    df_aux['order_by_delivery'] = df_aux['ID'] / df_aux['Delivery_person_ID']
    fig = px.line( df_aux, x = 'week_of_year', y = 'order_by_delivery' )    
    return fig

def country_maps( df1 ):
    data_plot = ( df1.loc[:, ['City', 'Road_traffic_density', 'Delivery_location_latitude', 'Delivery_location_longitude']]
                     .groupby( ['City', 'Road_traffic_density'])
                     .median()
                     .reset_index() )

    # Desenhar o mapa
    map = folium.Map( zoom_start=11 )

    for index, location_info in data_plot.iterrows():
        folium.Marker( [location_info['Delivery_location_latitude'],
                      location_info['Delivery_location_longitude']],
                      popup = location_info[['City', 'Road_traffic_density']] ).add_to( map )
    folium_static(map, width=1024, height=600)

# ------------------- Início da Estrutura Lógica do Código --------------------------

# ================================
# Carregando os dados 
# ================================

df = pd.read_csv('dataset/train.csv')

df1 = df.copy()

# ================================
# Limpando os dados
# ================================

df1 = clean_code( df1 )

# ======================================
# Streamlit
# ======================================

st.header('Marketplace - Visão Empresa')

# ======= Sidebar ====================

st.sidebar.markdown( '# Curry Company' )
st.sidebar.markdown( '## Fastest Delivery in Town' )
st.sidebar.markdown( """---""" )

# Filtro de data
st.sidebar.markdown( '## Selecione uma data limite' )

date_slider = st.sidebar.slider(
    'Até qual valor?',
    value=datetime.datetime(2022, 4, 6),
    min_value=datetime.datetime(2022, 2, 11),
    max_value=datetime.datetime(2022, 4, 13),
    format='DD-MM-YYYY'
)

date_slider = pd.to_datetime(date_slider)
df1 = df1[df1['Order_Date'] < date_slider]

st.sidebar.markdown( """---""" )

traffic_options = st.sidebar.multiselect(
    'Quais as condições do trânsito?',
    ['Low', 'Medium', 'High', 'Jam'],
    default=['Low', 'Medium', 'High', 'Jam'])

linhas_selecionadas = df1['Road_traffic_density'].isin(traffic_options)
df1 = df1.loc[linhas_selecionadas, :]

df1 = df1.loc[linhas_selecionadas, :]

st.sidebar.markdown( """---""" )
st.sidebar.markdown( '### Powered by Comunidade DS' )

# ============= Layout no Streamlit ===============

tab1, tab2, tab3 = st.tabs(['Visão Gerencial', 'Visão Tático', 'Visão Geográfico'])

with tab1:
    with st.container():
        st.subheader('Pedidos')

        st.markdown('Pedidos por Dia')
        fig = order_metric( df1 )
        st.plotly_chart(fig, use_container_width=True)
              
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            
            st.markdown('Pedidos por tipo de tráfego')
            fig = traffic_order_share( df1 )
            st.plotly_chart(fig, use_container_width=True)            
 
        with col2:
           
            st.markdown('Pedidos por cidade e tipo de tráfego')
            fig = traffic_order_city( df1)
            st.plotly_chart(fig, use_container_width=True)   

with tab2:
    st.subheader('Análise por semana')
    with st.container():        
    
        st.markdown('Pedidos por semana')
        fig = order_by_week( df1 )
        st.plotly_chart(fig, use_container_width=True)
    
    with st.container():
        
        st.markdown('Pedidos por entregador por semana')
        fig = order_share_by_week( df1 )
        st.plotly_chart(fig, use_container_width=True)        
    
with tab3:

    st.subheader('A localização central de cada cidade por tipo de tráfego')
    country_maps( df1 )