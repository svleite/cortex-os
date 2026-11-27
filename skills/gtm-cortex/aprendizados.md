# Aprendizados do gtm-cortex

Memória da skill. Ler antes de criar receita nova ou mexer em container de cliente.
Uma entrada por aprendizado: o que aconteceu e a regra que ficou. Nada de ID de cliente aqui (repositório público).

## API do Tag Manager

- **conversionId do Google Ads vai só com os dígitos.** Com o prefixo `AW-`, a tag salva mas não dispara. O rótulo vai separado em `conversionLabel`.
- **`measurementIdOverride` do evento GA4 não aceita variável.** A API recusa `{{...}}` com "Please enter a valid measurement ID"; vai o `G-` literal.
- **Nome de tag ou gatilho não aceita `:`.** Usar ` - ` como separador.
- **Variáveis nativas recusadas pela API:** `scrollDirection` e `pageTitle` voltam 400 `Invalid value at 'type'`. Para título da página, criar variável própria.
- **Gatilhos nativos têm ID fixo:** Todas as páginas `2147479553`; Inicialização (todas as páginas) `2147479573`. A tag do Google (`googtag`) vai na Inicialização.
- **`googtag` substitui a antiga configuração do GA4 (`gaawc`).** Para containers novos, usar `googtag` com `tagId`.
- **Publicar consome o workspace.** Depois de criar a versão, o GTM abre um workspace novo: nunca guardar o ID do workspace.
- **Escopos do OAuth atuais não incluem exclusão de workspace** (`tagmanager.delete.containers`). Apagar tag ou gatilho dentro do workspace funciona; apagar o workspace inteiro não. Workspace de teste se apaga pela interface.
- **Container gratuito tem limite de 3 workspaces.** Conferir antes de criar workspace de teste.
- **Cota por minuto:** a API devolve 429 em rajadas; a biblioteca espera e tenta de novo (até 3 vezes).

## Plataformas e plugins

- **Joinchat (botão de WhatsApp do WordPress) já avisa o GTM:** no clique faz `dataLayer.push({event: 'JoinChat'})` e abre o WhatsApp por `window.open`, sem link clicável. Por isso a receita `lead-whatsapp` usa dois gatilhos: o evento personalizado `JoinChat` e o clique em links `wa.me` soltos na página.
- **Joinchat + tag do Google instalada direto no código do site = `generate_lead` duplicado** (o próprio Joinchat manda o evento quando acha o gtag). Regra: toda tag do Google dentro do GTM, nada de gtag fixo no site.
- **Duplicata com outro nome:** containers montados à mão costumam ter vinculador, tag do Google ou pixel com nomes livres. As receitas comparam pela função (tipo + ID), não só pelo nome, e apontam o equivalente existente em vez de criar outro.
