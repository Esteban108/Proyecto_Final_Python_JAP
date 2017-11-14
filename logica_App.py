
from flask import Flask
from conexion_sheld import obtener_hoja

from functools import wraps
from flask import request, Response
from flask import g
from datetime import datetime
from flask import request
from conexion_BD import  ConexionBD
import json
import time

#___________________________________________#

class App_flask(Flask):
    
    def __init__(self, import_name):
        super().__init__(import_name)
        
        
    def obtener_csv(self):
        planilla=obtener_hoja().get('values', [])
        csv=""
        for i in range(0,len(planilla)):
            for ii in range(len(planilla[0])):#el largo es igual para todas las columnas
                csv=csv+planilla[i][ii] + ","
            csv=csv[0:-1]#Quita el ultimo ","//Cambio de columna 
            csv=csv+ "<br/>"
        return csv
        

    def check_auth(self,username, password):
        
        dic=json.loads(open('config.json').read())["user"]
        
        return ((username in dic) and password ==dic[username])

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
    

#_________________________________________#
    
app=App_flask(__name__)
Mongo_Cli= ConexionBD(json.loads(open('config.json').read())["mongo_uri"])

@app.route('/resultados_csv')
def pagina_planilla():
    return app.obtener_csv()

@app.route("/microdatos")
@app.requires_auth
def microdatos():
    return(Mongo_Cli.obtener_microdatos())

@app.after_request
def per_request_callbacks(response):
    
    if request.authorization:
        dic=  {'fecha_invocacion': time.strftime("Fecha: %d/%m/%y Hora: %H:%M",datetime.now().timetuple()),'estado': {'codigo': response.status_code,'texto': response.status},'respuesta': {'largo': response.content_length,'tipo': response.content_type},'usuario': request.authorization["username"],'direccion_consulta': [request.environ['REMOTE_ADDR'], request.environ['REMOTE_PORT']]}
   
    else:
        dic=  {'fecha_invocacion': time.strftime("Fecha: %d/%m/%y Hora: %H:%M",datetime.now().timetuple()),'estado': {'codigo': response.status_code,'texto': response.status},'respuesta': {'largo': response.content_length,'tipo': response.content_type},'usuario': None,'direccion_consulta': [request.environ['REMOTE_ADDR'], request.environ['REMOTE_PORT']]}

    Mongo_Cli.agregar_log(dic)
    
  

   
  
    
    return response

app.run()
