
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

def calcular_valor_futuro_com_aporte(capital_inicial, taxa_juros_mensal, meses_total, valor_mensal, meses_aporte):
    taxa = taxa_juros_mensal / 100
    saldo = capital_inicial
    for mes in range(1, meses_total + 1):
        saldo *= (1 + taxa)
        if mes <= meses_aporte:
            saldo += valor_mensal
    return saldo

def calcular_valor_futuro_com_retirada(capital_inicial, taxa_juros_mensal, meses_total, valor_mensal, meses_retirada):
    taxa = taxa_juros_mensal / 100
    saldo = capital_inicial
    for mes in range(1, meses_total + 1):
        saldo *= (1 + taxa)
        if mes <= meses_retirada:
            saldo -= valor_mensal
    return saldo

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

def calcular_saldos_mensais(capital_inicial, taxa_juros_mensal, meses_total, valor_mensal, meses_movimentacao, tipo_movimento):
    taxa = taxa_juros_mensal / 100
    saldo = capital_inicial
    saldos = [saldo]
    dividendos = [0]
    for mes in range(1, meses_total + 1):
        rendimento = saldo * taxa
        saldo += rendimento
        if mes <= meses_movimentacao:
            if tipo_movimento == "aportes":
                saldo += valor_mensal
            elif tipo_movimento == "retiradas":
                saldo -= valor_mensal
        saldos.append(saldo)
        dividendos.append(rendimento)
    return saldos, dividendos

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

def buscar_cdi_open_finance():
    try:
        url = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoCDIUltimoDia?$format=json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            valor = float(data['value'][0]['valor'])
            return valor
    except Exception as e:
        st.warning(f"Erro ao buscar CDI (Open Finance): {e}")
    return None

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
        "CDI (via Open Finance API)",
        "IPCA (manual)",
        "IGP-M (manual)"
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
    elif indexador == "CDI (via Open Finance API)":
        taxa_cdi = buscar_cdi_open_finance()
        if taxa_cdi:
            taxa_final = ((1 + taxa_cdi / 100) ** (1 / 12) - 1) * 100
            st.info(f"📌 CDI anual: {taxa_cdi:.2f}% → mensal composta: {taxa_final:.4f}%")
        else:
            st.error("Erro ao obter CDI. Usando taxa padrão de 1% ao mês.")
            taxa_final = 1.0
    else:
        taxa_final = st.number_input(f"📉 Informe a taxa para {indexador} (% ao mês)", value=1.0, min_value=0.0)

    if st.button("Calcular"):
        if tipo == "aportes":
            resultado = calcular_valor_futuro_com_aporte(capital, taxa_final, meses, valor_mensal, meses_mov)
        elif tipo == "retiradas":
            resultado = calcular_valor_futuro_com_retirada(capital, taxa_final, meses, valor_mensal, meses_mov)
        else:
            resultado = capital * ((1 + taxa_final / 100) ** meses)

        st.success(f"💰 Valor final ao fim de {meses} meses: R$ {resultado:,.2f}")

        if calcular_meta:
            meses_meta = calcular_meses_ate_alvo(capital, taxa_final, valor_mensal, meses_mov, tipo, 100_000_000)
            if meses_meta:
                anos = meses_meta // 12
                resto = meses_meta % 12
                st.info(f"🎯 Alcançará R$ 100 milhões em {meses_meta} meses ({anos} anos e {resto} meses)")
            else:
                st.warning("⚠️ Não é possível alcançar R$ 100 milhões com esses parâmetros.")

        if mostrar_grafico:
            if tipo in ["aportes", "retiradas"]:
                saldos, dividendos = calcular_saldos_mensais(capital, taxa_final, meses, valor_mensal, meses_mov, tipo)
            else:
                saldos = [capital * ((1 + taxa_final / 100) ** i) for i in range(meses + 1)]
                dividendos = [saldos[i] * (taxa_final / 100) for i in range(len(saldos) - 1)] + [0]

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(range(len(saldos)), saldos, marker='o')
            ax.set_title("Evolução do Capital")
            ax.set_xlabel("Mês")
            ax.set_ylabel("Saldo (R$)")
            ax.grid(True)
            st.pyplot(fig)

            st.subheader("📋 Tabela de Dividendos")
            df = pd.DataFrame({"Mês": list(range(len(dividendos))), "Dividendos (R$)": dividendos})
            st.dataframe(df)

if __name__ == "__main__":
    main()
