from io import BytesIO
from io import StringIO
import numpy as np
import pandas as pd
from instagrapi import Client
import requests
from pathlib import Path
import time
import datetime
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import logging

logger = logging.getLogger()

global cl
def login_user():
    """
    Intenta iniciar sesión en Instagram usando la información de sesión proveída anteriormente o el nombre de usuario y contraseña dadas.
    """

    global cl    
    cl = Client()
    session = cl.load_settings(Path('session.json'))

    login_via_session = False
    login_via_pw = False

    if session:
        try:
            cl.set_settings(session)
            cl.login("USERNAME", "PASSWORD")

            # Chequear la validez de la sesión
            try:
                cl.get_timeline_feed()
            except LoginRequired:
                logger.info("Session is invalid, need to login via username and password")

                old_session = cl.get_settings()

                #Usar la misma uuid a través de distintos dispositivos
                cl.set_settings({})
                cl.set_uuids(old_session["uuids"])

                cl.login("USERNAME", "PASSWORD")
            login_via_session = True
        except Exception as e:
            logger.info("Couldn't login user using session information: %s" % e)

    if not login_via_session:
        try:
            logger.info("Attempting to login via username and password. username: testaccount7047")
            if cl.login("USERNAME", "PASSWORD"):
                login_via_pw = True
        except Exception as e:
            logger.info("Couldn't login user using username and password: %s" % e)

    if not login_via_pw and not login_via_session:
        raise Exception("Couldn't login user with either password or session")

#Ejecutar este código la primera vez que se inicie sesión
# cl = Client()
# cl.login(USERNAME, PASSWORD)
# cl.dump_settings("session.json")

#Ejecutar esta función para posteriores ingresos
login_user()

#Obtiene el excel con las respuestas al formulario
r = requests.get("https://docs.google.com/spreadsheet/ccc?key=1OgH12Ey_ZIRRJVruRSOvmRL1jH6e7JiQhvM_2unKKtg&output=csv")
if r.status_code == 200:
    print("Solicitud exitosa")
else: print("OCurrió un error")
data= r.content

#Pasa los datos a una tabla en pandas (la fecha y la hora de la respuesta quedan como índices de la tabla)
df = pd.read_csv(BytesIO(data),index_col=0,parse_dates=['Marca temporal'],dayfirst=True)
df.head()
today = datetime.date.today()


#Recorre la tabla a través de los índice
for ind in df.index:
    if ind.day == today.day and ind.month == today.month and ind.year == today.year:
        if str(df['Buscas o encontraste algo?'][ind]) == "Encontré algo perdido":  
            #obtiene el link de la imagen
            link = df['Imagen del objeto encontrado'][ind]
            s_link = str(link)
            #Obtiene la id de la imagen
            img_id = s_link[s_link.find("id=") + 3:]
            #Nombre del objeto
            obj_name = df['¿Cuál es la cosa perdida?'][ind]
            #Lugar donde se encontró
            place_found = df['¿Dónde se encontró?'][ind]
            #Lugar donde se dejó
            place_left = df['¿En qué parte se dejó el objeto (para su recepción) o en caso que aun no lo haya dejado su contacto?'][ind]
            #Enlace de descarga de la imagen
            link = "https://drive.google.com/uc?id=" + img_id
            img_req = requests.get(link)
            img_desc = "Objeto encontrado: " + obj_name + "\n" + "Lugar donde se encontró: " + place_found + "\n" + "Puede ir a buscarlo en " + place_left
            if img_req.status_code == 200:
                filename = "uploadImg.png"
                p = filename
                #Se guarda la imagen de forma local
                with open(filename, 'wb') as file:
                    file.write(img_req.content)
                    print("Imagen descargada")
                    #Sube una publicación con la foto
                    cl.photo_upload(path=Path(p),caption=img_desc, usertags=[])
                time.sleep(10)
        else:
            if str(df['Imagen del objeto perdido'][ind]) != "nan":
                #obtiene el link de la imagen
                link = df['Imagen del objeto perdido'][ind]
                s_link = str(link)
                #Obtiene la id de la imagen
                img_id = s_link[s_link.find("id=") + 3:]
                #Nombre del objeto
                obj_name = df['¿Cuál es la cosa perdida?'][ind]
                #Lugar donde fue visto por la última vez
                last_seen = df['Dónde se te perdió?'][ind]
                #Información de contacto
                contact_info = df['Información de contacto'][ind]
                #Enlace de descarga de la imagen
                link = "https://drive.google.com/uc?id=" + img_id
                img_req = requests.get(link)
                img_desc = "Objeto encontrado: " + obj_name + "\n" + "Lugar donde se perdió: \" " + last_seen + "\" \n" + "Información de contacto: \"" + place_left+ "\" \n"
                if img_req.status_code == 200:
                    filename = "uploadImg.png"
                    p = filename
                    #Se guarda la imagen de forma local
                    with open(filename, 'wb') as file:
                        file.write(img_req.content)
                        print("Imagen descargada")
                        #Sube una publicación con la foto
                        cl.photo_upload(path=Path(p),caption=img_desc, usertags=[])
                    time.sleep(10)
            else:
                #obtiene el link de la imagen
                obj_name = df['¿Cuál es la cosa perdida?'][ind]
                last_seen = df['Dónde se te perdió?'][ind]
                contact_info = df['Información de contacto'][ind]
                filename = "generic.png"
                p = filename
                img_desc = "Objeto encontrado: " + obj_name + "\n" + "Lugar donde se perdió: \" " + last_seen + "\" \n" + "Información de contacto: \"" + place_left+ "\" \n"
                with open(filename, 'wb') as file:
                    #Sube una publicación con una foto genérica
                    cl.photo_upload(path=Path(p),caption=img_desc, usertags=[])
                time.sleep(10)

print("Las nuevas entradas se subieron con éxito.")
