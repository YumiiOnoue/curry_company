# ================================
# Importando Bibliotecas
# ================================

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import folium
from streamlit_folium import folium_static
from haversine import haversine
from PIL import Image

st.set_page_config( page_title='Visão Restaurantes', layout='wide')

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

# Distância média das entregas            
def avg_delivery( df1 ):
    cols = ['Restaurant_latitude', 'Restaurant_longitude', 'Delivery_location_latitude', 'Delivery_location_longitude']
    df1['distance'] = (df1.loc[:, cols].apply( lambda x: 
                                               haversine(
                                                   (x['Restaurant_latitude'], x['Restaurant_longitude']),
                                                   (x['Delivery_location_latitude'], x['Delivery_location_longitude'])), axis=1))
    avg_distance = np.round(df1['distance'].mean(),2)
    
    return avg_distance

# Cálculo da média e mediana das entregas com festival e sem festival
def avg_std_delivery(df1, Festival, op):
    df_aux = ( df1.loc[: , ['Time_taken(min)', 'Festival'] ]
                  .groupby('Festival')
                  .agg( {'Time_taken(min)': ['mean','std'] } ) )

    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()
    linhas_selecionadas = df_aux['Festival'] == Festival
    df_aux = np.round(df_aux.loc[ linhas_selecionadas , op], 2)
    
    return df_aux

# Tempo de espera por cidade
def waiting_time( df1 ):
    df_aux = df1.loc[: , ['Time_taken(min)','City']].groupby('City').agg( { 'Time_taken(min)': ['mean', 'std'] }  )
    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()

    fig = go.Figure()
    fig.add_trace( go.Bar( name='Control', x=df_aux['City'], y=df_aux['avg_time'], error_y=dict(type='data', array=df_aux['std_time'] ) ) )

    fig.update_layout(barmode='group')            
    
    return fig

# Tempo médio de entrega por cidade
def waiting_time_city( df1 ):
    cols = ['Restaurant_latitude', 'Restaurant_longitude', 'Delivery_location_latitude', 'Delivery_location_longitude']
    df1['distance'] = (df1.loc[:, cols].apply( lambda x: 
                                              haversine( (x['Restaurant_latitude'], x['Restaurant_longitude']),
                                                         (x['Delivery_location_latitude'], x['Delivery_location_longitude'])), axis=1))

    avg_distance = df1.loc[:, ['City', 'distance']].groupby( 'City' ).mean().reset_index()

    fig = go.Figure( data = [ go.Pie( labels = avg_distance['City'], values=avg_distance['distance'], pull=[0, 0.1, 0] ) ] )
    
    return fig

# Tempo de entrega por cidade e tipo de tráfego
def waiting_time_city_traffic( df1 ):
    df_aux = ( df1.loc[: , ['Time_taken(min)', 'City', 'Road_traffic_density']]
                  .groupby(['City', 'Road_traffic_density'])
                  .agg({'Time_taken(min)' : ['mean', 'std']}) )

    df_aux.columns = ['avg_time', 'std_time']

    df_aux = df_aux.reset_index()

    fig = px.sunburst(df_aux, path = ['City', 'Road_traffic_density'], values = 'avg_time', 
                      color = 'std_time', color_continuous_scale = 'RdBu', 
                      color_continuous_midpoint=np.average(df_aux['std_time'] ) )
    return fig


# Tempo de entrega por cidade e tipo de pedido
def waiting_time_city_typeorder( df1 ):
    delivery_time = ( df1.loc[: , ['Time_taken(min)','City', 'Type_of_order']]
                         .groupby(['City', 'Type_of_order'])
                         .agg( {'Time_taken(min)':['mean', 'std']}) )
    delivery_time.columns = ['avg_time', 'std_time']
    delivery_time = np.round(delivery_time.reset_index(), 2)

    return delivery_time

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

st.header('Marketplace - Visão Restaurantes')

# ======= Sidebar ====================

#image_path = '/Users/User/Documents/CDS/koi.png'
image = Image.open('koi.png')
st.sidebar.image(image, width=80)

st.sidebar.markdown( '# Curry Company' )
st.sidebar.markdown( '## Fastest Delivery in Town' )
st.sidebar.markdown( """---""" )

# Filtro de data
st.sidebar.markdown( '## Selecione uma data limite' )

date_slider = st.sidebar.slider(
    'Até qual valor?',
    value=pd.datetime(2022, 4, 13),
    min_value=pd.datetime(2022, 2, 11),
    max_value=pd.datetime(2022, 4, 6),
    format='DD-MM-YYYY')

linhas_selecionadas = df1['Order_Date'] < date_slider
df1 = df1.loc[linhas_selecionadas, :]

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
        st.subheader( 'Métricas Gerais' )
        
        col1, col2 = st.columns( 2 )
        
        with col1:
            entregadores = len(df['Delivery_person_ID'].unique())
            col1.metric( 'Entregadores únicos', entregadores )
        
        with col2:
            avg_distance = avg_delivery( df1 )
            col2.metric('Distância média das entregas', avg_distance)
            
    with st.container():
        st.subheader( 'Tempo relacionado aos Festivais')
    
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            df_aux = avg_std_delivery( df1, 'Yes', 'avg_time' )
            col3.metric( 'Média c/ Festival', df_aux )
            
        with col4:
            df_aux = avg_std_delivery( df1, 'Yes', 'std_time' )
            col4.metric( 'DP c/ Festival', df_aux )
            
        with col5:
            df_aux = avg_std_delivery( df1, 'No', 'avg_time' )
            col5.metric( 'Média s/ Festival', df_aux )
            
        with col6:
            df_aux = avg_std_delivery( df1, 'No', 'std_time' )
            col6.metric( 'DP s/ Festival', df_aux )    
    
    with st.container():
        st.markdown( """---""" )

        st.subheader('Tempo de entrega por cidade')
        fig = waiting_time( df1 )
        st.plotly_chart( fig )        
            
    with st.container():
        st.markdown( """---""" )
        st.subheader( 'Distribuição do Tempo' )
    
        col7, col8 = st.columns( 2 )
        
        with col7:
            st.markdown('Tempo médio de entrega por cidade')
            fig = waiting_time_city( df1 )
            st.plotly_chart( fig )
   
        with col8:
            st.markdown('Tempo de entrega por cidade e tipo de tráfego')
            fig = waiting_time_city_traffic( df1 )
            st.plotly_chart( fig )
            
    with st.container():
        st.markdown( """---""" )
        st.subheader( 'Tempo de entrega por cidade e tipo de pedido' )
        delivery_time = waiting_time_city_typeorder( df1 )
        st.dataframe( delivery_time )