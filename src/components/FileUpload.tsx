import { Upload, RefreshCw, FileSpreadsheet } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";
import { useState, useRef } from "react";

interface FileUploadProps {
  onSyncData?: () => void;
}

export const FileUpload = ({ onSyncData }: FileUploadProps) => {
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validar tamanho do arquivo (máx 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error("Arquivo muito grande. Máximo: 10MB");
      return;
    }

    // Validar extensão
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!validExtensions.includes(fileExtension)) {
      toast.error("Formato não suportado. Use Excel (.xlsx, .xls) ou CSV");
      return;
    }

    try {
      setIsUploading(true);
      toast.loading("Fazendo upload do arquivo...", { id: 'upload-toast' });

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload-data', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        toast.success(
          `✅ ${result.rows_imported} linhas importadas!\n🔄 Dados atualizados e prontos para análise.`, 
          {
            id: 'upload-toast',
            duration: 5000,
            description: 'Você já pode fazer perguntas sobre os novos dados!'
          }
        );
        
        // Sincronizar dados após upload
        if (onSyncData) {
          onSyncData();
        }
      } else {
        toast.error(result.error || "Erro ao fazer upload", {
          id: 'upload-toast'
        });
      }
    } catch (error) {
      console.error('Erro no upload:', error);
      toast.error("Erro de conexão ao fazer upload", {
        id: 'upload-toast'
      });
    } finally {
      setIsUploading(false);
      // Limpar input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleSyncData = async () => {
    if (onSyncData) {
      onSyncData();
    } else {
      // Implementação padrão de sincronização
      try {
        toast.loading("Atualizando dados...", { id: 'sync-toast' });
        
        const response = await fetch('/api/database-stats');
        const result = await response.json();
        
        if (response.ok) {
          toast.success(`Dados atualizados! ${result.total_records || 0} registros no banco.`, {
            id: 'sync-toast',
            duration: 3000
          });
        } else {
          toast.error("Erro ao atualizar dados", {
            id: 'sync-toast'
          });
        }
      } catch (error) {
        console.error('Erro na sincronização:', error);
        toast.error("Erro de conexão ao sincronizar", {
          id: 'sync-toast'
        });
      }
    }
  };

  return (
    <div className="space-y-4">
      {/* Input oculto para upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Upload Drop Zone - Mais moderno */}
      <div 
        className="group relative border-2 border-dashed rounded-2xl p-6 transition-all duration-500 
                   border-border/50 hover:border-primary/50 cursor-pointer overflow-hidden
                   bg-gradient-to-br from-muted/30 to-muted/10 hover:from-primary/5 hover:to-accent/5"
        onClick={handleUploadClick}
      >
        {/* Efeito shimmer no hover */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 animate-shimmer" />
        
        <div className="relative flex flex-col items-center justify-center gap-3 text-center">
          {/* Ícone animado */}
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-primary/20 blur-xl group-hover:bg-primary/30 transition-all" />
            <div className="relative rounded-full bg-gradient-to-br from-primary/10 to-accent/10 p-4 
                          transition-all duration-300 group-hover:scale-110 group-hover:rotate-3">
              <Upload className={`h-7 w-7 text-primary transition-all duration-300 
                                ${isUploading ? 'animate-bounce' : 'group-hover:text-accent'}`} />
            </div>
          </div>
          
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-foreground">
              {isUploading ? 'Enviando arquivo...' : 'Arraste ou clique para enviar'}
            </h3>
            <p className="text-xs text-muted-foreground">
              Excel (.xlsx, .xls) ou CSV • Máx: 10MB
            </p>
          </div>

          {/* Botão integrado */}
          <Button
            onClick={(e) => {
              e.stopPropagation();
              handleUploadClick();
            }}
            className="mt-2 bg-gradient-primary hover:opacity-90 transition-all shadow-md hover:shadow-lg"
            size="sm"
            disabled={isUploading}
          >
            <FileSpreadsheet className="h-3.5 w-3.5 mr-2" />
            {isUploading ? 'Enviando...' : 'Selecionar Arquivo'}
          </Button>
        </div>
      </div>

      {/* Divider */}
      <div className="relative py-2">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border/50"></div>
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-card px-2 text-muted-foreground">ou</span>
        </div>
      </div>

      {/* Botão de sincronização melhorado */}
      <Button
        onClick={handleSyncData}
        variant="outline"
        size="sm"
        className="w-full border-border/50 hover:border-primary/50 hover:bg-primary/5 transition-all"
      >
        <RefreshCw className="h-3.5 w-3.5 mr-2" />
        Atualizar Cache
      </Button>

      {/* Info adicional */}
      <div className="rounded-lg bg-muted/30 border border-border/30 p-3 space-y-2">
        <p className="text-xs text-muted-foreground leading-relaxed">
          <strong className="text-foreground">💡 Dica:</strong> Envie planilhas com colunas: 
          Data, Produto, Categoria, Região, Quantidade, Preço Unitário
        </p>
      </div>
    </div>
  );
};
