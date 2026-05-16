from django.shortcuts import render
from core.models import Marca

def importacao_view(request):
    # Puxa todas as marcas do banco para popular o <select>
    marcas = Marca.objects.all()
    
    if request.method == 'POST':
        # Aqui é onde o Pandas vai brilhar na próxima etapa!
        arquivo = request.FILES.get('csv_file')
        marca_id = request.POST.get('marca_id')
        print(f"Recebido: {arquivo.name} para a Marca ID: {marca_id}")
        
    return render(request, 'importacao.html', {'marcas': marcas})