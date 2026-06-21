from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from core.models import Marca, Tenant, Pesquisa, Compra

def importacao_view(request):
    """View responsável por renderizar a tela e processar o upload do CSV."""
    tenant = Tenant.objects.first() 
    marcas = Marca.objects.filter(tenant=tenant)
    contexto = {'marcas': marcas}
    
    if request.method == 'POST':
        try:
            from core.services.data_processor import processar_csv_compras
            arquivo = request.FILES.get('csv_file')
            marca_id = request.POST.get('marca_id')
            tipo_pesquisa_nome = request.POST.get('tipo_pesquisa_id')
            
            if not arquivo or not arquivo.name.endswith('.csv'):
                raise ValueError("Por favor, envie um arquivo .csv válido.")

            marca = Marca.objects.get(id=marca_id, tenant=tenant)
            file_bytes = arquivo.read()
            
            resultado = processar_csv_compras(tenant, file_bytes, marca, tipo_pesquisa_nome)
            contexto['resultado'] = resultado
            contexto['sucesso'] = True
            
        except Exception as e:
            contexto['erro'] = str(e)
            contexto['sucesso'] = False
            
    return render(request, 'importacao.html', contexto)


def crm_clientes_view(request):
    """View principal do CRM que lista as pesquisas, calcula métricas e aplica filtros."""
    tenant = Tenant.objects.first()
    marcas = Marca.objects.filter(tenant=tenant)
    
    # Busca todas as pesquisas trazendo os relacionamentos de forma otimizada (Evita o problema de query N+1)
    pesquisas = Pesquisa.objects.filter(tenant=tenant).select_related(
        'compra__cliente', 
        'compra__veiculo__marca', 
        'tipo_pesquisa'
    ).order_by('-created_at')
    
    # 1. Captura os filtros vindos da URL (Request GET)
    busca = request.GET.get('busca', '').strip()
    marca_id = request.GET.get('marca_id', '').strip()
    status_filtro = request.GET.get('status', '').strip()
    
    # 2. Aplica os filtros na query do banco de dados se eles existirem
    if busca:
        pesquisas = pesquisas.filter(
            Q(compra__cliente__nome__icontains=busca) |
            Q(compra__cliente__telefone__icontains=busca) |
            Q(compra__veiculo__placa__icontains=busca)
        )
        
    if marca_id:
        pesquisas = pesquisas.filter(compra__veiculo__marca_id=marca_id)
        
    # 3. Cálculo das Métricas do Painel (Antes de filtrar por status, para o painel não zerar)
    total_pesquisas = pesquisas.count()
    total_respondidas = pesquisas.filter(respondida=True).count()
    total_criticos = pesquisas.filter(respondida=False, tratado=False).count()
    
    # 4. Aplica o filtro de abas (Status) na listagem
    if status_filtro == 'respondidas':
        pesquisas = pesquisas.filter(respondida=True)
    elif status_filtro == 'criticos':
        pesquisas = pesquisas.filter(respondida=False, tratado=False)
        
    # 5. Monta o contexto para enviar para o HTML
    contexto = {
        'pesquisas': pesquisas,
        'marcas': marcas,
        'busca': busca,
        'marca_selecionada': marca_id,
        'status_selecionado': status_filtro,
        'metricas': {
            'total': total_pesquisas,
            'respondidas': total_respondidas,
            'criticos': total_criticos,
        }
    }
    
    # Se a requisição vier via HTMX, nós não precisamos renderizar a página inteira,
    # apenas o pedaço da tabela que mudou! (Faremos esse arquivo parcial logo em seguida)
    if request.headers.get('HX-Request'):
        return render(request, 'partials/tabela_clientes.html', contexto)
        
    return render(request, 'clientes.html', contexto)


def alternar_tratado_view(request, pesquisa_id):
    """Ação rápida do HTMX para marcar como Tratado/Pendente sem recarregar a tela."""
    if request.method == 'POST':
        tenant = Tenant.objects.first()
        pesquisa = get_object_or_404(Pesquisa, id=pesquisa_id, tenant=tenant)
        
        # Inverte o status atual no banco
        pesquisa.tratado = not pesquisa.tratado
        pesquisa.save()
        
        # Devolvemos apenas o elemento HTML do botão atualizado. O HTMX substitui na tela na hora!
        if pesquisa.tratado:
            return HttpResponse(
                '<button class="px-3 py-1 text-xs font-bold rounded bg-green-900 border border-green-500 text-green-200">✅ Tratado</button>'
            )
        else:
            return HttpResponse(
                '<button class="px-3 py-1 text-xs font-bold rounded bg-amber-900 border border-amber-500 text-amber-200">⚠️ Pendente</button>'
            )
    return HttpResponse(status=405)