# -*- coding: utf-8 -*-
import eel
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

pd.options.mode.chained_assignment = None

# Inicia eel app
eel.init('app') 

####################  INPUTS  ####################

@eel.expose
def retorna_Regiao(region):
    return str(region)

@eel.expose
def retorna_TCV(tcv):
    return float(tcv)

@eel.expose
def retorna_TERM(term):
    return int(term)

@eel.expose
def retorna_NET_DAY(net_days):
    return int(net_days)

@eel.expose
def retorna_RBD(rbd):
    return float(rbd)

@eel.expose
def retorna_Dia_Mes_Ano(date):
    date = str(date)
    mes, dia, ano = date.split("-")
    return int(dia), int(mes), int(ano)    # retorna tupla : [0]=dia, [1]=mes, [2]=ano, 


####################  CÁLCULOS INTERNOS  ####################

@eel.expose
def parcelas_IBM_PRINT(tcv, term):
    parcelas = retorna_TCV(tcv) / retorna_TERM(term)
    return '${:20,.2f}'.format(parcelas)

def parcelas_IBM(tcv, term):
    return retorna_TCV(tcv) / retorna_TERM(term)

@eel.expose
def parcelas_IGF(tcv, rbd, term):
    return ((retorna_TCV(tcv)*-retorna_RBD(rbd)) + retorna_TCV(tcv))/retorna_TERM(term)

@eel.expose
def n_Mora(net_days):
    return retorna_NET_DAY(net_days) // 30

@eel.expose
def meses_Pagamento(term, net_days):
    return retorna_TERM(term) + n_Mora(net_days)

@eel.expose
def tcv_menos_rbd(tcv, rbd):
    return (retorna_TCV(tcv)*-retorna_RBD(rbd)) + retorna_TCV(tcv)


####################  TABELA HISTÓRICA  ####################



#Função filtrará tabela historica de acordo com o ano anterior do contrato
@eel.expose
def ano_Anterior_do_Contrato(date):
    ano = retorna_Dia_Mes_Ano(date)[2]
    return int(ano-1)

@eel.expose
def tabela_Historica(region, date):
    base = pd.read_csv(resource_path('app/dados.csv'), sep=',') #Carrega base histórica
    
    base.columns = base.columns.str.replace(' ', '') #Remove espaços brancos no header
    

    # Filtra Região do Contrato
    base = base.query(f'region == "{retorna_Regiao(region)}"')

    # Filtra Ano Anterior ao Contrato
    base['date'] = pd.DatetimeIndex(base['date']) # FIX IT - remover warning...
    base = base.set_index('date') # Transforma DataFrame em Series Temporal   
    base = base[f'{ano_Anterior_do_Contrato(date)}']

    base = base.drop(['year','quarter'], axis=1)
    
    return base # [region, ar, revenue]



####################  TABELA PRINCIPAL  ####################


@eel.expose
def tabela_Principal(tcv, term, net_days, rbd, date, region):

    # COLUNA IBM AR
    ibm_ar = list()
    for n in range(meses_Pagamento(term, net_days)):
            ibm_ar.append(parcelas_IBM(tcv, term))

    # COLUNA IBM REV
    ibm_rev = list()
    for n in range(n_Mora(net_days)):
        ibm_rev.append(0)
    for n in range(meses_Pagamento(term, net_days)):
        ibm_rev.append(parcelas_IBM(tcv, term))

    # COLUNA IGF AR
    igf_ar = list()
    for n in range(len(ibm_rev)):
        igf_ar.append(0)

    # COLUNA IGF REV
    igf_rev = list()
    for n in range(meses_Pagamento(term, net_days)):
        igf_rev.append(parcelas_IGF(tcv, rbd, term))

    # Pandas DataFrame
    coluna_Data = pd.date_range(start = f'{retorna_Dia_Mes_Ano(date)[1]}-01-{retorna_Dia_Mes_Ano(date)[2]}', periods=meses_Pagamento(term, net_days), freq='M')
    data_tuples = list(zip(coluna_Data, ibm_ar, ibm_rev, igf_ar, igf_rev))
    df = pd.DataFrame(data_tuples, columns=['date','ibm_ar','ibm_rev','igf_ar','igf_rev'])
    df = df.set_index('date')

    #Quater Resample
    df = df.resample('Q').sum()
    
    # Quarter Updates
    Q1_Update = df[df.index.quarter.isin([1])] + [float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([1])]['ar'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([1])]['revenue'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([1])]['ar'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([1])]['revenue'][0])]
    Q2_Update = df[df.index.quarter.isin([2])] + [float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([2])]['ar'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([2])]['revenue'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([2])]['ar'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([2])]['revenue'][0])]
    Q3_Update = df[df.index.quarter.isin([3])] + [float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([3])]['ar'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([3])]['revenue'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([3])]['ar'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([3])]['revenue'][0])]
    Q4_Update = df[df.index.quarter.isin([4])] + [float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([4])]['ar'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([4])]['revenue'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([4])]['ar'][0]), float(tabela_Historica(region, date)[tabela_Historica(region, date).index.quarter.isin([4])]['revenue'][0])]

    # df Update
    df.update(Q1_Update)
    df.update(Q2_Update)
    df.update(Q3_Update)
    df.update(Q4_Update)
    

    df['DSO_IBM'] = ((df['ibm_ar']/df['ibm_rev'])*90).astype(float)
    df['DSO_IGF'] = ((df['igf_ar']/df['igf_rev'])*90).astype(float)
    df['DSO_DELTA'] = (df['DSO_IBM'] - df['DSO_IGF']).astype(float)

    # Currency format
    pd.options.display.float_format = '{:,}'.format
    # Diminui casas decimais
    df = df.round(2)

    DSO_IBM_Media = df['DSO_IBM'].mean()
    DSO_IGF_Media = df['DSO_IGF'].mean()
    
    return '{:.2f}'.format(DSO_IBM_Media), '{:.2f}'.format(DSO_IGF_Media)


    
####################  PYINSTALLER  ####################
    
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)    #Necessário p/ PyInstaller achar o caminho do arquivo


'''----------------------------------------------------------------------------------------'''



#Eel starter

eel.start('index.html', block=False, size=(900, 600)) #eel initiate
while True: #needed for eel functionality, see doc.
    eel.sleep(1.0)

