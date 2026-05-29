# Escolher e preparar a VPS

O bot precisa de um host **always-on** (conexão WhatsApp viva 24/7 + cron). Não roda em serverless (Cloudflare Workers etc.) porque a conexão do Evolution é um processo persistente. Latência não importa: o resumo é 1x/dia, não tempo real.

Alvo: **2 vCPU / 2-4 GB RAM**, Docker.

## Opções

| Provedor | Preço (~2-4GB) | Comunidade | Observação |
|---|---|---|---|
| Hetzner | ~€4,5/mês | Grande | Melhor custo. Cobra em euro. |
| DigitalOcean | ~US$6-12/mês | A maior | Tutorial pra tudo. |
| Vultr / AWS Lightsail | ~US$6-10/mês | Grande | Têm datacenter no Brasil. |
| Hostinger VPS | ~R$40/mês | BR | Cobra em BRL, suporte PT. |
| Oracle Cloud Free (ARM A1) | **grátis** | Média | Cota ARM generosa (até 4 OCPU/24GB). Risco de reclaim se a conta ficar ociosa. |
| Contabo | ~€5/mês | Média | Muita RAM barata, suporte fraco. |

## Recomendação

- Quer custo zero e topa o risco: **Oracle Free ARM A1** (some a instância se a conta for considerada ociosa; mantenha algo rodando).
- Quer estável e barato: **Hetzner**.
- Quer tudo em real com suporte PT: **Hostinger**.

## Instalar Docker (Ubuntu)

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER   # relogar depois
```

## Segurança

- Libere só a porta **22 (SSH)**. O Evolution fica no localhost (`127.0.0.1:8080`), acessado por túnel SSH. Não exponha 8080 na internet.
- Se já roda outra coisa sensível na conta (ex: um cofre de senhas), use uma **instância separada** pro bot. Não misture um bot não-oficial de WhatsApp com dados sensíveis.
