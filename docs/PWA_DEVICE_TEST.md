# Teste da PWA em dispositivos reais

Executar primeiro no ambiente `dev`. Usar apenas dados de teste: nao introduzir nomes, contactos, informacao clinica ou relatos reais. Registar modelo do dispositivo, versao do sistema, navegador, data e resultado.

## Preparacao

1. Confirmar que o dispositivo tem ligacao a Internet e que nao existe uma instalacao antiga da aplicacao.
2. Abrir o URL `dev` autorizado diretamente no navegador indicado.
3. Confirmar que a pagina mostra a meditacao da data atual em Cabo Verde.
4. Percorrer Meditacao, Jornada, Viver Saudavel, Ajuda e Sobre pela navegacao inferior.
5. Confirmar que a barra inferior nao tapa o ultimo conteudo de nenhuma area.

## Android com Chrome

1. Abrir `Mais > Aplicacao e notificacoes`.
2. Tocar em `Instalar aplicacao`; se o prompt nao aparecer, tocar em `Como instalar` e seguir a indicacao do menu do Chrome.
3. Abrir a aplicacao pelo icone criado no dispositivo.
4. Confirmar que abre sem a barra normal do navegador e inicia em Meditacao.
5. Fechar completamente a aplicacao, desligar Wi-Fi e dados moveis e voltar a abrir.
6. Confirmar que Meditacao, Jornada, Ajuda, Sobre, `/expo` e `/privacidade` continuam acessiveis.
7. Voltar a ligar a Internet e confirmar que a aplicacao recupera sem perder os dados locais de teste.

## iPhone ou iPad com Safari

1. Abrir `Mais > Aplicacao e notificacoes` e tocar em `Como instalar`.
2. No Safari, tocar em Partilhar e depois em `Adicionar ao ecra principal`.
3. Abrir a aplicacao pelo icone criado no dispositivo.
4. Confirmar que abre em modo autonomo, com titulo e icone corretos.
5. Repetir o teste offline descrito para Android.
6. Confirmar que o menu inferior respeita a area segura do ecra e nao fica por baixo do indicador de inicio.
7. Rodar o dispositivo e confirmar que a aplicacao continua utilizavel em paisagem, sem forcar o regresso a vertical.

## Dados e continuidade

1. Guardar uma gratidao de teste, um check-in e uma data de sobriedade ficticia.
2. Fechar e reabrir a aplicacao; confirmar que os tres valores continuam no mesmo dispositivo.
3. Exportar a Jornada e confirmar que e descarregado um ficheiro JSON.
4. Noutro perfil ou dispositivo de teste, importar a copia e aceitar a substituicao apenas quando o aviso aparecer.
5. Confirmar que Sala Anonima e preferencias de notificacao nao atravessam a copia.

## Mudanca de dia e atualizacao

1. Deixar a aplicacao aberta durante uma mudanca de dia em Cabo Verde ou regressar a ela depois da mudanca.
2. Confirmar que a data, a meditacao e o apoio diario mudam sem ser necessario limpar dados.
3. Com uma versao nova publicada em `dev`, abrir `Mais` e confirmar que aparece `Atualizar aplicacao`.
4. Tocar no botao e confirmar que a aplicacao recarrega uma vez e mantem os dados locais.
5. Repetir uma abertura offline para confirmar que a nova cache ficou ativa.

## Notificacoes

1. Autorizar notificacoes apenas no dispositivo de teste.
2. Escolher uma hora alguns minutos adiante em Jornada.
3. Com o push ainda desativado, confirmar que o texto explica que o lembrete local depende da aplicacao aberta.
4. Confirmar que nenhuma notificacao mostra check-in, gratidao, data de sobriedade ou outro dado privado.
5. Desativar as notificacoes em `Mais` e confirmar que o estado muda na Jornada.

## Criterio de aprovacao

O dispositivo passa quando todos os passos aplicaveis funcionam sem perda de dados, sobreposicao visual, ecra vazio ou exposicao de informacao privada. Qualquer falha deve incluir dispositivo, sistema, navegador, passos exatos e captura sem dados pessoais.
