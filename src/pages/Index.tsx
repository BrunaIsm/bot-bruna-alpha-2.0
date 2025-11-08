import { useState, useEffect } from "react";
import { Send, TrendingUp, DollarSign, ShoppingCart, BarChart3, FileSpreadsheet, RefreshCw, Calendar, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "@/components/ChatMessage";
import { FileUpload } from "@/components/FileUpload";
import { MetricsCard } from "@/components/MetricsCard";
import { toast } from "sonner";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface MetricsData {
  melhor_mes: {
    nome: string;
    valor: string;
  };
  produto_mais_vendido: {
    nome: string;
    quantidade: number;
  };
  quantidade_produtos: number;
  vendas_totais_ano: string;
  files_processed: number;
  records_analyzed: number;
  last_updated: string;
}

// Perguntas sugeridas para o usuário - Mais específicas para evitar bloqueios da API
const SUGGESTED_QUESTIONS = [
  {
    icon: "📊",
    text: "Qual mês teve a maior receita total em 2024?",
    category: "Análise Mensal"
  },
  {
    icon: "🏆",
    text: "Liste os 5 produtos com mais unidades vendidas",
    category: "Top Produtos"
  },
  {
    icon: "💰",
    text: "Quanto foi a receita total do ano de 2024?",
    category: "Faturamento"
  },
  {
    icon: "🌍",
    text: "Qual região gerou mais receita de vendas?",
    category: "Análise Regional"
  },
  {
    icon: "📈",
    text: "Mostre a receita de cada mês de 2024",
    category: "Evolução Mensal"
  },
  {
    icon: "🎯",
    text: "Qual categoria tem o maior volume de vendas?",
    category: "Categorias"
  },
  {
    icon: "📅",
    text: "Compare o faturamento de Março e Abril de 2024",
    category: "Comparação"
  },
  {
    icon: "🛒",
    text: "Quantos produtos diferentes foram vendidos?",
    category: "Diversidade"
  }
];

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Olá! Sou seu analista de vendas inteligente. Tenho acesso ao banco de dados de vendas no Supabase. Pergunte-me sobre vendas, tendências, produtos mais vendidos, ticket médio e muito mais!",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [metricsData, setMetricsData] = useState<MetricsData | null>(null);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true);
  const [showSuggestions, setShowSuggestions] = useState(true);

  // Função para carregar métricas
  const loadMetrics = async () => {
    try {
      setIsLoadingMetrics(true);
      const response = await fetch('/api/metrics');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Erro ao carregar métricas');
      }

      setMetricsData(data);
    } catch (error) {
      console.error('Erro ao carregar métricas:', error);
      toast.error('Erro ao carregar métricas. Verifique a configuração.');
    } finally {
      setIsLoadingMetrics(false);
    }
  };

  // Carregar métricas ao inicializar
  useEffect(() => {
    loadMetrics();
  }, []);

  // Métricas baseadas nos dados reais
  const metrics = metricsData ? [
    {
      title: "Produto Mais Vendido",
      value: metricsData.produto_mais_vendido.nome,
      icon: ShoppingCart,
      trend: { value: `${metricsData.produto_mais_vendido.quantidade} unidades`, isPositive: true },
    },
    {
      title: "Quantidade de Produtos",
      value: metricsData.quantidade_produtos.toString(),
      icon: Package,
      trend: { value: "produtos únicos", isPositive: true },
    },
    {
      title: "Vendas Totais do Ano",
      value: metricsData.vendas_totais_ano,
      icon: DollarSign,
      trend: { value: `${metricsData.files_processed} planilhas`, isPositive: true },
    },
    {
      title: "Melhor Mês",
      value: metricsData.melhor_mes.nome,
      icon: Calendar,
      trend: { value: metricsData.melhor_mes.valor, isPositive: true },
    },
  ] : [
    {
      title: "Produto Mais Vendido",
      value: isLoadingMetrics ? "Carregando..." : "N/A",
      icon: ShoppingCart,
      trend: { value: "0 unidades", isPositive: true },
    },
    {
      title: "Quantidade de Produtos",
      value: isLoadingMetrics ? "Carregando..." : "0",
      icon: Package,
      trend: { value: "produtos únicos", isPositive: true },
    },
    {
      title: "Vendas Totais do Ano",
      value: isLoadingMetrics ? "Carregando..." : "R$ 0,00",
      icon: DollarSign,
      trend: { value: "0 planilhas", isPositive: true },
    },
    {
      title: "Melhor Mês",
      value: isLoadingMetrics ? "Carregando..." : "N/A",
      icon: Calendar,
      trend: { value: "R$ 0,00", isPositive: true },
    },
  ];

  const handleSend = async (question?: string) => {
    const messageText = question || input.trim();
    if (!messageText) return;

    const userMessage: Message = { role: "user", content: messageText };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setShowSuggestions(false); // Esconder sugestões após primeira pergunta

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: messageText }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Erro na requisição');
      }

      if (data.error) {
        toast.error(data.error);
        const errorMessage: Message = {
          role: "assistant",
          content: `Erro: ${data.error}. ${data.details || ''}`,
        };
        setMessages((prev) => [...prev, errorMessage]);
      } else {
        const botMessage: Message = {
          role: "assistant",
          content: data.answer || data.response,
        };
        setMessages((prev) => [...prev, botMessage]);
        
        if (data.files_processed) {
          toast.success(`Analisados ${data.records_analyzed} registros de ${data.files_processed} planilha(s)`);
        }
      }
    } catch (error) {
      console.error('Erro ao consultar bot:', error);
      toast.error('Erro ao processar sua pergunta. Verifique a configuração.');
      const errorMessage: Message = {
        role: "assistant",
        content: "Desculpe, ocorreu um erro ao processar sua pergunta. Verifique se o banco de dados está configurado corretamente.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSyncData = async () => {
    setIsSyncing(true);
    try {
      const response = await fetch('/api/sync-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Erro na sincronização');
      }

      const syncMessage: Message = {
        role: "assistant",
        content: data.message || 'Sincronização concluída!',
      };
      setMessages((prev) => [...prev, syncMessage]);
      toast.success('Dados sincronizados com sucesso!');
      
      // Recarregar métricas após sincronização
      await loadMetrics();
    } catch (error) {
      console.error('Erro ao sincronizar:', error);
      toast.error('Erro ao sincronizar dados');
    } finally {
      setIsSyncing(false);
    }
  };



  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/10 relative overflow-hidden">
      {/* Efeitos de fundo decorativos */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-accent/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
      </div>
      {/* Header com gradiente */}
      <header className="border-b border-border/40 bg-card/80 backdrop-blur-xl sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-gradient-primary p-3 shadow-glow">
                <BarChart3 className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                  Alpha Insights
                </h1>
                <p className="text-sm text-muted-foreground">
                  Análise Inteligente de Vendas com IA
                </p>
              </div>
            </div>
            
            {/* Info Badge */}
            {metricsData && (
              <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl bg-muted/50 border border-border/50">
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs font-medium text-muted-foreground">
                  {metricsData.records_analyzed.toLocaleString()} registros • Atualizado {metricsData.last_updated.split(' ')[1]}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Metrics Dashboard com hover effects */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8 animate-fade-in">
          {metrics.map((metric, index) => (
            <div 
              key={index}
              className="transform transition-all duration-300 hover:scale-105 hover:z-10"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <MetricsCard {...metric} />
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Chat Area - Mais moderno */}
          <div className="lg:col-span-2">
            <div className="rounded-2xl border border-border/40 bg-card/95 backdrop-blur-sm shadow-xl h-[650px] flex flex-col overflow-hidden">
              {/* Header do Chat */}
              <div className="bg-gradient-to-r from-primary/5 via-accent/5 to-primary/5 border-b border-border/40 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
                      <div className="absolute inset-0 h-3 w-3 rounded-full bg-green-500 animate-ping" />
                    </div>
                    <div>
                      <span className="text-sm font-semibold text-foreground block">
                        Assistente de Análise
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Supabase • Gemini AI
                      </span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSyncData}
                    disabled={isSyncing}
                    className="hover:bg-primary/10 hover:border-primary/50 transition-all"
                  >
                    <RefreshCw className={`h-4 w-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`} />
                    {isSyncing ? 'Sincronizando...' : 'Atualizar'}
                  </Button>
                </div>
              </div>

              {/* Messages Area */}
              <ScrollArea className="flex-1 p-6 bg-gradient-to-b from-transparent to-muted/5">
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <ChatMessage key={index} {...message} />
                  ))}
                  
                  {isLoading && (
                    <div className="flex gap-2 items-center text-muted-foreground px-4">
                      <div className="h-2 w-2 rounded-full bg-primary animate-bounce" />
                      <div className="h-2 w-2 rounded-full bg-accent animate-bounce [animation-delay:0.2s]" />
                      <div className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:0.4s]" />
                      <span className="text-xs ml-2">Analisando dados...</span>
                    </div>
                  )}
                </div>
              </ScrollArea>

              {/* Input Area */}
              <div className="border-t border-border/40 p-4 bg-muted/20 backdrop-blur-sm">
                <div className="flex gap-3">
                  <Input
                    placeholder="💬 Pergunte sobre vendas, produtos, tendências..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                    className="flex-1 !bg-background hover:!bg-background border-border/50 hover:border-primary/50 focus:border-primary/50 focus:ring-2 focus:ring-primary/20 transition-all"
                    disabled={isLoading}
                  />
                  {!showSuggestions && messages.length > 1 && (
                    <Button
                      onClick={() => setShowSuggestions(true)}
                      variant="outline"
                      size="icon"
                      className="shrink-0 hover:bg-primary/10 hover:border-primary/50"
                      title="Mostrar perguntas sugeridas"
                    >
                      <TrendingUp className="h-4 w-4" />
                    </Button>
                  )}
                  <Button
                    onClick={() => handleSend()}
                    disabled={isLoading || !input.trim()}
                    className="bg-gradient-primary hover:opacity-90 transition-all shadow-md hover:shadow-glow px-6"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex items-center justify-between mt-2 px-1">
                  <p className="text-xs text-muted-foreground">
                    Pressione Enter para enviar • Shift + Enter para nova linha
                  </p>
                  {!showSuggestions && messages.length > 1 && (
                    <button
                      onClick={() => setShowSuggestions(true)}
                      className="text-xs text-primary hover:text-accent transition-colors"
                    >
                      Ver sugestões 💡
                    </button>
                  )}
                </div>
              </div>

              {/* Perguntas Sugeridas - Abaixo do Input */}
              {showSuggestions && !isLoading && (
                <div className="px-4 pb-4 space-y-3 animate-fade-in">
                  <div className="flex items-center justify-between px-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      💡 Perguntas Sugeridas
                    </p>
                    {messages.length > 1 && (
                      <button
                        onClick={() => setShowSuggestions(false)}
                        className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                      >
                        ✕ Fechar
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {SUGGESTED_QUESTIONS.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleSend(question.text)}
                        className="group relative text-left p-3 rounded-xl border border-border/40 
                                 bg-card/50 hover:bg-card/100 hover:border-primary/50 
                                 transition-all duration-300 hover:scale-[1.02] hover:shadow-md backdrop-blur-sm"
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-lg mt-0.5 transition-transform duration-300 group-hover:scale-110">
                            {question.icon}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                              {question.text}
                            </p>
                            <span className="text-xs text-muted-foreground">
                              {question.category}
                            </span>
                          </div>
                        </div>
                        
                        {/* Indicador visual de hover */}
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary/0 via-primary/50 to-accent/0 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar - Upload e Info */}
          <div className="lg:col-span-1 space-y-4">
            {/* Upload Card */}
            <div className="rounded-2xl border border-border/40 bg-card/95 backdrop-blur-sm shadow-xl p-6 transition-all hover:shadow-2xl">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-2 rounded-lg bg-primary/10">
                  <FileSpreadsheet className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-foreground">
                    Upload de Dados
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    Envie planilhas Excel ou CSV
                  </p>
                </div>
              </div>
              <FileUpload onSyncData={handleSyncData} />
            </div>

            {/* Quick Stats Card */}
            <div className="rounded-2xl border border-border/40 bg-gradient-to-br from-card/95 to-muted/20 backdrop-blur-sm shadow-xl p-6">
              <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                Estatísticas Rápidas
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 rounded-lg bg-background/50 border border-border/30">
                  <span className="text-xs text-muted-foreground">Período</span>
                  <span className="text-xs font-semibold text-foreground">2024 Completo</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-background/50 border border-border/30">
                  <span className="text-xs text-muted-foreground">Registros</span>
                  <span className="text-xs font-semibold text-primary">
                    {metricsData ? metricsData.records_analyzed.toLocaleString() : '0'}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 rounded-lg bg-background/50 border border-border/30">
                  <span className="text-xs text-muted-foreground">Banco de Dados</span>
                  <span className="text-xs font-semibold text-green-600 dark:text-green-400">
                    Supabase ✓
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
