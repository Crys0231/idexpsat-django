import uuid
from django.db import models
from django.utils import timezone

# --- Abstract Base Model ---
class BaseModel(models.Model):
    """
    Classe base que fornece UUID, timestamps de criação/atualização 
    e soft delete para todos os modelos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    # updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

# --- Entidades de Acesso ---

class Tenant(BaseModel):
    nome = models.CharField(max_length=255)

    class Meta:
        db_table = 'tenants' # <--- Conecta com a tabela existente

    def __str__(self):
        return self.nome

# --- Entidades de Negócio ---

class Cliente(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clientes')
    nome = models.CharField(max_length=255, null=True, blank=True)
    telefone = models.CharField(max_length=50)
    cidade = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return self.nome or self.telefone

class Marca(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='marcas')
    nome = models.CharField(max_length=255)

    class Meta:
        db_table = 'marcas'

    def __str__(self):
        return self.nome

class Veiculo(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='veiculos')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='veiculos')
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name='veiculos')
    placa = models.CharField(max_length=20)
    modelo = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'veiculos'

    def __str__(self):
        return f"{self.modelo} - {self.placa}"

class TipoPesquisa(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tipos_pesquisa')
    nome = models.CharField(max_length=255)
    descricao = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'tipos_pesquisa'

    def __str__(self):
        return self.nome

# --- Entidades de Operação ---

class Compra(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='compras')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='compras')
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='compras')
    tipo_pesquisa = models.ForeignKey(TipoPesquisa, on_delete=models.CASCADE, related_name='compras', null=True, blank=True)
    data_compra = models.DateField(null=True, blank=True)
    hash_compra = models.CharField(max_length=255, db_index=True)
    loja = models.CharField(max_length=255, null=True, blank=True)
    tratado = models.BooleanField(default=False)
    tratado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compras'

    def __str__(self):
        return f"Compra {self.hash_compra} - {self.cliente}"

class Pesquisa(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='pesquisas')
    tipo_pesquisa = models.ForeignKey(TipoPesquisa, on_delete=models.CASCADE, related_name='pesquisas')
    compra = models.ForeignKey(Compra, on_delete=models.SET_NULL, null=True, blank=True, related_name='pesquisas')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    respondida = models.BooleanField(default=False)
    data_resposta = models.DateTimeField(null=True, blank=True)
    
    enviada = models.BooleanField(default=False)
    data_envio = models.DateTimeField(null=True, blank=True)
    expira_em = models.DateTimeField(null=True, blank=True)

    ligacao_feita = models.BooleanField(default=False)
    ligacao_feita_por = models.CharField(max_length=255, null=True, blank=True)
    rac_aberto = models.BooleanField(default=False)
    rac_aberto_por = models.CharField(max_length=255, null=True, blank=True)
    tratado = models.BooleanField(default=False)

    class Meta:
        db_table = 'pesquisas'

    def __str__(self):
        return f"Pesquisa {self.token} - Respondida: {self.respondida}"

class Pergunta(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='perguntas')
    tipo_pesquisa = models.ForeignKey(TipoPesquisa, on_delete=models.CASCADE, related_name='perguntas', null=True, blank=True)
    pergunta = models.TextField()
    tipo_pergunta = models.CharField(max_length=50, default="scale")
    ordem = models.IntegerField(null=True, blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        db_table = 'perguntas'

    def __str__(self):
        return self.pergunta

class Resposta(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='respostas')
    pesquisa = models.ForeignKey(Pesquisa, on_delete=models.CASCADE, related_name='respostas')
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE, related_name='respostas')
    resposta = models.TextField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    sentimento = models.CharField(max_length=50, null=True, blank=True)
    temas = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'respostas'

    def __str__(self):
        return f"Resposta para {self.pergunta} (Pesquisa: {self.pesquisa.token})"

class Notificacao(BaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='notificacoes')
    pesquisa = models.ForeignKey(Pesquisa, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificacoes')
    titulo = models.CharField(max_length=255)
    conteudo = models.TextField(null=True, blank=True)
    lida = models.BooleanField(default=False)
    
    # Nota: Mapeado como string temporariamente para não conflitar com a tabela antiga de users da API
    user_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'notificacoes'

    def __str__(self):
        return self.titulo