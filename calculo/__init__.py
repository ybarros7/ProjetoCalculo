import pandas as pd
import Operacoes, Parcelas, FuncoesCalculo
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

TAXA_TETO = 0.0208

df = pd.read_csv("tests\PARCELA_Testes.csv", skiprows=0, sep=";")
listaPortabilidade = df.values.tolist()

for a in listaPortabilidade:
    operPortabilidade = Operacoes.Operacoes(
        numeroOperacaoRefinanciada = None,
        numeroOperacao = a[1],
        dataBase = datetime.strptime(a[0], "%d/%m/%Y"),
        primeiroVencimento = datetime.strptime(a[2], "%d/%m/%Y"),
        ultimoVencimento = None,
        prazo = 0,
        qtdParcelas = a[3],
        valorParcela= a[5],
        valorPrincipal = 0,
        valorIof = 0,
        valorJuros = 0,
        valorTarifas = 0,
        valorBruto = 0,
        valorLiquido = 0,
        taxaApAm = a[4]/100,
        taxaNmAm = 0,
        taxaClAm = 0,
        taxaApAa = 0,
        taxaNmAa = 0,
        taxaClAa = 0
    )

    operPortabilidade.preparaOperacao()

    operRefinanciamento = Operacoes.Operacoes(
        numeroOperacaoRefinanciada = a[1],
        numeroOperacao = None,
        dataBase = datetime.strptime(a[0], "%d/%m/%Y"),
        primeiroVencimento = datetime.strptime(a[0], "%d/%m/%Y"),
        ultimoVencimento = None,
        prazo = 0,
        qtdParcelas = a[6],
        valorParcela= a[7],
        valorPrincipal = 0,
        valorIof = 0,
        valorJuros = 0,
        valorTarifas = 0,
        valorBruto = 0,
        valorLiquido = 0,
        #taxaApAm = 0.019749999,
        taxaApAm = TAXA_TETO, #2,08
        taxaNmAm = 0,
        taxaClAm = 0,
        taxaApAa = 0,
        taxaNmAa = 0,
        taxaClAa = 0
    )

    operRefinanciamento.preparaOperacao()

    operTroco = FuncoesCalculo.MetaCalculoParcela(operPortabilidade, operRefinanciamento)

    while operTroco.taxaApAm > TAXA_TETO or operTroco.qtdParcelas <= 1:   
        operPortabilidade.valorParcela = a[5]
        operPortabilidade.valorPrincipal = 0
        operPortabilidade.valorBruto = 0
        operPortabilidade.dataBase += relativedelta(months=1)
        operPortabilidade.primeiroVencimento += relativedelta(months=1)
        operPortabilidade.qtdParcelas -= 1
        operPortabilidade.preparaOperacao()

        operRefinanciamento.valorParcela = a[7]
        operRefinanciamento.valorPrincipal = 0
        operRefinanciamento.valorBruto = 0
        operRefinanciamento.dataBase += relativedelta(months=1)
        operRefinanciamento.primeiroVencimento += relativedelta(months=1)
        operRefinanciamento.preparaOperacao()
        
        operTroco = FuncoesCalculo.MetaCalculoParcela(operPortabilidade, operRefinanciamento)

    print(operTroco.taxaApAm)