from flask import Flask

from functools import wraps
from flask import request, Response
from flask import g
from datetime import datetime
from flask import request
from flask import send_file
#___________________________________________#
from conexion_BD import  ConexionBD
#_________________________________________#

from conexion_sheld import resultado_csv,obtener_microdatos,agregados

import conexion_sheld
#________________________________________________#


import json
import time
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import  Features,SentimentOptions
import watson_developer_cloud


CONFIG=json.loads(open('config.json').read())
"""Planilla--> ///Seria mejor realizar una copia local de la planilla para realizar menos llamados a esta"""

"""Podria mejorarse conexion_sheld para crear una clase que probea dichas funciones y realizar menos import"""

#___________________________________________#

class App_flask(Flask):
    """Realiza parte de la logica de la App"""
    def __init__(self, import_name):
        super().__init__(import_name)
        
    def check_auth(self,username, password):
        
        
        for usuario in CONFIG["user_list"]:
            if(usuario["user"]==username):
                return(usuario["pass"]==password)
                    
        return (False)

    def authenticate(self):
        """Sends a 401 response that enables basic auth"""
        return Response(
        'necesita credenciales validas para este recurso', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

    def requires_auth(self,f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not self.check_auth(auth.username, auth.password):
                return self.authenticate()
            return f(*args, **kwargs)
        return decorated
    
    def credenciales_validas(self,f):
        @wraps(f)
        def decorated(*args, **kwargs):
            usu= request.authorization["username"]
            for usuario in CONFIG["user_list"]:
                if(usuario["user"]==usu):
                    if(request.path[1:] in usuario["roles"]):
                        return f(*args, **kwargs)
            return Response('Sus credenciales no son validas para este recurso',400)
        return decorated




##_____________________________________________________________#


    
app=App_flask(__name__)
Mongo_Cli= ConexionBD(CONFIG["mongo_uri"])

@app.route('/resultados_csv')
def pagina_planilla():
    return resultado_csv()

@app.route("/logs")
@app.requires_auth
@app.credenciales_validas
def logs():
   
    
        return json.dumps(logs)
    


@app.route("/microdatos")
@app.requires_auth
@app.credenciales_validas
def microdatos():
    dic=dict(request.args)
    
   
    
   
    for f in dic:
        
        if(comprobar(f)):
            return(Response('Filtro invalido',400))
        else:
            
            if(f=="Edad"):
                
                try:
                    dic[f]=[int(dic[f][0])]
                except:
                    return (Response('No es una Edad la edad es un numero',400))
                if(not(dic[f][0]> 0 and dic[f][0]<99)):
                    return (Response('Edad invalida',400))
            
            elif(f=="Genero"):
                aux=comprobar_filtro(dic,f,["Hombre","Mujer","Otro"],'Genero invalido Opciones validas:["Hombre","Mujer","Otro"]')
                if(type(aux)!=str):
                    return aux
                dic[f]=[aux]
               
                  
            elif(f=="Maximo_nivel_educativo"):
                
                aux=comprobar_filtro(dic,f,["Universitario","Terciario(no universitario)","Secundaria","Primaria"],'Max.Nivel educativo invalido Opciones validas:["Universitario","Terciario(no universitario)","Secundaria","Primaria"]')

                if(type(aux)!=str):
                    return aux
                dic[f]=[aux]
               
            else:
                aux=comprobar_filtro(dic,f,["Sí", "No", "Si"],'Conoce JAP invalido Opciones validas:[Sí, No]')
                if(type(aux)!=str):
                    return aux
                dic[f]=[aux[0].replace("Si","Sí")]
    

    return obtener_microdatos(dic)
    
def comprobar(f):
    """Dado un filtro comprueba que este dentro de los permitidos"""
    for filtro in CONFIG["config_servicio"]["filters"]:
        if(( f ==filtro[0])):
            return False
    return True


                       
def comprobar_filtro(dic,f,opciones,mensaje_error):
                """Dado el filtro comprueba que las opciones de este sean correctas"""
                if(not(dic[f][0].title() in opciones)):
                    return (Response(mensaje_error,400))
                else:
                    return(dic[f][0].title())
    
@app.route("/aggregation")
def agregado():
    R=agregados(dict(request.args))
    if(type(R)==dict):
        return(json.dumps(R))
    else:
        return R
    
    

@app.route("/graficos")
def graficos():
    return "Use /graficos/Edades para obtener el grafico correspondiente o /graficos/conoceJAP para el grafico de si conocen JAP"
@app.route("/graficos/Edades")
def grafico_edad():
    conexion_sheld.obtener_grafico_edades() 
    return send_file('GraficoEdades.png',attachment_filename='GraficoEdades.jpg')

@app.route("/graficos/conoceJAP")
def grafico_conoceJAP():
    conexion_sheld.obtener_grafico_conoce_JAP()
    return send_file('GraficoconocenJAP.png',attachment_filename='GraficoconocenJAP.png')

@app.route("/reporte")
def reporte():
    conexion_sheld.dibujar_pdf()
    return send_file('Reporte.pdf',attachment_filename='Reporte.pdf')

    
@app.after_request
def per_request_callbacks(response):

    if(request.path in ["microdatos","resultados_csv"]):
        request.content_type="text/csv"
    
    if request.authorization:
        dic=  {'servicio_invocado':request.path,'fecha_invocacion': time.strftime("%d/%m/%y",datetime.now().timetuple()),'estado': {'codigo': response.status_code,'texto': response.status},'respuesta': {'largo': response.content_length,'tipo': response.content_type},'usuario': request.authorization["username"],'direccion_consulta': [request.environ['REMOTE_ADDR'], request.environ['REMOTE_PORT']]}
    else:
        dic=  {'servicio_invocado':request.path,'fecha_invocacion': time.strftime("%d/%m/%y",datetime.now().timetuple()),'estado': {'codigo': response.status_code,'texto': response.status},'respuesta': {'largo': response.content_length,'tipo': response.content_type},'usuario': None,'direccion_consulta': [request.environ['REMOTE_ADDR'], request.environ['REMOTE_PORT']]}

    Mongo_Cli.agregar_logs(dic)
    
    return response

app.run()
