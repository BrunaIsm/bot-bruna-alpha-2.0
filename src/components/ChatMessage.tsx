import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

const formatMessage = (text: string) => {
  // Converter markdown simples em HTML
  let formatted = text;
  
  // Negrito: **texto** -> <strong>texto</strong>
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-primary">$1</strong>');
  
  // Itálico: *texto* -> <em>texto</em>
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Bullets: • ou - no início da linha
  formatted = formatted.replace(/^[•\-]\s+(.+)$/gm, '<span class="flex gap-2 my-1"><span class="text-primary">•</span><span>$1</span></span>');
  
  // Quebras de linha duplas -> parágrafo
  formatted = formatted.replace(/\n\n/g, '</p><p class="mt-3">');
  
  // Wrap em parágrafo se não tiver
  if (!formatted.startsWith('<p')) {
    formatted = '<p>' + formatted + '</p>';
  }
  
  return formatted;
};

export const ChatMessage = ({ role, content }: ChatMessageProps) => {
  const isBot = role === "assistant";
  const formattedContent = isBot ? formatMessage(content) : content;

  return (
    <div
      className={cn(
        "flex gap-3 animate-fade-in group",
        isBot ? "justify-start" : "justify-end"
      )}
    >
      {isBot && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-primary shadow-md transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg">
          <Bot className="h-5 w-5 text-primary-foreground" />
        </div>
      )}
      
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-5 py-3.5 transition-all duration-300",
          isBot
            ? "bg-card/95 backdrop-blur-sm text-card-foreground border border-border/40 shadow-md hover:shadow-xl hover:border-border/60"
            : "bg-gradient-primary text-primary-foreground shadow-lg hover:shadow-xl hover:opacity-95"
        )}
      >
        {isBot ? (
          <div 
            className="text-sm leading-relaxed prose prose-sm max-w-none
                       prose-strong:text-primary prose-strong:font-semibold
                       prose-p:my-0 prose-p:leading-relaxed
                       prose-p:text-foreground"
            dangerouslySetInnerHTML={{ __html: formattedContent }}
          />
        ) : (
          <p className="text-sm leading-relaxed whitespace-pre-wrap font-medium">{content}</p>
        )}
      </div>

      {!isBot && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-secondary/80 backdrop-blur-sm shadow-md transition-all duration-300 group-hover:scale-110">
          <User className="h-5 w-5 text-secondary-foreground" />
        </div>
      )}
    </div>
  );
};
