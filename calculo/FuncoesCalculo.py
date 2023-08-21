from datetime import datetime, timedelta
from pyxirr import xirr
import pandas as pd
import holidays
import Operacoes, Parcelas
from decimal import Decimal

#CONSTANTES
PROXIMO_DIA_UTIL = 0 #DETERMINA SE O SISTEMA IRA CALCULAR DIA UTIL OU NÃO
LIMITE_TENTATIVAS = 35000 #DETERMINA O NUMERO MAXIMO DO LOOP DE DE TENTATIVAS DE CALCULO
VARIACAO_PADRAO = 0.00000001 #DETERMINA A VARIACAO DURANTE O CALCULO DE META
VARIACAO_PADRAO_3_CASAS = 0.001
VARIACAO_PADRAO_4_CASAS = 0.0001
VARIACAO_PADRAO_5_CASAS = 0.00001
VARIACAO_PADRAO_INTEIRO = 0.000001
VARIACAO_PADRAO_DECIMAL = 0.0000001
TETO_DIAS_IOF = 365 #PRAZO MAXIMO PARA COBRANÇA DE IOF
ALIQUOTA_IOF_DIA_PF = 0.000082 #IOF A.D PF
ALIQUOTA_IOF_FLAT = 0.0038 #IOF FLAT // IOF A.A
TARIFA_CREDITO = 0
ARREDONDAMENTO_PADRAO_REAL = 2

#Calcula próximo dia util
def DataPU(data):
    if PROXIMO_DIA_UTIL != 1:
        return data
    
    br_holidays = holidays.Brazil(years=[data.year, data.year], observed=False) #retorna o ano atual e o próximo, caso o vencimento venha a cair no ultimo dia do ano atual
    
    while data.weekday() >= 5 or data in br_holidays: #se a data cair no sábado (5) ou domingo (6) ou num feriado, soma mais um até dar falso
        data += timedelta(days=1)  

    return data

#Calculo por meta PARCELA com PONDERAÇÃO
def clcParcCP(operCalculo : Operacoes.Operacoes):
    
    parcelaCalculo = Parcelas.Parcelas

    mes = operCalculo.primeiroVencimento.month - 1
    ano = operCalculo.primeiroVencimento.year

    listaParcela = []

    operCalculo.valorPrincipal = 0
    operCalculo.valorBruto = 0

    for parcela in range(operCalculo.qtdParcelas):
        if mes >= 12 or mes < 1:
            mes = 1
            ano += 1
        else:
            mes += 1
     
        parcelaCalculo.dataVencimento = DataPU(datetime(ano, mes, operCalculo.primeiroVencimento.day))
        parcelaCalculo.numeroParcela = parcela + 1
        parcelaCalculo.prazo = (parcelaCalculo.dataVencimento - operCalculo.dataBase).days
        
        parcelaCalculo.valorPrincipal = operCalculo.valorParcela / ((1 + operCalculo.taxaApAm) ** (parcelaCalculo.prazo/30))
        
        operCalculo.valorPrincipal += parcelaCalculo.valorPrincipal
        
        operCalculo.valorBruto += operCalculo.valorParcela
        
        if parcelaCalculo.prazo < TETO_DIAS_IOF:
            prazoIof = parcelaCalculo.prazo
        else:
            prazoIof = TETO_DIAS_IOF
            
        parcelaCalculo.valorIof = round(parcelaCalculo.valorPrincipal * prazoIof * ALIQUOTA_IOF_DIA_PF, 2)        

        listaParcela.append(parcelaCalculo)

    return operCalculo, listaParcela

#Calculo Nominal
def clcNominal(listaVencimentoNominal, taxaNominalAm, dataBaseNominal, vlrParcela):
    principalNominal = 0
    listaNominal = []

    for a in listaVencimentoNominal:
        principalNominal += round(vlrParcela / (1 + taxaNominalAm/100) ** ((a - dataBaseNominal).days / 30), 2)
        listaNominal.append(principalNominal)
    
    return listaNominal, principalNominal

def clcTaxaNominal(operCalculo : Operacoes.Operacoes):
    price30 = (1 + operCalculo.taxaApAm) ** operCalculo.qtdParcelas * (operCalculo.taxaApAm) / (((1 + operCalculo.taxaApAm) ** operCalculo.qtdParcelas) - 1)
    priceReal = round((1 + operCalculo.taxaApAm) ** (((operCalculo.primeiroVencimento - operCalculo.dataBase).days - 30) / 30 ) * price30, 8)

    return price30, priceReal

def clcVariacaoTaxa(meta):
    variacao = 0
    if abs(meta) >= 1000:
        variacao += VARIACAO_PADRAO_3_CASAS
    elif abs(meta) >= 100:
        variacao += VARIACAO_PADRAO_4_CASAS
    elif abs(meta) >= 10:
        variacao += VARIACAO_PADRAO_5_CASAS
    elif abs(meta) >= 1:
        variacao += VARIACAO_PADRAO_INTEIRO
    else:
        variacao += VARIACAO_PADRAO_DECIMAL

    if meta > 0:
        variacao * -1

    return variacao

def metaClcParcCP(operCalculo : Operacoes.Operacoes, operCalculoSecundaria : Operacoes.Operacoes, meta : Decimal, saldo : Decimal):
    tentativa = 0
    variacao = 0
    while round(meta, ARREDONDAMENTO_PADRAO_REAL) != 0.00 and tentativa < LIMITE_TENTATIVAS:
        
        operCalculo.taxaApAm += clcVariacaoTaxa(meta)
        operCalculoSecundaria.taxaApAm = operCalculo.taxaApAm

        #RECALCULA O FLUXO PORTADO COM TAXA NOVA
        operCalculoSecundaria, listaParcelaPortabilidadeNovo = clcParcCP(operCalculoSecundaria)

        #CALCULA O FLUXO NOVO COM A TAXA NOVA
        operCalculo, listaParcelaRefinanciamentoNovo = clcParcCP(operCalculo)
        
        meta = saldo - (operCalculo.valorPrincipal * -1 + operCalculoSecundaria.valorPrincipal)

        tentativa += 1
    
    return operCalculo, operCalculoSecundaria

def metaClcParcTroco(operCalculo : Operacoes.Operacoes, saldo : Decimal):
    meta = saldo - operCalculo.valorPrincipal
    tentativa = 0
    variacao = 0.000000000

    while round(meta, ARREDONDAMENTO_PADRAO_REAL) != 0.00 and tentativa < LIMITE_TENTATIVAS:
        if meta is None or meta < 0:
            if abs(meta) >= 1:
                variacao += VARIACAO_PADRAO_INTEIRO
            else:
                variacao += VARIACAO_PADRAO_DECIMAL
        else:
            if abs(meta) >= 1:
                variacao -= VARIACAO_PADRAO_INTEIRO
            else:
                variacao -= VARIACAO_PADRAO_DECIMAL

        operCalculo.taxaApAm += variacao

        operCalculo, listaParcelaTroco = clcParcCP(operCalculo)

        meta = saldo - operCalculo.valorPrincipal

        tentativa += 1
        variacao = 0
    
    return operCalculo

#Realiza calculo das parcelas
def MetaCalculoParcela(operPortabilidade : Operacoes.Operacoes, operRefinanciamento : Operacoes.Operacoes):

    #CALCULA O CONTRATO PORTADO
    operPortabilidade, listaParcela = clcParcCP(operPortabilidade)
    
    #CALCULA O FLUXO INTERMEDIARIO, QUE SERA UTILIZADO PARA CALCULAR A TAXA CL DO NOVO CONTRATO
    operRefinanciamento, listaParcelaRefinanciamento = clcParcCP(operRefinanciamento)
    
    saldo = operPortabilidade.valorPrincipal * -1 + operRefinanciamento.valorPrincipal

    ##########
    #CALCULO DO NOVO CONTRATO
    ##########
    operPortabilidadeNovo, operNovoContrato = metaClcParcCP(operPortabilidade, operRefinanciamento, 1, saldo)

    ##########
    #CALCULO DO TROCO
    ##########
    operTroco = operNovoContrato

    price30, priceReal = clcTaxaNominal(operRefinanciamento)

    operTroco.valorParcela = round(saldo * priceReal, 2)
   
    operTroco = metaClcParcTroco(operTroco, saldo)
    
    ##########
    #CALCULO DO FLUXO NOMINAL
    ##########
    #Prepara vencimentos sequenciais a cada 30 dias
    # fluxoVencimentoNominal = []
    # fluxoVencimentoNominal.append(operRefinanciamento.dataBase)

    # for linha in range(operRefinanciamento.qtdParcelas):
    #     fluxoVencimentoNominal.append(operRefinanciamento.dataBase + timedelta(days=30) * len(fluxoVencimentoNominal))
    
    # tentativa = 0
    # meta = 1
    # taxaNomAm = txClAm
    # principalNominal = 0
    # while round(principalIntermediario - principalNominal, 2) != 0.00 and tentativa < LIMITE_TENTATIVAS:
    #     if meta < 0:
    #         taxaNomAm += VARIACAO_PADRAO
    #     else:
    #         taxaNomAm -= VARIACAO_PADRAO
        
    #     principalNominal = clcNominal(dataBaseNominal=datetime.strptime(listaRefinanciado[0][0], "%d/%m/%Y"), listaVencimentoNominal=fluxoVencimentoNominal, taxaNominalAm=taxaNomAm, vlrParcela=operRefinanciamento.valorParcela)
    #     meta = round(principalIntermediario - principalNominal, 2) 
    #     tentativa += 1
    
    ##########
    #CET
    ##########
    # listaCetVencimentos = [dtBase]
    # for linha in fluxoIntermediario:
    #     listaCetVencimentos.append(linha[1])

    # listaCetPrincipal = [liberado * -1]
    # for linha in fluxoIntermediario:
    #     listaCetPrincipal.append(linha[3])

    # txCetAa = xirr(listaCetVencimentos, listaCetPrincipal) * 100 #Tx.CET aa
    # txCetAm = ((1 + txCetAa / 100) ** (30/365) -1) * 100 

    return operTroco