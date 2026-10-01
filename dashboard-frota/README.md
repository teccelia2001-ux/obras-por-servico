# Dashboard Frota TECCEL (Streamlit)

Visão geral de **combustível e manutenção numa tela só**, substituindo as
várias abas do relatório em Power BI.

## Rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Dados

Três jeitos, nesta ordem:

1. **Enviar pela barra lateral** (planilha de combustível e de manutenção);
2. deixar as planilhas na pasta `dados/` com nomes começando por
   `combustivel` e `manutencao` (várias são somadas — ex.: uma por ano);
3. sem planilha, o app mostra **dados de exemplo** fictícios para ver o layout.

As colunas são reconhecidas pelo nome, sem ligar para acento ou maiúscula:

| Combustível | aceita também |
|---|---|
| data | data abastecimento, emissão |
| tombamento | tomb, prefixo, veículo, placa |
| tipo de veículo | tipo |
| serviços | serviço, equipe, centro de custo |
| concessionária | cliente, contrato |
| regional | estado, UF, base |
| combustível | produto |
| litros | qtd litros, quantidade |
| km rodados | km |
| valor | valor total, total, custo |

Manutenção usa os mesmos nomes para data/tombamento/tipo/serviços/
concessionária/regional, mais **descrição** (categoria: peças, pneus,
serviços…), **material**, **fornecedor**, **qtd** e **valor**.
Só **data** e **valor** são obrigatórias.

## O que a tela mostra

- Cards: custo total, combustível e manutenção — com variação contra o
  **mesmo período** do ano anterior, média mensal e previsão do ano
  (realizado + média mensal × meses que faltam).
- Indicadores: veículos, litros, km, consumo (km/l), preço médio do litro,
  combustível/km, manutenção/km e custo total/km.
- Custo mensal empilhado (com o total do ano anterior), custo por km,
  comparativo de 3 anos, maiores custos por tombamento e por equipe,
  manutenção por categoria, preço do litro (diesel × gasolina), custo por
  concessionária e a tabela por veículo (com download CSV).

Filtros na barra lateral: ano, mês, regional, tipo de veículo,
serviço/equipe, concessionária e tombamento.
