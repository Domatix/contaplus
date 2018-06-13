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

customerAccount = origen.model(name='account.account').browse([('code','=','430000')])[0]
providerAccount = origen.model(name='account.account').browse([('code','=','400000')])[0]
supplierAccount = origen.model(name='account.account').browse([('code','=','410000')])[0]

def getDiario(apuntes):
    for apunte in apuntes:
        if apunte['SUBCTA'].startswith('6'):
            if apunte['EURODEBE'] > 0:
                return 2  # Diario de compras
            else:
                return 2  # Diario de abono de compras (Cambiado para odoo 11 antes era 4)
        elif apunte['SUBCTA'].startswith('7'):
            if apunte['EUROHABER'] > 0:
                return 1  # Diario de ventas
            else:
                return 1  # Diario de abono de ventas (Cambiado para odoo 11 antes era 3)
    return 3 # Diario general(Cambiado para odoo11 antes 5)


def getAccount(account,apunte):
    # if account.startswith('430'):
    #     return customerAccount.id
    # elif account.startswith('400'):
    #     return providerAccount.id
    # elif account.startswith('410'):
    #     return supplierAccount.id
    # else:
    #     account = origen.model(name='account.account').browse([('code','=',apunte['SUBCTA'][0:2]+'0000')])[0]
    #     if not account:
    #         account = origen.model(name='account.account').browse([('code','=',apunte['SUBCTA'][0:3])])[0]
    #     return account.id
    account_id = origen.model(name='account.account').search([('code','=',apunte['SUBCTA'])])
    if account_id:
        account_id = account_id[0]
    return account_id


def getPartnerApunte(apunte):
    account_obj = origen.model(name='account.account')
    accounts = account_obj.browse([("code", "=", apunte['SUBCTA'])])
    if accounts:
        res_obj = origen.model(name='res.partner')
        res_id = res_obj.search([('name','in',accounts.name)])
        if res_id:
            return res_id[0]
        return False
    return False


def getPartner(apuntes):
    for apunte in apuntes:
        partner = getPartnerApunte(apunte)
        if partner:
            return partner
    return False

def crearAsiento(apuntes):
    apunte = apuntes[0]
    # Cabecera del asiento
    account_move = {
                    'name': '%s/%04d' %(apunte['FECHA'].year, apunte['ASIEN']),
                    'ref': apunte['DOCUMENTO'] if bool(apunte['DOCUMENTO'].strip()) else apunte['CONCEPTO'].strip(),
                    'journal_id': getDiario(apuntes),
                    'date': apunte['FECHA'].strftime("%Y-%m-%d"),
                    'partner_id': getPartner(apuntes),
                    }
    move_obj = origen.model(name='account.move')
    move_id = move_obj.create(account_move)
    # Obtener datos para los impuestos
    base_id = False
    tax_id = False
    for apunte in apuntes:
        if apunte['IVA'] > 0:
            if apunte['SUBCTA'].startswith('472'):
                if apunte['IVA'] == 18.0:
                    base_id = 39
                    tax_id = 93
                elif apunte['IVA'] == 21.0:
                    base_id = 40
                    tax_id = 94
                elif apunte['IVA'] == 8.0:
                    base_id = 36
                    tax_id = 90
                elif apunte['IVA'] == 10.0:
                    base_id = 37
                    tax_id = 91
            elif apunte['SUBCTA'].startswith('477'):
                if apunte['IVA'] == 18.0:
                    base_id = 10
                    tax_id = 24
                elif apunte['IVA'] == 21.0:
                    base_id = 11
                    tax_id = 25
                elif apunte['IVA'] == 8.0:
                    base_id = 7
                    tax_id = 21
                elif apunte['IVA'] == 10.0:
                    base_id = 8
                    tax_id = 22
            break

    for apunte in apuntes:
        # Apuntes

        line = {
                'move_id': move_id.id,
                'account_id': getAccount(apunte['SUBCTA'],apunte),
                'partner_id': getPartnerApunte(apunte) or (account_move['name'] != 'Diario de apertura' and account_move['partner_id']),
                'date': account_move['date'],
                'ref': account_move['ref'],
                'name': apunte['CONCEPTO'].strip(),
                'debit': 0,
                'credit': 0,
                'journal_id': account_move['journal_id'],
                }

        if apunte['EURODEBE'] > 0:
            line['debit'] = float(apunte['EURODEBE'])
        else:
            line['credit'] = -float(apunte['EURODEBE'])
        if apunte['EUROHABER'] > 0:
            line['credit'] += float(apunte['EUROHABER'])
        else:
            line['debit'] -= float(apunte['EUROHABER'])
        if (apunte['SUBCTA'].startswith('6') or apunte['SUBCTA'].startswith('7')) and base_id:
            line['tax_line_id'] = base_id
            # line['tax_amount'] = abs(float(apunte['EURODEBE'] - apunte['EUROHABER']))
        elif (apunte['SUBCTA'].startswith('477') or apunte['SUBCTA'].startswith('472')) and tax_id:
            line['tax_line_id'] = tax_id
            # line['tax_amount'] = abs(float(apunte['EURODEBE'] - apunte['EUROHABER']))

        line_obj = origen.model(name='account.move.line')

        line_id = line_obj.create(line)


def importar():
    dbf = ydbf.open(os.path.join('dbf', 'Diario.dbf'), encoding='latin-1')
    antNumero = 0
    apuntes = []
    for row in dbf:
        if antNumero != row['ASIEN']:
            if len(apuntes):
                crearAsiento(apuntes)
            antNumero = row['ASIEN']
            apuntes = []
        apuntes.append(row)

    if len(apuntes):
        crearAsiento(apuntes)

importar()
