import pandas as pd
import hashlib
import io
import re
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from core.models import Cliente, Veiculo, Compra, Pesquisa, TipoPesquisa

def gerar_hash_compra(tenant_id: str, cliente_id: str, veiculo_id: str, data_compra: str) -> str:
    """Gera um hash único SHA-256 baseado nas chaves primárias e data."""
    raw_string = f"{tenant_id}-{cliente_id}-{veiculo_id}-{data_compra}"
    return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

# O decorator @transaction.atomic garante que ou salva TODAS as linhas do CSV, ou não salva nenhuma (evita banco corrompido)
@transaction.atomic
def processar_csv_compras(tenant, file_bytes: bytes, marca, tipo_pesquisa_nome: str):
    
    # 1. Lê o arquivo com o separador correto
    df = pd.read_csv(io.BytesIO(file_bytes), sep=';')
    
    # 2. Converte todos os nomes da coluna MODELO para maiúsculas
    if 'MODELO' in df.columns:
        df['MODELO'] = df['MODELO'].astype(str).str.upper()

    df = df.where(pd.notnull(df), None)
    
    data_compra_atual = timezone.now().date()
    inseridos = ignorados = pesquisas_criadas = 0

    # 3. Resolve o Tipo de Pesquisa dinamicamente
    # O HTML manda "venda" ou "pos_venda". Aqui a gente acha no banco ou cria na hora.
    tipo_pesquisa, _ = TipoPesquisa.objects.get_or_create(
        tenant=tenant,
        nome=tipo_pesquisa_nome.upper().replace('_', ' '),
        defaults={'descricao': f'Pesquisa importada via CSV'}
    )

    for index, row in df.iterrows():
        telefone_raw = str(row.get('TELEFONE', '')).strip()
        placa_raw = str(row.get('PLACA', '')).strip().upper()
        nome_cliente = str(row.get('NOME', '')).strip()
        cidade = str(row.get('CIDADE', '')).strip()
        modelo = str(row.get('MODELO', '')).strip()

        # LIMPEZA (Remove parênteses, traços e espaços)
        telefone = re.sub(r'\D', '', telefone_raw)
        placa = re.sub(r'[^A-Z0-9]', '', placa_raw)

        if not telefone or not placa or telefone == 'None' or placa == 'None':
            ignorados += 1
            continue

        # 4. Cliente (Pega o existente ou cria um novo na mesma linha)
        cliente, _ = Cliente.objects.get_or_create(
            tenant=tenant, 
            telefone=telefone,
            defaults={'nome': nome_cliente, 'cidade': cidade}
        )

        # 5. Veículo
        veiculo, _ = Veiculo.objects.get_or_create(
            tenant=tenant, 
            placa=placa,
            defaults={'cliente': cliente, 'marca': marca, 'modelo': modelo}
        )

        # 6. Hash (Bloqueia duplicados)
        hash_compra = gerar_hash_compra(str(tenant.id), str(cliente.id), str(veiculo.id), str(data_compra_atual))
        
        # Substitui o "db.query(Compra)..." do SQLAlchemy
        if Compra.objects.filter(tenant=tenant, hash_compra=hash_compra).exists():
            ignorados += 1
            continue

        # 7. Inserção da Compra Oficial
        nova_compra = Compra.objects.create(
            tenant=tenant,
            cliente=cliente,
            veiculo=veiculo,
            tipo_pesquisa=tipo_pesquisa,
            data_compra=data_compra_atual,
            hash_compra=hash_compra,
            loja=cidade if cidade and cidade != 'NONE' else "NÃO INFORMADA" 
        )

        # 8. Geração Automática da Pesquisa
        Pesquisa.objects.create(
            tenant=tenant,
            tipo_pesquisa=tipo_pesquisa,
            compra=nova_compra,
            expira_em=timezone.now() + timedelta(days=30)
        )
        
        inseridos += 1
        pesquisas_criadas += 1

    return {
        "status": "Sucesso",
        "novas_compras": inseridos,
        "pesquisas_geradas": pesquisas_criadas,
        "ignorados_ou_duplicados": ignorados
    }