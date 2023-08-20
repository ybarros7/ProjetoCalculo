from datetime import datetime, timedelta
from pyxirr import xirr
import pandas as pd
import holidays
import Operacoes, Parcelas

#CONSTANTES
PROXIMO_DIA_UTIL = 0 #DETERMINA SE O SISTEMA IRA CALCULAR DIA UTIL OU NÃO
LIMITE_TENTATIVAS = 35000 #DETERMINA O NUMERO MAXIMO DO LOOP DE DE TENTATIVAS DE CALCULO
VARIACAO_PADRAO = 0.00001 #DETERMINA A VARIACAO DURANTE O CALCULO DE META
TETO_DIAS_IOF = 365 #PRAZO MAXIMO PARA COBRANÇA DE IOF
ALIQUOTA_IOF_DIA_PF = 0.000082 #IOF A.D PF
ALIQUOTA_IOF_FLAT = 0.0038 #IOF FLAT // IOF A.A
TARIFA_CREDITO = 0

#Calcula próximo dia util
def DataPU(data):
    if PROXIMO_DIA_UTIL != 1:
        return data
    
    br_holidays = holidays.Brazil(years=[data.year, data.year], observed=False) #retorna o ano atual e o próximo, caso o vencimento venha a cair no ultimo dia do ano atual
    
    while data.weekday() >= 5 or data in br_holidays: #se a data cair no sábado (5) ou domingo (6) ou num feriado, soma mais um até dar falso
        data += timedelta(days=1)  

    return data

#Calculo por meta PARCELA com PONDERAÇÃO
def clcParcCP(dataBase, primeiroVencimento, qtdParcelas, txAm, vlrParcela):
    mes = primeiroVencimento.month - 1
    ano = primeiroVencimento.year
    lista_parcela = []
    principal = 0
    saldo = 0
    iof = 0

    for parcela in range(qtdParcelas):
        if mes >= 12 or mes < 1:
            mes = 1
            ano += 1
        else:
            mes += 1
     
        vencimento = DataPU(datetime(ano, mes, primeiroVencimento.day))
        prazo = (vencimento - dataBase).days
        vlrPresente = vlrParcela / ((1 + txAm) ** (prazo/30))
        principal += vlrPresente
        saldo += vlrParcela
        
        if prazo < TETO_DIAS_IOF:
            prazoIof = prazo
        else:
            prazoIof = TETO_DIAS_IOF
            
        iof = round(vlrPresente * prazoIof * ALIQUOTA_IOF_DIA_PF, 2)

        lista_parcela.append((parcela + 1, vencimento, prazo, vlrParcela, vlrPresente, vlrParcela - vlrPresente, iof))

    return lista_parcela, principal, saldo

#Calculo Nominal
def clcNominal(listaVencimentoNominal, taxaNominalAm, dataBaseNominal, vlrParcela):
    principalNominal = 0
    listaNominal = []

    for a in listaVencimentoNominal:
        principalNominal += round(vlrParcela / (1 + taxaNominalAm/100) ** ((a - dataBaseNominal).days / 30), 2)
        listaNominal.append(principalNominal)
    
    return listaNominal, principalNominal

#Realiza calculo das parcelas
def MetaCalculoParcela(listaRefinanciado, listaIntermediaria):
    #CALCULA O CONTRATO PORTADO
    fluxoRefinanciado, principalRefinanciado, saldoRefinanciado = clcParcCP(dataBase = datetime.strptime(listaRefinanciado[0][0], "%d/%m/%Y"), 
            primeiroVencimento = datetime.strptime(listaRefinanciado[0][1], "%d/%m/%Y"), qtdParcelas = listaRefinanciado[0][2], 
            txAm = listaRefinanciado[0][3]/100, vlrParcela = listaRefinanciado[0][4])
    
    #CALCULA O FLUXO INTERMEDIARIO, QUE SERA UTILIZADO PARA CALCULAR A TAXA CL DO NOVO CONTRATO
    fluxoIntermediario, principalIntermediario, saldoReIntermediario = clcParcCP(dataBase = datetime.strptime(listaIntermediaria[0][0], "%d/%m/%Y"), 
            primeiroVencimento = datetime.strptime(listaIntermediaria[0][1], "%d/%m/%Y"), qtdParcelas = listaIntermediaria[0][2], 
            txAm = listaIntermediaria[0][3]/100, vlrParcela = listaIntermediaria[0][4])
    
    saldo = principalRefinanciado * -1 + principalIntermediario
    
    txClAm = listaIntermediaria[0][3]
    meta = 1    
    tentativa = 0
    
    ##########
    #CALCULO DO NOVO CONTRATO
    ##########

    while round(meta, 2) != 0.00 and tentativa < LIMITE_TENTATIVAS:
        if meta < 0:
            txClAm += VARIACAO_PADRAO
        else:
            txClAm -= VARIACAO_PADRAO

        #RECALCULA O FLUXO PORTADO COM TAXA NOVA
        fluxoRefinanciadoNovo, principalRefinanciadoNovo, saldoRefinanciadoNovo = clcParcCP(dataBase = datetime.strptime(listaRefinanciado[0][0], "%d/%m/%Y"), 
            primeiroVencimento = datetime.strptime(listaRefinanciado[0][1], "%d/%m/%Y"), qtdParcelas = listaRefinanciado[0][2], 
            txAm = txClAm/100, vlrParcela = listaRefinanciado[0][4])

        #CALCULA O FLUXO NOVO COM A TAXA NOVA
        fluxoNovo, principalNovo, saldoNovo = clcParcCP(dataBase = datetime.strptime(listaIntermediaria[0][0], "%d/%m/%Y"), 
                primeiroVencimento = datetime.strptime(listaIntermediaria[0][1], "%d/%m/%Y"), qtdParcelas = listaIntermediaria[0][2], 
                txAm =txClAm/100, vlrParcela = listaIntermediaria[0][4])
        
        meta = saldo - (principalRefinanciadoNovo * -1 + principalNovo)

        tentativa += 1

    ##########
    #CALCULO DO FLUXO IOF
    ##########

    price30 = (1 + txClAm/100) ** listaIntermediaria[0][2] * (txClAm/100) / (((1 + txClAm/100) ** listaIntermediaria[0][2]) - 1)
    priceReal = round((1 + txClAm/100) ** (((datetime.strptime(listaIntermediaria[0][1], "%d/%m/%Y") - datetime.strptime(listaIntermediaria[0][0], "%d/%m/%Y")).days - 30) / 30 ) * price30, 8)

    parcelaNovoIof = round(saldo * priceReal, 2)

    txApIof = listaIntermediaria[0][3]
    
    meta = 1
    tentativa = 0

    while round(meta, 2) != 0.00 and tentativa < LIMITE_TENTATIVAS:
        if meta < 0:
            txApIof += VARIACAO_PADRAO
        else:
            txApIof -= VARIACAO_PADRAO

        fluxoNovoIof, principalNovoIof, saldoNovoIof = clcParcCP(dataBase = datetime.strptime(listaIntermediaria[0][0], "%d/%m/%Y"), 
                        primeiroVencimento = datetime.strptime(listaIntermediaria[0][1], "%d/%m/%Y"), qtdParcelas = listaIntermediaria[0][2], 
                        txAm =txApIof/100, vlrParcela = parcelaNovoIof)
    
        meta = saldo - principalNovoIof

        tentativa += 1
    
    
    ##########
    #CALCULO DO FLUXO NOMINAL
    ##########
    #Prepara vencimentos sequenciais a cada 30 dias
    fluxoVencimentoNominal = []
    for linha in fluxoIntermediario:
        if len(fluxoVencimentoNominal) == 0:
            fluxoVencimentoNominal.append(datetime.strptime(listaRefinanciado[0][1], "%d/%m/%Y"))# SE FOR PRIMEIRO VENCIMENTO É O VENCIMENTO PADRAO
        else:
            fluxoVencimentoNominal.append(datetime.strptime(listaRefinanciado[0][1], "%d/%m/%Y") + timedelta(days=30) * len(fluxoVencimentoNominal))
    
    tentativa = 0
    meta = 1
    taxaNomAm = txClAm
    principalNominal = 0
    while round(principalIntermediario - principalNominal, 2) != 0.00 and tentativa < LIMITE_TENTATIVAS:
        if meta < 0:
            taxaNomAm += VARIACAO_PADRAO
        else:
            taxaNomAm -= VARIACAO_PADRAO
        
        principalNominal = clcNominal(dataBaseNominal=datetime.strptime(listaRefinanciado[0][0], "%d/%m/%Y"), listaVencimentoNominal=fluxoVencimentoNominal, taxaNominalAm=taxaNomAm, vlrParcela=listaIntermediaria[0][4])
        meta = round(principalIntermediario - principalNominal, 2) 
        tentativa += 1

    ##########
    #RETORNOS
    ##########
    
    txApIof = txApIof #Tx.AP.am IOF
    parcelaNovoIof = parcelaNovoIof #Parc.

    novoPrinc = principalNovoIof #Novo Princ.
    dtBase = datetime.strptime(listaRefinanciado[0][0], "%d/%m/%Y") #Dt. Base
    vlrPrinc = principalIntermediario #Vlr Princ.
    vlrBruto = saldoReIntermediario #Vlr Bruto
    vlrParcela = listaIntermediaria[0][4] #Vlr Parcela
    txApAm = listaIntermediaria[0][3] #Tx.Ap.am
    txApAa = ((listaIntermediaria[0][3] / 100 + 1) ** 12 - 1) * 100 #Tx.Ap.aa
   
    txApAaIof = ((txApIof / 100 + 1) ** 12 - 1) * 100 #Tx.Ap.aa IOF
    iof = round(sum(linha[6] for linha in fluxoNovoIof) + (principalNovoIof * ALIQUOTA_IOF_FLAT), 2) #iof geral

    liberado = round(principalIntermediario - iof - TARIFA_CREDITO, 2) #Liberado
    lib_cliente = principalNovoIof - iof #Lib. Cliente
    vctoOp = fluxoNovoIof[-1][1] #Vcto Op
    
    ##########
    #CL
    ##########
    txClAm = txClAm #Tx CL Mês
    txClAa = ((txClAm / 100 + 1) ** 12 - 1) * 100 #Tx.Ap.aa IOF

    ##########
    #Nominal
    ##########
    taxaNomAm = taxaNomAm
    taxaNomAA = ((taxaNomAm / 100 + 1) ** 12 - 1) * 100

    ##########
    #CET
    ##########
    listaCetVencimentos = [dtBase]
    for linha in fluxoIntermediario:
        listaCetVencimentos.append(linha[1])

    listaCetPrincipal = [liberado * -1]
    for linha in fluxoIntermediario:
        listaCetPrincipal.append(linha[3])

    txCetAa = xirr(listaCetVencimentos, listaCetPrincipal) * 100 #Tx.CET aa
    txCetAm = ((1 + txCetAa / 100) ** (30/365) -1) * 100 

    #print(f'principalRefinanciado: {principalRefinanciado}, saldoRefinanciado: {saldoRefinanciado}')
    #print(f'principalRefinanciadoNovo {principalRefinanciadoNovo}, saldoRefinanciadoNovo {saldoRefinanciadoNovo}')
    #print(f'principalNovo {principalNovo}, saldoNovo {saldoNovo}')
    #print(f'principalNovoIof {principalNovoIof}, saldoNovoIof {saldoNovoIof}')
    #print(f'principalIntermediario {principalIntermediario}, saldoReIntermediario {saldoReIntermediario}')

    #return fluxoRefinanciado #FLUXO REFINANCIADO
    #return fluxoRefinanciadoNovo #FLUXO NOVA OPERAÇÃO - FLUXO DA PORTABILIDADE RECALCULADO COM A NOVA TAXA
    #return fluxoIntermediario #FLUXO NOVA OPERAÇÃO
    return fluxoNovo #FLUXO NOVO PRINCIPAL
    #return fluxoNovoIof #NOVO IOF