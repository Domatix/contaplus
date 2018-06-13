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
USERNAME = 'usuario'
PASSWORD = 'contraseña'

debug = True

# Conectar al ERP
origen = erppeek.Client(SERVER_origen, DATABASE_origen, USERNAME, PASSWORD)

def getLetraDNI(dni):
    NIF='TRWAGMYFPDXBNJZSQVHLCKE'
    if type(dni) == str or type(dni) == unicode:
        try:
            dni = int(dni)
        except:
            dni = dni.replace('/','')
            dni = int(dni)
            return NIF[dni%23]
    return NIF[dni%23]


def decodeCIF(originalCIF):
    if len(originalCIF):
        # Quitar guiones, puntos y espacios
        decodedCIF = originalCIF.replace("-", "").replace(".", "").replace(" ", "")
        if decodedCIF[0].isdigit():
            # Es una persona física
            if decodedCIF[-1].isdigit():
                decodedCIF += getLetraDNI(decodedCIF) # Letra de control
            if len(decodedCIF) < 9:
                decodedCIF = "0" + decodedCIF # Añadir un 0 delante
        # Ver si lleva ya el prefijo de dos letras del país delante del código
        if decodedCIF[0:2].isalpha():
            return decodedCIF.upper()
        if not decodedCIF.startswith('ES'):
            decodedCIF = "ES" + decodedCIF
        return decodedCIF.upper()
    else:
        return originalCIF

def import_account(dbf):
    for row in dbf:
        # CREACIÓN DE CUENTAS

        account_obj = origen.model(name='account.account')
        accounts = account_obj.browse([("code", "=", row['COD'][0:2]+'0000')])
        if not accounts:
            accounts = account_obj.browse([("code", "like", row['COD'][0:2])])

        account = {
                'name': row['TITULO'].strip(),
                'code': row['COD'],
                'user_type_id': accounts[0].user_type_id.id or 1,
                'reconcile': accounts[0].reconcile
            }

        if not account_obj.browse([('code','=',row['COD'])]):
            account = account_obj.create(account)

def import_partner(dbf):
    for row in dbf:
        account_obj = origen.model(name='account.account')
        # PARA PROVEEDORES

        if ((row["COD"].startswith('410') and row["COD"] != "41000000")
            or (row["COD"].startswith('400') and row["COD"] != "40000000")):

            country_obj = origen.model('res.country.state')
            country_id = country_obj.browse([('name','ilike',row['PROVINCIA'])])

            if country_id:
                country_id = country_id[0].id

            else:
                country_id = False
            account_id = account_obj.search([('code','=',row['COD'])])
            if account_id:
                account_id = account_id[0]
            partner = {
                'name': row['TITULO'].strip(),
                'vat': decodeCIF(row['NIF']),
                'supplier': True,
                'customer': False,
                'opt_out': True,
                'street': row['DOMICILIO'].strip(),
                'zip': row['CODPOSTAL'],
                'city':row['POBLACION'],
                'state_id': country_id,
                'property_account_payable_id':account_id

            }

            if not vatnumber.check_vat(partner['vat']):
                partner['vat'] = False

            partner_obj = origen.model(name='res.partner')
            if not partner_obj.browse([('name','=',row['TITULO'])]):
                partner = partner_obj.create(partner)
            else:
                print row['TITULO']

        # PARA CLIENTES

        if ((row["COD"].startswith('430') and row["COD"] != "43000000")
            or (row["COD"].startswith('440') and row["COD"] != "44000000")):


            country_obj = origen.model('res.country.state')
            country_id = country_obj.browse([('name','ilike',row['PROVINCIA'])])

            if country_id:
                country_id = country_id[0].id

            else:
                country_id = False

            account_id = account_obj.search([('code','=',row['COD'])])
            if account_id:
                account_id = account_id[0]
            partner = {
                'name': row['TITULO'].strip(),
                'vat': decodeCIF(row['NIF']),
                'supplier': False,
                'customer': True,
                'opt_out': True,
                'street': row['DOMICILIO'].strip(),
                'zip': row['CODPOSTAL'],
                'city':row['POBLACION'],
                'state_id': country_id,
                'property_account_receivable_id':account_id,


            }

            if not vatnumber.check_vat(partner['vat']):
                partner['vat'] = False

            partner_obj = origen.model(name='res.partner')
            if not partner_obj.browse([('name','=',row['TITULO'])]):
                partner = partner_obj.create(partner)
            else:
                print row['TITULO']
def importar():
    dbf = ydbf.open(os.path.join('dbf', 'Subcta.dbf'), encoding='latin-1')
    account_obj = origen.model(name='account.account')
    print 'Importando Cuentas'
    import_account(dbf)
    print 'Importando Partners'
    dbf2 = ydbf.open(os.path.join('dbf', 'Subcta.dbf'), encoding='latin-1')
    import_partner(dbf2)




importar()
