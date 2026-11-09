# Triplo de Costas

Mini-site da nossa liga ESPN Fantasy NBA. Atualiza-se sozinho todas as manhãs, às 9h07 de Lisboa, com as estatísticas e o comentário do Claude.

Tudo o que está abaixo faz-se no site do GitHub, nesta página do projeto.

## Atualizar agora, sem esperar pela manhã

1. Carrega em **Actions**, no menu de cima.
2. À esquerda, carrega em **Atualização diária**.
3. À direita, carrega em **Run workflow** e outra vez em **Run workflow**.

## Mudar a hora

1. Abre o ficheiro `.github/workflows/diario.yml`.
2. Carrega no lápis, em cima à direita.
3. Na linha `cron: "7 9 * * *"`, o primeiro número são os minutos e o segundo é a hora de Lisboa. Para 8h22, por exemplo, fica `cron: "22 8 * * *"`.
4. Carrega em **Commit changes**.

Não uses o minuto 0, porque é quando o GitHub costuma ter mais atrasos. Não marques antes das 8h, para a ESPN ter tempo de fechar os números.

As duas linhas `cron` seguintes são reservas, para o caso de o GitHub saltar a corrida principal. Só fazem alguma coisa se a atualização do dia ainda faltar, por isso é normal veres corridas curtas sem nada feito. Se mudares a hora principal, mantém as reservas mais tarde.

## Pausar e voltar a ligar

1. Carrega em **Actions** e, à esquerda, em **Atualização diária**.
2. Carrega nos três pontos, em cima à direita.
3. Escolhe **Disable workflow** para pausar e **Enable workflow** para voltar a ligar.

O site continua aberto durante a pausa, com os últimos números.

## Renovar o token do Claude

O token dura 1 ano. Quando acabar, o site continua a sair, mas sem comentário.

1. No PC, abre um terminal e corre `claude setup-token`.
2. Autoriza no navegador e copia o token que aparece no terminal.
3. No GitHub, carrega em **Settings**, depois **Secrets and variables** e **Actions**.
4. Em `CLAUDE_CODE_OAUTH_TOKEN`, carrega no lápis, cola o token novo e carrega em **Update secret**.

O token é como uma palavra-passe: não o envies a ninguém nem o escrevas em nenhum ficheiro.

## Quando alguma coisa falha

- **Comentário falhou:** o site sai na mesma, com uma nota no lugar do comentário.
- **ESPN falhou:** o site sai com os últimos números e o aviso "Dados de ontem", e o GitHub envia um email de falha.

## Coisas a saber

- O GitHub desliga o agendamento ao fim de 60 dias sem atividade. Os dados guardados todas as manhãs contam como atividade, por isso só precisa de atenção se pausares durante muito tempo.
- O número da liga está em `config.json`, tal como a equipa que fica de fora do site e do comentário (`equipas_fantasma`) e os nomes com que o comentário trata os donos (`donos`). Para a próxima época, muda lá também `ano_api`.
- A liga tem de continuar visível ao público na ESPN, senão os dados deixam de chegar.
- Para acrescentar um bloco de estatísticas, junta um ficheiro em `src/blocos/` e regista-o em `src/blocos/__init__.py`.
- Para mudar o que aparece em cada menu do site, altera as listas em `src/seccoes.py`.
