
from pymongo import MongoClient

import time
from datetime import datetime

###___________________###

class ConexionBD():
    def __init__(self, uri):
        
        self.client = MongoClient(uri)
        
        self.db=self.client.ProyectoFinal_DB
        
        self.col=self.db.pro_final_col
        self._id=self.col.find().count() +1
    def agregar_logs(self,dic):
        try:
            dic["_id"]=self._id
            self.col.insert_one(dic)
            self._id=self._id + 1
        except Exception as e:
            print("Problemas al insertar un documento a la BD" + str(e))#No es lo mejor un print.......

    def obtener_logs(self, filtros):
        """Obtiene los logs"""
        dic=self.obtener_dic(self.col.find())
        
        return (dic)


    def obtener_dic(self,cursor):
        """Obtiene el dic dado un cursor""" #Se usa muy poco....
        dic={"microdatos":[], "cantidad":cursor.count()}

        for objeto in cursor:
            dic["microdatos"].append(objeto)

        return dic
