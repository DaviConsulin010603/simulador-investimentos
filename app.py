
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

FRED_API_KEY = "f4b558fccbf4b6b5104773899e01ed10"

def format_brl(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def buscar_ipca_fred(api_key):
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FPCPITOTLZGBRA&api_key={api_key}&file_type=json&observation_start=2023-01-01"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            valores = [float(obs['value']) for obs in data['observations'] if obs['value'] != "."]
            if valores:
                media_anual = sum(valores[-12:]) / 12
                return media_anual
    except Exception as e:
        st.warning(f"Erro ao buscar IPCA no FRED: {e}")
    return None

def buscar_selic_brasilapi():
    try:
        url = "https://brasilapi.com.br/api/taxas/v1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            taxas = response.json()
            for t in taxas:
                if t['nome'].lower() == 'selic':
                    return float(t['valor'])
    except Exception as e:
        st.warning(f"Erro ao buscar SELIC na BrasilAPI: {e}")
    return None

def calcular_meses_ate_alvo(capital_inicial, taxa_juros_mensal, valor_mensal, meses_movimentacao, tipo_movimento, alvo):
    taxa = taxa_juros_mensal / 100
    saldo = capital_inicial
    mes = 0
    while saldo < alvo and mes <= 10000:
        saldo *= (1 + taxa)
        if mes < meses_movimentacao:
            if tipo_movimento == "aportes":
                saldo += valor_mensal
            elif tipo_movimento == "retiradas":
                saldo -= valor_mensal
        mes += 1
        if saldo <= 0:
            return None
    return mes if saldo >= alvo else None

def calcular_detalhado(capital_inicial, taxa_mensal, meses_total, valor_mensal, meses_movimentacao, tipo_movimento):
    taxa = taxa_mensal / 100
    saldo = capital_inicial
    dados = []

    for mes in range(meses_total + 1):
        dividendos = saldo * taxa if mes > 0 else 0
        saldo += dividendos

        if tipo_movimento == "aportes" and mes > 0 and mes <= meses_movimentacao:
            movimento = valor_mensal
            saldo += valor_mensal
            aporte_real = valor_mensal
        elif tipo_movimento == "retiradas" and mes > 0 and mes <= meses_movimentacao:
            movimento = -valor_mensal
            saldo -= valor_mensal
            aporte_real = 0
        else:
            movimento = 0
            aporte_real = 0

        dados.append({
            "Mês": mes,
            "Dividendos (R$)": format_brl(dividendos),
            "Aporte/Retirada (R$)": format_brl(movimento),
            "Valor Aportado no Mês (R$)": format_brl(aporte_real),
            "Valor Total Investido (R$)": format_brl(saldo)
        })

    return pd.DataFrame(dados)

def main():
    st.title("📈 Simulador de Investimentos com Juros Compostos")

    capital = st.number_input("💵 Capital inicial (R$)", value=10000.0, min_value=0.0)
    meses = st.number_input("⏳ Total de meses", value=240, min_value=1)
    tipo = st.selectbox("💼 Tipo de movimentação", ["nenhum", "aportes", "retiradas"])
    valor_mensal = st.number_input("💸 Valor mensal (R$)", value=1000.0)
    meses_mov = st.slider("📆 Meses com movimentação", min_value=0, max_value=600, value=12)
    mostrar_grafico = st.checkbox("📊 Mostrar gráfico de evolução", value=True)
    calcular_meta = st.checkbox("🎯 Calcular tempo para atingir R$ 100 milhões")

    indexador = st.selectbox("📊 Escolha o indexador:", [
        "Taxa personalizada (%)",
        "SELIC (via BrasilAPI)",
        "IPCA (via FRED)"
    ])

    taxa_final = 1.0

    if indexador == "Taxa personalizada (%)":
        taxa_final = st.number_input("📉 Informe a taxa personalizada (% ao mês)", value=1.0, min_value=0.0)
    elif indexador == "SELIC (via BrasilAPI)":
        taxa_selic = buscar_selic_brasilapi()
        if taxa_selic:
            taxa_final = ((1 + taxa_selic / 100) ** (1 / 12) - 1) * 100
            st.info(f"📌 SELIC anual: {taxa_selic:.2f}% → mensal composta: {taxa_final:.4f}%")
        else:
            st.error("Erro ao obter SELIC. Usando taxa padrão de 1% ao mês.")
            taxa_final = 1.0
    elif indexador == "IPCA (via FRED)":
        taxa_ipca = buscar_ipca_fred(FRED_API_KEY)
        if taxa_ipca:
            taxa_final = ((1 + taxa_ipca / 100) ** (1 / 12) - 1) * 100
            st.info(f"📌 IPCA anual: {taxa_ipca:.2f}% → mensal composta: {taxa_final:.4f}%")
        else:
            st.error("Erro ao obter IPCA. Usando taxa padrão de 1% ao mês.")
            taxa_final = 1.0

    if st.button("Calcular"):
        df = calcular_detalhado(capital, taxa_final, meses, valor_mensal, meses_mov, tipo)
        valor_final_raw = df.iloc[-1]["Valor Total Investido (R$)"]
        st.success(f"💰 Valor final ao fim de {meses} meses: R$ {valor_final_raw}")

        if calcular_meta:
            meses_meta = calcular_meses_ate_alvo(capital, taxa_final, valor_mensal, meses_mov, tipo, 100_000_000)
            if meses_meta:
                anos = meses_meta // 12
                resto = meses_meta % 12
                st.info(f"🎯 Alcançará R$ 100 milhões em {meses_meta} meses ({anos} anos e {resto} meses)")
            else:
                st.warning("⚠️ Não é possível alcançar R$ 100 milhões com esses parâmetros.")

        if mostrar_grafico:
            st.warning("Gráfico desabilitado com strings formatadas. Podemos ajustar para reativar.")

        st.subheader("📋 Detalhamento Mês a Mês")
        st.dataframe(df)

if __name__ == "__main__":
    main()
