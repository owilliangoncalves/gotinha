# Gotinha

> **Sistema de Retrieval-Augmented Generation (RAG) para profissionais da Atenção Primária à Saúde (APS) do Sistema Único de Saúde (SUS).**

O objetivo é que o profissional encontre informação de forma **rápida e assertiva**, com respostas fundamentadas **exclusivamente** na base documental oficial fornecida.

---

## ✨ Características

- **Grounding estrito**: Respostas derivam apenas dos trechos recuperados da base documental — sem conhecimento paramétrico nem internet.
- **Citação obrigatória**: Toda afirmação referencia o documento de origem (título, seção, página).
- **LGPD por design**: Logs anonimizados, nada persistido sem tratamento.

---

## 🚀 Quick Start

```bash
# 1. Clone e entre no diretório
cd gotinha

# 2. Instale dependências (requer uv)
make install

# 3. Suba o servidor de desenvolvimento
make dev

# 4. Acesse http://localhost:8000
```

---