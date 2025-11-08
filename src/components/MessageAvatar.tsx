import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface MessageAvatarProps {
  isAi: boolean;
}

export const MessageAvatar = ({ isAi }: MessageAvatarProps) => {
  return (
    <Avatar className={`w-8 h-8 ${isAi ? 'bg-primary' : 'bg-secondary'}`}>
      <AvatarFallback className={isAi ? 'text-primary-foreground' : 'text-secondary-foreground'}>
        {isAi ? '🤖' : '👤'}
      </AvatarFallback>
    </Avatar>
  );
};
