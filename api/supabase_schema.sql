-- Schema para o banco de dados de vendas no Supabase
-- Execute este SQL no Supabase SQL Editor

-- Criar tabela de vendas
CREATE TABLE IF NOT EXISTS vendas (
    id BIGSERIAL PRIMARY KEY,
    data DATE NOT NULL,
    id_transacao TEXT NOT NULL,
    produto TEXT NOT NULL,
    categoria TEXT NOT NULL,
    regiao TEXT NOT NULL,
    quantidade NUMERIC NOT NULL,
    preco_unitario NUMERIC NOT NULL,
    receita_total NUMERIC NOT NULL,
    mes_origem TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Criar índices para melhorar performance de queries
CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(data);
CREATE INDEX IF NOT EXISTS idx_vendas_produto ON vendas(produto);
CREATE INDEX IF NOT EXISTS idx_vendas_categoria ON vendas(categoria);
CREATE INDEX IF NOT EXISTS idx_vendas_regiao ON vendas(regiao);
CREATE INDEX IF NOT EXISTS idx_vendas_mes_origem ON vendas(mes_origem);
CREATE INDEX IF NOT EXISTS idx_vendas_id_transacao ON vendas(id_transacao);

-- Criar função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Criar trigger para atualizar updated_at
CREATE TRIGGER update_vendas_updated_at BEFORE UPDATE ON vendas
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Habilitar Row Level Security (RLS)
ALTER TABLE vendas ENABLE ROW LEVEL SECURITY;

-- Criar política para permitir leitura e escrita com service_role key
-- (você pode ajustar conforme suas necessidades de segurança)
CREATE POLICY "Enable all access for service role" ON vendas
FOR ALL
USING (true)
WITH CHECK (true);

-- Comentários nas colunas para documentação
COMMENT ON TABLE vendas IS 'Tabela de dados de vendas da Alpha Insights';
COMMENT ON COLUMN vendas.data IS 'Data da transação de venda';
COMMENT ON COLUMN vendas.id_transacao IS 'Identificador único da transação';
COMMENT ON COLUMN vendas.produto IS 'Nome do produto vendido';
COMMENT ON COLUMN vendas.categoria IS 'Categoria do produto';
COMMENT ON COLUMN vendas.regiao IS 'Região onde ocorreu a venda';
COMMENT ON COLUMN vendas.quantidade IS 'Quantidade de unidades vendidas';
COMMENT ON COLUMN vendas.preco_unitario IS 'Preço por unidade';
COMMENT ON COLUMN vendas.receita_total IS 'Receita total da transação';
COMMENT ON COLUMN vendas.mes_origem IS 'Mês/arquivo de origem dos dados';
