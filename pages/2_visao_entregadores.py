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

st.set_page_config( page_title='Visão Entregadores', layout='wide')

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

# Avaliação média por entregador
def mean_deliver(df1):
    avg_delivery = (df1.loc[:, ['Delivery_person_Ratings','Delivery_person_ID']]
                       .groupby('Delivery_person_ID')
                       .mean()
                       .reset_index())
    
    return avg_delivery

# Avalição Média e Desvio Padrão
def mean_std_ratings(df1):
    mean_std_ratings = ( df1.loc[:, ['Delivery_person_Ratings', 'Road_traffic_density' ]]
                            .groupby('Road_traffic_density')
                            .agg({'Delivery_person_Ratings': ('mean', 'std')}) )
    mean_std_ratings.columns = ['ratings_mean', 'ratings_std']
    mean_std_ratings = mean_std_ratings.reset_index()

    return mean_std_ratings

def mean_std_ratings_weather(df1):
    mean_std_ratings = ( df1.loc[:, ['Delivery_person_Ratings', 'Weatherconditions' ]]
                            .groupby('Weatherconditions')
                            .agg({'Delivery_person_Ratings': ('mean', 'std')}) )
    mean_std_ratings.columns = ['ratings_mean', 'ratings_std']
    mean_std_ratings = mean_std_ratings.reset_index()

    return mean_std_ratings
    
# Os tops entregadores
def top_delivers ( df1, top_asc ):
    df2 = (df1.loc[:, ['Delivery_person_ID', 'City', 'Time_taken(min)']]
              .groupby(['City', 'Delivery_person_ID'])
              .mean()
              .sort_values(['City' , 'Time_taken(min)'], ascending = top_asc)
              .reset_index())

    df_aux1 = df2.loc[df2['City'] == 'Metropolitian', :].head(10)
    df_aux2 = df2.loc[df2['City'] == 'Urban', :].head(10)
    df_aux3 = df2.loc[df2['City'] == 'Semi-Urban', :].head(10)

    df3 = pd.concat( [df_aux1, df_aux2, df_aux3] ).reset_index( drop=True ) 
            
    return df3

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

st.header('Marketplace - Visão Entregadores')

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

tab1, tab2, tab3 = st.tabs( ['Visão Gerencial', '_', '_'] )

with tab1:
    with st.container():
        st.subheader( 'Visão Geral' )
        
        col1, col2, col3, col4 = st.columns( 4, gap='large' )
        with col1:
            mais_novo = df1.loc[:, 'Delivery_person_Age'].min()
            col1.metric( 'Menor idade', mais_novo )
            
        with col2:
            mais_velho = df1.loc[:, 'Delivery_person_Age'].max()
            col2.metric('Maior idade', mais_velho )
            
        with col3:
            pior_veiculo = df1.loc[:, 'Vehicle_condition'].min()
            col3.metric('Pior condição de veículo', pior_veiculo)
            
        with col4:
            melhor_veiculo = df1.loc[:, 'Vehicle_condition'].max()
            col4.metric('Melhor condição de veículo', melhor_veiculo)

    with st.container():
        st.markdown( """---""" )
        st.subheader('Avaliações')
        
        col5, col6 = st.columns( 2, gap='large' )
        with col5:
            st.markdown( 'Avaliação média por entregador' )
            avg_delivery = mean_deliver( df1)
            st.dataframe( avg_delivery)
        
        with col6:
            st.markdown( 'Avaliação média e o desvio padrão por tipo de tráfego' )
            mean_std_ratings = mean_std_ratings( df1 )
            st.dataframe( mean_std_ratings )
            
            st.markdown( 'Avaliação média e o desvio padrão por condições climáticas' )
            mean_std_ratings = mean_std_ratings_weather( df1 )
            st.dataframe( mean_std_ratings )
    
    with st.container():
        st.markdown( """---""" )
        st.subheader('Top Entregadores')
        
        col7, col8 = st.columns( 2, gap='large' )
        with col7:
            st.markdown( 'Os 10 entregadores mais rápidos por cidade' )
            df3 = top_delivers ( df1, top_asc=True )
            st.dataframe( df3 ) 
            
        with col8:
            st.markdown( 'Os 10 entregadores mais lentos por cidade' )
            df3 = top_delivers ( df1, top_asc=False )
            st.dataframe( df3 ) 