
from pymongo import MongoClient
import json
###___________________###

class ConexionBD():
    def __init__(self, uri):
        
        self.client = MongoClient(uri)
        
        self.db=self.client.ProyectoFinal_DB
        
        self.col=self.db.pro_final_col
        self._id=self.col.find().count() +1
    def agregar_log(self,dic):
        try:
            dic["_id"]=self._id
            self.col.insert_one(dic)
            self._id=self._id + 1
        except Exception as e:
            print("Problemas al insertar un documento a la BD" + str(e))

    def obtener_microdatos(self):
        return json.dumps(self.obtener_dic(self.col.find()))



    def obtener_dic(self,cursor):
        dic={"microdatos":[], "cantidad":cursor.count()}

        for objeto in cursor:
            dic["microdatos"].append(objeto)

        return dic
