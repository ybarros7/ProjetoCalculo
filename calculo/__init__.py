import pandas as pd
import Operacoes, Parcelas, FuncoesCalculo
from datetime import date, datetime

df = pd.read_csv("C:/Users/yagod/OneDrive/Área de Trabalho/Calculo/PARCELA_Testes.csv", skiprows=0, sep=";")
listaPortabilidade = df.iloc[:, :6].values.tolist()
listaRefin = df.iloc[:, 6:].values.tolist()

for a in listaRefin:
    print(a[0])
    print(a[1])

listaOperacao = []

for a in listaPortabilidade:
    operacao = Operacoes.Operacoes(
        numeroOperacaoRefinanciada = a[1],
        numeroOperacao = None,
        dataBase = datetime.strptime(a[0], "%d/%m/%Y"),
        primeiroVencimento = datetime.strptime(a[2], "%d/%m/%Y"),
        ultimoVencimento = None,
        prazo = 0,
        qtdParcelas = a[3],
        valorPrincipal = 0,
        valorIof = 0,
        valorJuros = 0,
        valorTarifas = 0,
        valorBruto = 0,
        valorLiquido = 0,
        taxaApAm = a[4],
        taxaNmAm = 0,
        taxaClAm = 0,
        taxaApAa = 0,
        taxaNmAa = 0,
        taxaClAa = 0
    )

    operacao.preparaOperacao()

    listaOperacao.append(operacao)