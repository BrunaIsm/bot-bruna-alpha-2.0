import { LucideIcon } from "lucide-react";
import { Card } from "./ui/card";

interface MetricsCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive: boolean;
  };
}

export const MetricsCard = ({ title, value, icon: Icon, trend }: MetricsCardProps) => {
  return (
    <Card className="group relative p-6 bg-gradient-card border-border/40 shadow-lg hover:shadow-2xl transition-all duration-500 overflow-hidden backdrop-blur-sm">
      {/* Efeito de brilho ao hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/3 via-accent/2 to-primary/3 group-hover:from-primary/10 group-hover:via-accent/8 group-hover:to-primary/10 transition-all duration-500" />
      
      {/* Conteúdo */}
      <div className="relative flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            {title}
          </p>
          <h3 className="text-2xl lg:text-3xl font-bold text-foreground mt-1 mb-2 transition-all duration-300 group-hover:scale-105">
            {value}
          </h3>
          {trend && (
            <div className="flex items-center gap-1 mt-3">
              <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium
                ${trend.isPositive 
                  ? 'bg-green-500/10 text-green-600 dark:text-green-400' 
                  : 'bg-red-500/10 text-red-600 dark:text-red-400'
                }`}>
                <span className="text-sm">{trend.isPositive ? '↑' : '↓'}</span>
                <span>{trend.value}</span>
              </div>
            </div>
          )}
        </div>
        
        {/* Ícone com animação */}
        <div className="rounded-xl bg-gradient-to-br from-primary/15 to-accent/15 p-3 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-lg group-hover:from-primary/25 group-hover:to-accent/25">
          <Icon className="h-6 w-6 text-primary transition-all duration-300 group-hover:text-accent" />
        </div>
      </div>
      
      {/* Borda inferior com gradiente */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary/0 via-primary/50 to-accent/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    </Card>
  );
};
