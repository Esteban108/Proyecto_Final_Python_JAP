from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import matplotlib.pyplot as plt
import numpy as np
import json
from reportlab.pdfgen import canvas
CONFIG=json.loads(open('config.json').read())
from datetime import datetime
import time 
"""COPIA LOCAL DE LA PLANILLA//CADA CIERTO TIEMPO UN LLAMADO PARA ACTUALIZAR, LLAMAR A FUNCIONES UNICAMENTE SI NO EXSISTEN LAS COSAS...//CADA CIERTO TIEMPO UN LLAMADO PARA ACTUALIZAR
Podria mejorar el manejo de las funciones y ese uso de llamado indiscriminado(....) a recursos pudiendo hacer una copia local y consultarla...."""

"""Se podria Dividir en distintos modulos y tambien separar en carpetas para mejorar la organizacion"""  
#___________________________________________________________________________________________________________#


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = json.loads(open('config.json').read())["google_credenciales"]
#APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def get_credentials():
    """"Obtiene credenciales de usuario válidas del almacenamiento.

    Si no se ha almacenado nada, o si las credenciales almacenadas no son válidas,
    el flujo OAuth2 se completa para obtener las nuevas credenciales.

    Devoluciones:
        Credenciales, la credencial obtenida.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def obtener_hoja():

    """obtiene la oja de la planilla"""
    credentials=get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
   
    spreadsheetId = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    rangeName = 'XXXXXXXXXXXXXXXXXXXXXX'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    return result
    

#_______________________________________LLAmados de _____________________________________________________________#

def resultado_csv():
    """Convierte a CSV de Excel la Planilla"""
    convertir_a_csv2(obtener_hoja().get("values",[]))


def obtener_microdatos(dic):
     """Obtiene los Microdatos dados lso filtros pasados por parametro"""
     planilla=obtener_hoja().get('values', [])


     return convertir_a_csv2(filtros2(dic,planilla))


def agregados(dic):
    dic_2={}
    
    planilla=obtener_hoja().get('values', [])
    for f in dic["aggregation"]:
        if(not f in CONFIG["config_servicio"]["aggregation"]):
                return(Response('Parametro invalido',400))
        else:
            if(f=="Genero"):
                if(not("aggregation" in dic_2.keys())):
                   dic_2["aggregation"]={}
                dic_2["aggregation"][f]=obtener_cantidad(planilla,3)
            else:
                if(not("aggregation" in dic_2.keys())):
                   dic_2["aggregation"]={}
                dic_2["aggregation"][f]=obtener_cantidad(planilla,5)
                 
        
    if("sentiment" in dic.keys()):
        a=False
        if(type(dic["sentiment"])==list):
            a=(dic["sentiment"][0] in CONFIG["config_servicio"]["sentiment"])
        else:
            a=dic["sentiment"] in CONFIG["config_servicio"]["sentiment"]
        
        if(a):
            dic_2["sentiment"]={}
            dic_2["sentiment"]['Si_conoce_JAP_opinion_que_posee']=obtener_sentimientos(planilla)

    
    return dic_2

#____________________________________________________________________________________________________#
def convertir_a_csv2(lista):
    """Dada una lista de Listas la convierte a CSV(de Excel)"""
    csv=""
    for e in lista:
        for e2 in e:
            csv=csv + '"' + str(e2) + '"' +  ";"
        csv=csv[:-1] + " \n "
	
    return csv

def filtros2(dic,planilla):
    """Dado un diccionario con filtros y la planilla con los datos devuelve la planilla filtrada"""
    keys=dic.keys()
    
    for filtro in  CONFIG["config_servicio"]["filters"]:
        
        if(filtro[0] in keys):
            
            planilla=filtrar_unf(filtro,planilla, dic)
            
       
    return planilla




def filtrar_unf(filtro,planilla, dic):
    """Dado un Filtro Filtra los datos"""
    planilla_aux=[]
    planilla_aux.append(planilla[0])
    
    for i in range(0,len(planilla)):
                if(i!=0):
                    if(filtro[0]=="Edad"):
                        planilla[i][filtro[1]]=  int(planilla[i][filtro[1]])#No es lo mas eficiente pero.../si practico
                        #if(fila planilla columna == un dato)/DAto de planilla igual dato?
                    if(planilla[i][filtro[1]]==dic[filtro[0]][0]):#dic[filtro[0]]= dic[Edad], dic["Genero"]
                        planilla_aux.append( planilla[i])

    return(planilla_aux)



def obtener_cantidad(planilla, indice_pregunta):
    """Obtiene una cantidad en porsentaje y numerica de una pregunta por su indice"""
    cantidad={}
    cant_total=0
    for i in range(1,len(planilla)):
        if(i!=0):
            una_respuesta=str(planilla[i][indice_pregunta])
                       
            if(una_respuesta in cantidad.keys()):
                cantidad[una_respuesta]+=1
                cant_total+=1
            else:
                cantidad[una_respuesta]=1
                cant_total+=1

    return {"cantidad":cantidad, "porsentaje":obtener_porsentaje(cantidad, cant_total)}

          
def obtener_porsentaje(dic, cant_total):
    """Obtiene el porsentaje de un Num"""
    dic_por={}
   
    for e in dic:
        dic_por[e]=dic[e]*100/cant_total
                   
    return dic_por


#_____________________________________________________________________________________________________________#


def obtener_columna(planilla,num_colum):
    """Obtiene unaa columna dado el numero de la coluimna y la planilla"""
    aux=[]
    for a in planilla:
        aux.append(a[num_colum])
    return aux

def obtener_respuestas_unicas(colum):
    """Obtiene las respuestas unicas de una columna"""
    aux=[]
    for respuesta in colum:
        if not (respuesta in aux):
            
            aux.append(respuesta)
    
    return aux
def obtener_cat_respuestas(respuestas,colum):
    aux=[]
    for a in respuestas:
            aux.append(0)

    for respuesta in colum:
            aux[respuestas.index(respuesta)]+=1
    return aux


        


def obtener_grafico_edades(guardar_como=".png"):#Tambien se puede guardar como .pdf//Aunque no esta implementado
    """Obtiene el grafico de Edades """
    planilla=obtener_hoja().get('values', [])
    todas_las_edades=obtener_columna(planilla,2)[1:]
    
    edades_unicas=obtener_respuestas_unicas(todas_las_edades)
    edades_unicas.sort()
    
    E=obtener_cat_respuestas(edades_unicas, todas_las_edades)
    
    posicion_y = np.arange(len(edades_unicas))
    plt.barh(posicion_y, E, align = "center")
    plt.yticks(posicion_y, edades_unicas)
    plt.xlabel('Cantidad de personas')
    plt.title("Gráfico de Edades")
    
    
    plt.savefig("GraficoEdades"  + guardar_como)
    


def obtener_grafico_conoce_JAP(guardar_como=".png"):
    """Obtiene el grafico de si conocen JAP"""
    planilla=obtener_hoja().get('values', [])
    todas_las_respuestas=obtener_columna(planilla,12)[1:]
    dic={"Sí":0,"No":0}
    
    for e in todas_las_respuestas:
        
        if(e=="No"):
            
                dic["No"]+=1
        else:
            
                dic["Sí"]+=1
            
    
    dic_por=obtener_porsentaje(dic,len( todas_las_respuestas))
    plt.pie([dic_por["Sí"],dic_por["No"]],explode=(0,0.05),labels=["Sí","No"], autopct='%1.1f%%',shadow=True)
    plt.title("Conocen Jovenes a Programar")
    
    plt.savefig("GraficoEdades"  + guardar_como)


def obtener_grafico_genero(guardar_como=".png"):
    """Obtiene el grafico del Genero de las personas encuestadas"""
    planilla=obtener_hoja().get('values', [])
    todas_las_respuestas=obtener_columna(planilla,3)[1:]
    dic={"Hombre":0,"Mujer":0, "Otro": 0}
    for e in todas_las_respuestas:
        if(e=="Hombre"):
           dic["Hombre"]+=1
        elif(e=="Mujer"):
            dic["Mujer"]+=1
        else:
            dic["Otro"]+=1
    dic_por=obtener_porsentaje(dic,len( todas_las_respuestas))
    plt.pie([dic_por["Hombre"],dic_por["Mujer"],dic_por["Otro"]],explode=(0,0.05,0.05),labels=["Masculino","Femenino","Otro"], autopct='%1.1f%%',shadow=True)
    plt.title("Gráfico de Género")
    if(guardar_como!=".png"):
        plt.savefig("GraficoGenero.pdf")
    else:
        plt.savefig("GraficoGenero.png")
        
        
def obtener_grafico_nivel_educativo(guardar_como=".png"):
    """Obtiene el grafico del Nivel Educativo de las personas encuestadas"""
    planilla=obtener_hoja().get('values', [])
    todas_las_respuestas=obtener_columna(planilla,5)[1:]
    respuestas_unicas=obtener_respuestas_unicas(todas_las_respuestas)#Solo van a ser primara, secundaria...//Pero no quiero fijarme como esta escrito
    R=obtener_cat_respuestas(respuestas_unicas, todas_las_respuestas)
    X = np.arange(len(respuestas_unicas))
   
    plt.bar(X,R, color="b")
    
    plt.xticks(X, ["Univiersitaria","Terciaria","Secundaria","Primaria"])
    plt.title("Gráfico de nivel educativo")
    if(guardar_como!=".png"):
        plt.savefig("GraficoNivelEducativo.pdf")
    else:
        plt.savefig("GraficoNivelEducativo.png")
        
def obtener_cantidad_de_encuestados():
    """Obtiene la Cantidad de Encuestados"""
    return(str( len(obtener_hoja().get('values', []))-1))
    
 #XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#
def dibujar_pdf():
    """Dibuja un archivo PDF dados todos los graficos y unos textos//Cabe destacar que tienen que existir los grafiscos si no da Error"""
    try:
        c=canvas.Canvas("Reporte.pdf")
        c.drawString(20,800,"Jovenes a Programar Grupo 33")
        c.drawString(525,800,time.strftime("%d/%m/%y",datetime.now().timetuple()))
        c.drawString(450,35,"Esteban Gaudenti 2017")
        c.line(0,795,600,795)
        c.drawString(20,750,"Cantidad de Encuestados:   "+ obtener_cantidad_de_encuestados())#Demasiadas llamadas a la planilla.....
        c.drawImage("graficoEdades.png",300,450,width=320,height=240,preserveAspectRatio=True)
        c.drawImage("GraficoGenero.png",-10,450,width=320,height=240,preserveAspectRatio=True)
        c.drawString(240,700,"Edad de los encuestados:")
        c.drawString(20,700,"Género de los encuestados:")
        c.drawString(20,400,"Nivel educativo:")
        c.drawImage("GraficoNivelEducativo.png",-10,150,width=320,height=240,preserveAspectRatio=True)
        c.drawString(240,400,"Conocen JAP los encuestados:")
        c.drawImage("GraficoConocenJAP.png",300,150,width=320,height=240,preserveAspectRatio=True)
        c.line(0,50,600,50)
        c.save()
        
    except OSError as ex:
        aux=ex.args[0][ex.args[0].index('"'):]#Podria definir el nombre de las funciones como parte del nombre de los archivos y ahorraria este monton de ifs
        if(aux=='"graficoEdades.png"'):
            obtener_grafico_edades()
        elif(aux=='"graficoGenero.png"'):
            obtener_grafico_genero()
        elif(aux=='"GraficoNivelEducativo.png"'):
            obtener_grafico_nivel_educativo()
            
        else:
            obtener_grafico_conoce_JAP()
        
        dibujar_pdf()#Esto se puede repetir 4 veces....//OSError se produce por otra causa ? 
            
            
            
    

#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#
def obtener_sentimientos(planilla):
    """Dada la planilla obtiene los sentimientos de La unica pregunta que se requiere(POR LETRA) """
    natural_language_understanding = NaturalLanguageUnderstandingV1(version='2017-02-27',username=CONFIG["natural_language_credenciales"]["username"],password=CONFIG["natural_language_credenciales"]["password"])
    dic={ "positivo":0 ,"negativo":0, "neutro":0}
    for i in range(1,len(planilla)):
        
        una_respuesta=planilla[i]
        
        if(len(planilla[i])>14):
            una_respuesta=una_respuesta[14]
            
            if(una_respuesta != "" and una_respuesta != None and len(una_respuesta)>=15):#No se si viene como None o como "" si no existe...//15 es el largo minimo que acepta
                try:
                    r = natural_language_understanding.analyze(text=una_respuesta,features=Features(sentiment=SentimentOptions()))#No hay suficiente texto para reconocer el lenguaje
                    sentimiento=r["sentiment"]["document"]["label"]
                    if(sentimiento == "positive"):
                       dic["positivo"]+=1
                    elif(sentimiento =="negative"):
                       dic["negativo"]+=1
                    else:
                       dic["neutro"]+=1


                except watson_developer_cloud.watson_service.WatsonApiException :
                    pass
    return dic


#___________________________________________________________________________________________________________________________________#

