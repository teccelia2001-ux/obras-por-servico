# Obras por serviço — termômetro

Informa todas as obras que tiveram um determinado serviço, buscando pelo
código. Usa o mesmo coletor do termômetro da análise de obras pagas.

- **Link público:** https://teccelia2001-ux.github.io/obras-por-servico/
- **Fontes na máquina:** `PROJETOS CLOUDE/busca-servico-obras/`

## Como funciona

A coleta é feita **por mês**, não pelo ano inteiro: o coletor muda o filtro de
mês da tela, lê a lista daquele mês (rolando até o fim e virando as páginas),
diz quantas obras achou e pede confirmação antes de varrer. Para não ficar obra
de fora, a listagem só para quando a contagem deixa de crescer, e cada obra
ainda é confirmada dentro da planilha.

Depois da coleta o filtro de mês continua valendo: cada serviço guarda a data
da planilha, então dá para trocar de mês sem varrer o termômetro de novo.

## Análises salvas

Mesmo padrão da análise detalhada de obras pagas, com os botões no topo:

- **💾 Salvar análise** — guarda a lista de obras, a coleta, os serviços
  escolhidos e os filtros. Com uma análise aberta, pergunta se é para
  atualizá-la ou salvar como uma nova.
- **📂 Minhas análises** — abrir, fechar, renomear, excluir e gerar o código.
  Ao abrir o link, a análise que estava aberta volta sozinha.
- **🔑 Código desta análise** — gera um código de recuperação (`BSO1-…`) para
  guardar num .txt e restaurar em outro computador ou depois de limpar o cache
  (*Minhas análises → Restaurar por código*).

## Arquivos

Um arquivo só — `index.html`, com tela, estilo e código dentro. Sem build e sem
dependência externa. Publicar é `git commit` + `git push`; o GitHub Pages
republica sozinho em cerca de um minuto.

O que a página guarda (a coleta em andamento) fica no `localStorage` do próprio
aparelho, com proteção para o caso de ele estar bloqueado — aba anônima ou
`file://` — em vez de quebrar a página.
