import streamlit as st
import pandas as pd
from datetime import datetime
from io import StringIO

st.set_page_config(page_title="Dashboard Financeiro", layout="wide")

# Função corrigida (NÃO divide o valor pelas parcelas)
def desmembrar_parcelas(df, vencimento_dia=10):
    linhas_expandidas = []
    for _, row in df.iterrows():
        if pd.isna(row["ITEM"]) or str(row["ITEM"]).strip() == "":
            continue

        # Trata data base
        data_base_csv = str(row.get("DATA", "")).strip()
        if data_base_csv not in ["", "nan"]:
            try:
                data_base = datetime.strptime(data_base_csv, "%d/%m/%Y")
            except:
                data_base = datetime.now().replace(day=vencimento_dia)
        else:
            data_base = datetime.now().replace(day=vencimento_dia)

        # Trata valor (MANTÉM o valor original para cada parcela)
        valor_str = str(row["VALOR"]).replace("R$", "").replace(",", ".").strip()
        try:
            valor_parcela = float(valor_str)  # Valor total repetido em cada parcela
        except:
            continue

        # Trata parcelas
        parcelas_info = str(row.get("PARCELAS", "1/1")).strip()
        if "/" in parcelas_info:
            try:
                atual, total = map(int, parcelas_info.split("/"))
            except:
                atual, total = 1, 1
        else:
            atual, total = 1, 1

        # Gera uma linha para cada parcela
        for i in range(total):
            data_parcela = data_base + pd.DateOffset(months=i)
            if data_base_csv not in ["", "nan"] and i == 0:
                data_parcela = data_base  # Mantém a data original se existir
            else:
                data_parcela = data_parcela.replace(day=vencimento_dia)

            linhas_expandidas.append({
                "ITEM": row["ITEM"],
                "PARCELA": f"{i+1}/{total}",
                "VALOR": valor_parcela,  # Mesmo valor para todas as parcelas
                "CATEGORIA": row.get("CATEGORIA", ""),
                "FORMA DE PAGAMENTO": row["FORMA DE PAGAMENTO"],
                "DATA": data_parcela
            })
    return pd.DataFrame(linhas_expandidas)

# Upload do arquivo
uploaded_file = st.file_uploader("Carregue seu arquivo CSV", type="csv")

if uploaded_file is not None:
    try:
        # Lê o arquivo
        string_data = StringIO(uploaded_file.getvalue().decode('utf-8'))
        df_raw = pd.read_csv(string_data)
        
        # Processamento
        df_raw = df_raw[df_raw["ITEM"].notna() & (df_raw["ITEM"] != "")]
        df = desmembrar_parcelas(df_raw)
        
        # Filtro por mês
        df["DATA"] = pd.to_datetime(df["DATA"])
        df["MÊS"] = df["DATA"].dt.strftime("%Y-%m")
        meses_disponiveis = sorted(df["MÊS"].unique().tolist(), reverse=True)
        
        if meses_disponiveis:
            mes_selecionado = st.selectbox("Selecione o Mês", meses_disponiveis)
            df_mes = df[df["MÊS"] == mes_selecionado]

            # Layout
            st.title(f"📊 Dashboard Financeiro - {mes_selecionado}")

            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                total_gasto = df_mes["VALOR"].sum()
                st.metric("Total Gasto", f"R$ {total_gasto:,.2f}".replace(".", "~").replace(",", ".").replace("~", ","))
            
            with col2:
                num_transacoes = len(df_mes)
                st.metric("Nº de Transações", num_transacoes)
            
            with col3:
                valor_medio = total_gasto / num_transacoes if num_transacoes > 0 else 0
                st.metric("Valor Médio", f"R$ {valor_medio:,.2f}".replace(".", "~").replace(",", ".").replace("~", ","))

            # Gráficos
            st.subheader("Distribuição por Forma de Pagamento")
            por_cartao = df_mes.groupby("FORMA DE PAGAMENTO")["VALOR"].sum().reset_index()
            st.bar_chart(por_cartao.set_index("FORMA DE PAGAMENTO"), y="VALOR")

            # Tabela detalhada
            st.subheader("Detalhamento das Despesas")
            st.dataframe(
                df_mes.sort_values("DATA")[["ITEM", "PARCELA", "VALOR", "FORMA DE PAGAMENTO", "DATA"]],
                use_container_width=True,
                column_config={
                    "VALOR": st.column_config.NumberColumn(format="R$ %.2f"),
                    "DATA": st.column_config.DateColumn(format="DD/MM/YYYY")
                },
                hide_index=True
            )
        else:
            st.warning("Nenhum dado válido encontrado no arquivo.")
            
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
else:
    st.info("Por favor, carregue um arquivo CSV para começar.")