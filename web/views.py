from django.shortcuts import render
from core.models import Marca, Tenant
from core.services.data_processor import processar_csv_compras

def importacao_view(request):
    # Como estamos no MVP, vamos pegar o primeiro Tenant do banco.
    # No futuro, isso será: tenant = request.user.tenant
    tenant = Tenant.objects.first() 
    marcas = Marca.objects.filter(tenant=tenant)
    
    # Este contexto é enviado para o HTML
    contexto = {'marcas': marcas}
    
    if request.method == 'POST':
        try:
            # Coleta os dados do formulário HTML
            arquivo = request.FILES.get('csv_file')
            marca_id = request.POST.get('marca_id')
            tipo_pesquisa_nome = request.POST.get('tipo_pesquisa_id') # "venda" ou "pos_venda"
            
            # Validação rápida de segurança
            if not arquivo or not arquivo.name.endswith('.csv'):
                raise ValueError("Por favor, envie um arquivo .csv válido.")

            marca = Marca.objects.get(id=marca_id, tenant=tenant)
            file_bytes = arquivo.read()
            
            # Chama o nosso motor (Pandas)
            resultado = processar_csv_compras(tenant, file_bytes, marca, tipo_pesquisa_nome)
            
            # Passamos os resultados de volta para a tela mostrar o alert verde
            contexto['resultado'] = resultado
            contexto['sucesso'] = True
            
        except Exception as e:
            # Se a marca não existir ou o CSV der erro, capturamos aqui
            contexto['erro'] = str(e)
            contexto['sucesso'] = False
            
    return render(request, 'importacao.html', contexto)