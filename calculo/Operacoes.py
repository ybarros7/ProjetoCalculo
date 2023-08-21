from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal

class Operacoes:
    def __init__(self, numeroOperacao: str, numeroOperacaoRefinanciada: str, qtdParcelas: int, valorParcela: Decimal, dataBase: date, primeiroVencimento: date, ultimoVencimento: date, prazo: int, valorPrincipal: Decimal, valorIof: Decimal, valorJuros: Decimal, valorTarifas: Decimal, valorBruto: Decimal, valorLiquido: Decimal, taxaApAm: float, taxaNmAm: float, taxaClAm: float, taxaApAa: float, taxaNmAa: float, taxaClAa: float):
        self.numeroOperacao = numeroOperacao
        self.numeroOperacaoRefinanciada = numeroOperacaoRefinanciada

        self.dataBase = dataBase
        self.primeiroVencimento = primeiroVencimento
        self.ultimoVencimento = ultimoVencimento
        self.prazo = prazo

        self.qtdParcelas = qtdParcelas
        self.valorParcela = valorParcela

        self.valorPrincipal = valorPrincipal
        self.valorIof = valorIof
        self.valorJuros = valorJuros
        self.valorTarifas = valorTarifas
        self.valorBruto = valorBruto
        self.valorLiquido = valorLiquido

        self.taxaApAm = taxaApAm
        self.taxaNmAm = taxaNmAm
        self.taxaClAm = taxaClAm

        self.taxaApAa = taxaApAa
        self.taxaNmAa = taxaNmAa
        self.taxaClAa = taxaClAa

    def clcTaxaAa(self):
        self.taxaApAa = ((1 + self.taxaApAm / 100) ** (30/365) -1) * 100
        self.taxaNmAa = ((1 + self.taxaNmAa / 100) ** (30/365) -1) * 100
        self.taxaClAa = ((1 + self.taxaClAa / 100) ** (30/365) -1) * 100

    def clcVencimentos(self):
        mes = 0
        if self.dataBase.day <= 2:
            mes = 1
        else:
            mes = 2
        
        self.primeiroVencimento = self.dataBase.replace(day=7) + relativedelta(months=mes)

        self.ultimoVencimento = self.primeiroVencimento + relativedelta(months=self.qtdParcelas-1)
    
    def clcPrazo(self):
        self.prazo = self.ultimoVencimento - self.dataBase

    def clcProximoMes(self):
        self.dataBase += relativedelta(months=1)
        self.primeiroVencimento += relativedelta(months=1)
        self.qtdParcelas -= 1
    
    def preparaOperacao(self):
        self.clcVencimentos()
        self.clcPrazo()
        self.clcTaxaAa()
        self.valorPrincipal = 0
        self.valorBruto = 0