import * as React from "react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

// Types
export type AnsibleHostMap = Record<string, number | unknown>;
export type AnsibleRunnerRawStats = {
  skipped?: AnsibleHostMap;
  ok?: AnsibleHostMap;
  dark?: AnsibleHostMap; // unreachable / ssh failure
  failures?: AnsibleHostMap;
  ignored?: AnsibleHostMap;
  rescued?: AnsibleHostMap;
  processed?: AnsibleHostMap;
  changed?: AnsibleHostMap;
  // allow any other keys that may appear
  [key: string]: unknown;
};

export type AnsibleRunnerStatsProps = {
  stats: AnsibleRunnerRawStats;
  className?: string;
  labelSuccess?: string;
  labelFailed?: string;
};

// Helpers
const keys = (obj?: Record<string, unknown>) =>
  obj ? Object.keys(obj) : [] as string[];

const uniqSorted = (arr: string[]) => Array.from(new Set(arr)).sort();

const joinForAria = (hosts: string[]) => (hosts.length ? hosts.join(", ") : "none");

function HostBadge({
  label,
  hosts,
  className,
  badgeClassName,
}: {
  label: string;
  hosts: string[];
  className?: string;
  badgeClassName?: string;
}) {
  const count = hosts.length;
  const content = count ? (
    <ul className="text-xs leading-6">
      {hosts.map((h) => (
        <li key={h} className="font-mono text-xs">{h}</li>
      ))}
    </ul>
  ) : (
    <div className="text-xs text-muted-foreground">None</div>
  );

  return (
    <TooltipProvider>
      <Tooltip delayDuration={100}>
        <TooltipTrigger asChild>
          <Badge
            aria-label={`${label}: ${count} (${joinForAria(hosts)})`}
            className={cn(
                "text-xs",
              badgeClassName,
            )}
            variant={"outline"}
          >
            <span>{label}</span>
            <span>{count}</span>
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-sm">
          <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">{label} hosts</div>
          {content}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default function AnsibleRunnerStats({
  stats,
  className,
  labelSuccess = "Successful",
  labelFailed = "Failed",
}: AnsibleRunnerStatsProps) {
  // Successful hosts: those with any entry in `ok` (typical for Ansible recap)
  // Failed hosts: union of `failures` and `dark`.
  const successHosts = React.useMemo(
    () => uniqSorted(keys(stats.ok as Record<string, unknown>)),
    [stats]
  );

  const failedHosts = React.useMemo(() => {
    const f = keys(stats.failures as Record<string, unknown>);
    const d = keys(stats.dark as Record<string, unknown>);
    return uniqSorted([...f, ...d]);
  }, [stats]);

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <HostBadge
        label={labelSuccess}
        hosts={successHosts}
        badgeClassName="bg-green-100 text-green-900 hover:bg-green-100/90 dark:bg-green-900/30 dark:text-green-200"
      />
      <HostBadge
        label={labelFailed}
        hosts={failedHosts}
        badgeClassName="bg-red-100 text-red-900 hover:bg-red-100/90 dark:bg-red-900/30 dark:text-red-200"
      />
    </div>
  );
}

// --- Example Data ---
// const data = {
//   "skipped": { "srv03.asdf": 1 },
//   "ok": { "srv03.asdf": 2 },
//   "dark": {},
//   "failures": {},
//   "ignored": {},
//   "rescued": {},
//   "processed": { "srv03.asdf": 1 },
//   "changed": {}
// } satisfies AnsibleRunnerRawStats;
//
// <AnsibleRunnerStats stats={data} />
