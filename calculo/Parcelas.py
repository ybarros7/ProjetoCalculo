from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal

class Parcelas:
    def __init__(self, numeroOperacao: str, dataBase: date, numeroParcela: int, dataVencimento: date, prazo: int, valorPrincipal: Decimal, valorIof = Decimal, valorJuros = Decimal, valorPmt = Decimal):
        self.numeroOperacao = numeroOperacao

        self.dataBase = dataBase
        
        self.dataVencimento = dataVencimento
        self.prazo = prazo

        self.numeroParcela = numeroParcela

        self.valorPrincipal = valorPrincipal
        self.valorIof = valorIof
        self.valorJuros = valorJuros
        self.valorPmt = valorPmt

        def clcPrazo(self):
            self.prazo = (dataVencimento - dataBase).days

        def clcVencimento(self):
            mes = 0
            if self.dataBase.days <= 2:
                mes = 1
            else:
                mes = 2
            
            self.dataVencimento += relativedelta(months=mes)
            self.dataVencimento = date(self.dataVencimento.year, self.dataVencimento.month, 7)