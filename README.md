# Triplo de Costas

Mini-site da nossa liga ESPN Fantasy NBA. Atualiza-se sozinho todas as manhãs, pouco depois das 9h de Lisboa, com as estatísticas e o comentário do Claude.

Tudo o que está abaixo faz-se no site do GitHub, nesta página do projeto.

## Atualizar agora, sem esperar pela manhã

1. Carrega em **Actions**, no menu de cima.
2. À esquerda, carrega em **Atualização diária**.
3. À direita, carrega em **Run workflow** e outra vez em **Run workflow**.

## Como funciona a hora

O GitHub não cumpre horas marcadas: neste projeto, cada tentativa agendada chega umas 7 horas depois da hora marcada, e a hora muda de dia para dia. Por isso o robô tem uma tentativa marcada para cada 20 minutos do dia e só trabalha na primeira que chegar depois das 9h de Lisboa. As outras acabam em segundos, sem fazer nada, e é normal veres dezenas dessas por dia na lista.

Se uma tentativa não chegar ao fim (a ESPN em baixo ou o comentário a falhar, por exemplo), o robô volta a tentar 1 hora depois, e a seguir com 2, 3 e 4 horas de intervalo. O ficheiro `dados/tentativa.json` é onde ele aponta quantas vezes já tentou nesse dia.

Para mudar a hora, abre `src/ja_atualizado.py`, carrega no lápis e muda a linha `HORA_DE_ABRIR = time(9, 0)`. Não marques antes das 9h, para a ESPN ter tempo de fechar os números. As linhas `cron` do ficheiro `.github/workflows/diario.yml` não são a hora da atualização: são só as tentativas, e não precisam de ser mexidas.

Se a atualização só correr depois das 11h, o site é publicado na mesma e o GitHub envia um email de falha, para saberes do atraso.

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
