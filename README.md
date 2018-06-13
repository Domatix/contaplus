# Contaplus

Importación de datos de Contaplus a Odoo 10.

### Requisitos iniciales

* Instalar ydbf: [ydbf](https://github.com/y10h/ydbf/blob/master/setup.py)
* Instalar erppeek: `pip install erppeek`
* Crear una carpeta llamada **dbf** en el lugar donde se vayan a ejecutar los scripts y dejar dentro los .dbf de contaplus

### Datos que se importarán a Odoo

Los datos que importa el script **import_cuentas_peek** son los siguientes:
* Cuentas contables
* Clientes (Nombre, dirección y NIF)
* Proveedores (Nombre, dirección y NIF)

Los datos que importa el script **import_asientos_peek** son los siguientes:
* Asientos contables
* Líneas de los asientos

### Ejecución de scripts

```
#-*- coding: utf-8 -*-
import ydbf
import sys
import erppeek
import csv
import datetime
import requests
import os.path
import vatnumber

SERVER_origen = 'http://localhost:8069'
DATABASE_origen = 'base_de_datos'
USERNAME = 'username'
PASSWORD = 'password'

debug = True

# Conectar al ERP
origen = erppeek.Client(SERVER_origen, DATABASE_origen, USERNAME, PASSWORD)
```
Es necesario cambiar las variables **SERVER_origen**, **DATABASE_origen**, **USERNAME** y **PASSWORD** para que coincidan con nuestra configuración de Odoo. 
* SERVER_origen: Dirección de la instancia de Odoo que tenemos ejecutándose.
* DATABASE_origen: Nombre de la base de datos donde se va a ejecutar la migración de datos.
* USERNAME: Usuario con el que se va a conectar a Odoo (por ejemplo admin).
* PASSWORD: Contraseña del usuario con el que se va a conectar a Odoo.

Una vez guardados los cambios en los dos ficheros, los ejecutaremos en este orden mediante la siguiente línea de comando:
* `python import_cuentas_peek.py`
* `python import_asientos_peek.py`

