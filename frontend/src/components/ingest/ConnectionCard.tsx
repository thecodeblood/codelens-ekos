import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function ConnectionCard({
  icon: Icon,
  iconTone = "text-secondary",
  title,
  description,
  children,
  headerAccessory,
}: {
  icon: LucideIcon;
  iconTone?: string;
  title: string;
  description?: string;
  children: ReactNode;
  headerAccessory?: ReactNode;
}) {
  return (
    <div className="glass-card p-6 rounded-xl flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
            <Icon className={`w-5 h-5 ${iconTone}`} />
          </div>
          <h3 className="font-semibold text-lg">{title}</h3>
        </div>
        {headerAccessory}
      </div>
      {description && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
      <div className="mt-auto flex flex-col gap-3">{children}</div>
    </div>
  );
}
