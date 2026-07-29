# Radar Sucessório — passo a passo para colocar no ar

Este pacote já contém tudo pronto: o robô que busca as notícias e o site que
as exibe. Você só precisa "hospedar" isso no GitHub (gratuito) e ligar a
automação. Leva uns 15 minutos, sem precisar escrever nenhuma linha de código.

As notícias vêm de: STJ, STF, CNJ, IBDFAM, ConJur, Migalhas, JOTA, Valor
Econômico e Colégio Notarial do Brasil - SP, filtradas pelos termos: ITCMD,
Direito das Sucessões, Planejamento Sucessório, Inventário, Holding Familiar,
Reforma Tributária ITCMD, STJ sucessões e STF sucessões.

---

## Passo 1 — Criar uma conta no GitHub (gratuita)

1. Acesse **https://github.com/signup**
2. Crie sua conta com seu e-mail (confirme o e-mail quando pedirem)
3. Escolha o plano **Free** quando perguntarem

## Passo 2 — Criar o repositório (a "pasta" do seu site)

1. Depois de logado, clique no **+** no canto superior direito → **New repository**
2. Em "Repository name", digite: `radar-sucessorio`
3. Marque a opção **Public**
4. **Não** marque "Add a README file" (já temos um)
5. Clique em **Create repository**

## Passo 3 — Enviar os arquivos deste pacote

1. Na página do repositório recém-criado, clique no link **uploading an existing file**
   (ou vá em **Add file → Upload files**)
2. Abra a pasta `radar-sucessorio` que você recebeu (descompactada) no seu
   computador e **arraste a pasta inteira** para dentro da janela do navegador
   — o GitHub mantém a estrutura de pastas automaticamente
3. Role para baixo, escreva uma mensagem tipo "primeiro envio" em
   "Commit changes" e clique em **Commit changes**

> Confira se, depois do envio, o repositório mostra as pastas
> `.github`, `scripts`, `data` e o arquivo `index.html` na raiz. Se o
> `.github` não aparecer, repita o upload arrastando a pasta `.github`
> sozinha (alguns navegadores escondem pastas que começam com ponto).

## Passo 4 — Ativar o GitHub Pages (publicar o site)

1. No repositório, clique em **Settings** (aba no topo)
2. No menu à esquerda, clique em **Pages**
3. Em "Source", escolha **Deploy from a branch**
4. Em "Branch", escolha **main** e a pasta **/ (root)** → clique **Save**
5. Aguarde 1–2 minutos. O GitHub vai te mostrar o endereço do seu site,
   algo como: `https://seu-usuario.github.io/radar-sucessorio/`

## Passo 5 — Rodar o robô pela primeira vez

Por padrão o robô roda sozinho todo dia às 08h (Brasília), mas o GitHub só
começa a contar esse horário depois do primeiro envio — então vamos disparar
manualmente uma vez para o site já nascer com notícias:

1. No repositório, clique na aba **Actions**
2. Se aparecer um aviso pedindo para habilitar workflows, clique em
   **I understand my workflows, go ahead and enable them**
3. Clique em **Atualizar notícias diárias** na lista à esquerda
4. Clique no botão **Run workflow** (à direita) → **Run workflow** novamente
   para confirmar
5. Aguarde cerca de 1 minuto e atualize a página — deve aparecer um ✅ verde

Pronto! Acesse o link do Passo 4 — o site já deve mostrar as notícias
encontradas.

## E depois disso?

Você não precisa fazer mais nada. Todo dia, automaticamente, o GitHub vai:

1. Rodar o robô de busca
2. Atualizar o `index.html` com as notícias novas
3. Publicar a atualização no site

Se quiser forçar uma atualização fora do horário programado, repita o
**Passo 5** a qualquer momento.

## Personalizações simples

Tudo o que pode ser ajustado está no topo do arquivo
`scripts/fetch_news.py`, dentro do repositório no GitHub (clique no arquivo →
ícone de lápis para editar):

- **`KEYWORDS`** — lista de termos de busca
- **`FONTES_CONFIAVEIS`** — lista de sites monitorados
- **`DIAS_NA_HOME`** — quantos dias de notícias ficam visíveis na página

Depois de editar, clique em **Commit changes** — na próxima execução
automática (ou ao rodar manualmente pelo Passo 5) as mudanças já valem.

## Limitações importantes

- O robô usa o Google Notícias como "motor de busca", restringindo os
  resultados aos domínios da sua lista. Isso é mais confiável do que tentar
  ler o feed RSS de cada site individualmente, porque nem todos os sites
  (como STF e o Colégio Notarial) publicam RSS próprio.
- Sites que exigem assinatura (como o Valor Econômico) vão aparecer apenas
  com título e link — o conteúdo completo fica atrás do login deles, isso é
  esperado e não tem como contornar.
- Se quiser abrir mão de qualquer termo pouco relevante ou adicionar novos
  (ex: "ITBI", "usufruto", "doação em vida"), é só editar a lista `KEYWORDS`.
