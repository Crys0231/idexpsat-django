from django.contrib import admin
from .models import Tenant, Cliente, Marca, Veiculo, TipoPesquisa, Compra, Pesquisa, Pergunta, Resposta

# Aqui dizemos pro Django: "Crie uma tela de gerenciamento para essas tabelas"
admin.site.register(Tenant)
admin.site.register(Cliente)
admin.site.register(Marca)
admin.site.register(Veiculo)
admin.site.register(TipoPesquisa)
admin.site.register(Compra)
admin.site.register(Pesquisa)
admin.site.register(Pergunta)
admin.site.register(Resposta)

# Customização do título do painel
admin.site.site_header = "IDEXPSAT - Administração"
admin.site.site_title = "Portal IDEXPSAT"
admin.site.index_title = "Gerenciamento de Pesquisas"